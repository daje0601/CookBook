#!/usr/bin/env python3
import os
import json
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_json_file(file_path):
    """단일 JSON 파일을 파싱하여 필요한 필드를 추출"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 필요한 필드들 추출
        result = {
            'LabelText': data.get('전사정보', {}).get('LabelText', 'N/A'),
            'FileName': data.get('파일정보', {}).get('FileName', 'N/A'),
            'QualityStatus': data.get('기타정보', {}).get('QualityStatus', 'N/A'),
            'SamplingRate': data.get('음성정보', {}).get('SamplingRate', 'N/A'),
            'Gender': data.get('화자정보', {}).get('Gender', 'N/A'),
            'Age': data.get('화자정보', {}).get('Age', 'N/A'),
            'Dialect': data.get('화자정보', {}).get('Dialect', 'N/A'),
        }
        
        return result
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def find_label_folders(data_path):
    """Validation 폴더에서 모든 [라벨] 폴더를 찾기"""
    validation_dir = Path(data_path)
    
    if not validation_dir.exists():
        print(f"Validation 폴더가 존재하지 않습니다: {data_path}")
        return []
    
    # [라벨]로 시작하는 폴더들 찾기
    label_folders = []
    for item in validation_dir.iterdir():
        if item.is_dir() and item.name.startswith('[라벨]'):
            label_folders.append(item)
    
    return label_folders

def extract_all_data(data_path, max_workers=4):
    """Validation 폴더의 모든 라벨 데이터를 추출"""
    
    print(f"Validation 폴더 스캔 중: {data_path}")
    label_folders = find_label_folders(data_path)
    
    if not label_folders:
        print("라벨 폴더를 찾을 수 없습니다.")
        return []
    
    print(f"발견된 라벨 폴더: {len(label_folders)}개")
    for folder in label_folders:
        print(f"  - {folder.name}")
    
    # 모든 JSON 파일 수집
    all_json_files = []
    for folder in label_folders:
        json_files = list(folder.glob("*.json"))
        print(f"{folder.name}: {len(json_files)}개 JSON 파일")
        all_json_files.extend(json_files)
    
    print(f"\n총 {len(all_json_files)}개 JSON 파일 처리 시작...")
    
    # 멀티스레딩으로 빠르게 처리
    results = []
    processed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 파일을 병렬로 처리
        future_to_file = {
            executor.submit(parse_json_file, json_file): json_file 
            for json_file in all_json_files
        }
        
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                results.append(result)
            
            processed_count += 1
            if processed_count % 1000 == 0:
                print(f"처리 완료: {processed_count}/{len(all_json_files)}")
    
    print(f"✅ 총 {len(results)}개 데이터 추출 완료!")
    return results

def save_results(results, data_path, format='csv'):
    """결과를 파일로 저장"""
    if not results:
        print("저장할 데이터가 없습니다.")
        return
    
    validation_dir = Path(data_path)

    
    if format == 'csv':
        output_file = validation_dir / 'extracted_data.csv'
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"📁 CSV 파일 저장: {output_file}")
    
def show_statistics(results):
    """데이터 통계 출력"""
    if not results:
        return
    
    df = pd.DataFrame(results)
    
    print(f"\n📊 데이터 통계")
    print(f"총 샘플 수: {len(results):,}개")
    
    print(f"\n👥 성별 분포:")
    gender_counts = df['Gender'].value_counts()
    for gender, count in gender_counts.items():
        print(f"  {gender}: {count:,}개")
    
    print(f"\n🎂 나이 분포:")
    age_counts = df['Age'].value_counts()
    for age, count in age_counts.items():
        print(f"  {age}: {count:,}개")
    
    print(f"\n🗣️ 방언 분포:")
    dialect_counts = df['Dialect'].value_counts()
    for dialect, count in dialect_counts.items():
        print(f"  {dialect}: {count:,}개")
    
    print(f"\n✅ 품질 분포:")
    quality_counts = df['QualityStatus'].value_counts()
    for quality, count in quality_counts.items():
        print(f"  {quality}: {count:,}개")

def main():
    # 사용자 설정
    data_path = "."
    
    # 데이터 추출
    results = extract_all_data(data_path, max_workers=8)
    
    if results:
        # 통계 출력
        show_statistics(results)
        
        # 결과 저장
        save_results(results, data_path, format='csv')
        
        print(f"\n🎉 완료! {len(results)}개 데이터가 추출되었습니다.")
        print(f"📁 저장 위치: {data_path}")
        
        # 샘플 데이터 미리보기
        print(f"\n👀 샘플 데이터:")
        df = pd.DataFrame(results)
        print(df.head())
        
    else:
        print("❌ 추출된 데이터가 없습니다.")


if __name__ == "__main__":
    main()