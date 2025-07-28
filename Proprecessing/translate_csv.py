#!/usr/bin/env python3
"""
CSV 파일의 지정된 컬럼을 한국어로 번역하는 스크립트
OpenAI API와 pqdm을 사용하여 대용량 파일을 안전하게 처리
  사용법:

  python translate_csv.py --input sampled_for_translation_korean.csv --columns "caption,caption_sv,caption_multi"

  주요 특징:

  1. 간단한 CLI: 파일명과 컬럼을 파라미터로 받음
  2. 안전한 처리: 5,000개마다 자동 저장, 중단 시 재시작 가능
  3. 병렬 처리: pqdm으로 효율적 번역
  4. 에러 처리: API 실패 시 3회 재시도
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from openai import OpenAI
from pqdm.processes import pqdm
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 설정
CHECKPOINT_DIR = Path("checkpoints")
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHECKPOINT_INTERVAL = 5000
DEFAULT_MAX_WORKERS = 5
MAX_RETRIES = 3

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def translate_text(text: str, target_lang: str = "Korean") -> str:
    """텍스트를 목표 언어로 번역"""
    if pd.isna(text) or text.strip() == "":
        return text
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": f"Translate the following text to {target_lang}. Only return the translation."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"번역 실패: {text[:50]}... - 오류: {str(e)}")
                return text  # 실패 시 원본 반환


def translate_batch(batch_data: List[tuple]) -> List[tuple]:
    """배치 데이터 번역 (pqdm에서 사용)"""
    results = []
    for idx, text in batch_data:
        translated = translate_text(text)
        results.append((idx, translated))
    return results


def save_checkpoint(df: pd.DataFrame, checkpoint_path: Path, progress: Dict):
    """체크포인트 저장"""
    df.to_csv(checkpoint_path, index=False)
    progress_path = checkpoint_path.parent / f"{checkpoint_path.stem}_progress.json"
    with open(progress_path, 'w') as f:
        json.dump(progress, f)
    print(f"체크포인트 저장: {progress['processed_rows']}행 완료")


def load_checkpoint(input_file: str, columns: List[str]) -> tuple:
    """이전 진행 상황 로드"""
    checkpoint_name = Path(input_file).stem
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_name}_checkpoint.csv"
    progress_path = CHECKPOINT_DIR / f"{checkpoint_name}_progress.json"
    
    if checkpoint_path.exists() and progress_path.exists():
        with open(progress_path, 'r') as f:
            progress = json.load(f)
        
        # 동일한 컬럼을 번역하는지 확인
        if set(progress.get('columns', [])) == set(columns):
            df = pd.read_csv(checkpoint_path)
            print(f"체크포인트 로드: {progress['processed_rows']}행부터 재시작")
            return df, progress['processed_rows']
    
    return None, 0


def translate_csv(
    input_file: str,
    columns: List[str],
    output_file: Optional[str] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
    max_workers: int = DEFAULT_MAX_WORKERS
):
    """CSV 파일의 지정된 컬럼을 번역"""
    
    # 체크포인트 디렉토리 생성
    CHECKPOINT_DIR.mkdir(exist_ok=True)
    
    # 출력 파일명 설정
    if not output_file:
        output_file = Path(input_file).stem + "_translated.csv"
    
    # 데이터 로드
    print(f"파일 로드 중: {input_file}")
    df = pd.read_csv(input_file)
    total_rows = len(df)
    print(f"총 {total_rows:,}개 행 발견")
    
    # 컬럼 검증
    missing_columns = set(columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"존재하지 않는 컬럼: {missing_columns}")
    
    # 체크포인트 확인
    checkpoint_df, start_row = load_checkpoint(input_file, columns)
    if checkpoint_df is not None:
        df = checkpoint_df
    
    # 번역 시작
    for column in columns:
        print(f"\n'{column}' 컬럼 번역 시작...")
        
        # 번역할 행만 선택 (이미 번역된 행 제외)
        translated_column = f"{column}_ko"
        if translated_column not in df.columns:
            df[translated_column] = None
        
        # 번역이 필요한 행 찾기
        needs_translation = df[translated_column].isna()
        if start_row > 0:
            needs_translation = needs_translation & (df.index >= start_row)
        
        rows_to_translate = df[needs_translation].index.tolist()
        
        if not rows_to_translate:
            print(f"'{column}' 컬럼은 이미 모두 번역됨")
            continue
        
        print(f"{len(rows_to_translate):,}개 행 번역 필요")
        
        # 배치 준비
        batches = []
        for i in range(0, len(rows_to_translate), chunk_size):
            batch_indices = rows_to_translate[i:i+chunk_size]
            batch_data = [(idx, df.loc[idx, column]) for idx in batch_indices]
            batches.append(batch_data)
        
        # 병렬 번역 실행
        print(f"{len(batches)}개 배치로 나누어 처리 (배치당 최대 {chunk_size}개)")
        
        processed_count = start_row
        for i, batch in enumerate(batches):
            # 배치 번역
            results = pqdm(
                [batch],
                translate_batch,
                n_jobs=1,  # 배치 자체가 이미 여러 항목을 포함
                desc=f"배치 {i+1}/{len(batches)}"
            )[0]
            
            # 결과 저장
            for idx, translated_text in results:
                df.loc[idx, translated_column] = translated_text
                processed_count += 1
            
            # 체크포인트 저장
            if processed_count % checkpoint_interval == 0:
                checkpoint_path = CHECKPOINT_DIR / f"{Path(input_file).stem}_checkpoint.csv"
                progress = {
                    'processed_rows': processed_count,
                    'total_rows': total_rows,
                    'columns': columns,
                    'current_column': column
                }
                save_checkpoint(df, checkpoint_path, progress)
    
    # 최종 결과 저장
    df.to_csv(output_file, index=False)
    print(f"\n번역 완료! 결과 저장: {output_file}")
    
    # 체크포인트 파일 정리
    checkpoint_files = list(CHECKPOINT_DIR.glob(f"{Path(input_file).stem}_*"))
    for file in checkpoint_files:
        file.unlink()
    print("체크포인트 파일 정리 완료")


def main():
    parser = argparse.ArgumentParser(description="CSV 파일의 특정 컬럼을 한국어로 번역")
    parser.add_argument("--input", "-i", required=True, help="입력 CSV 파일")
    parser.add_argument("--columns", "-c", required=True, help="번역할 컬럼 (쉼표로 구분)")
    parser.add_argument("--output", "-o", help="출력 파일 (기본: input_translated.csv)")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"배치 크기 (기본: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--checkpoint-interval", type=int, default=DEFAULT_CHECKPOINT_INTERVAL, help=f"체크포인트 간격 (기본: {DEFAULT_CHECKPOINT_INTERVAL})")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS, help=f"최대 워커 수 (기본: {DEFAULT_MAX_WORKERS})")
    
    args = parser.parse_args()
    
    # 컬럼 파싱
    columns = [col.strip() for col in args.columns.split(",")]
    
    # 번역 실행
    translate_csv(
        input_file=args.input,
        columns=columns,
        output_file=args.output,
        chunk_size=args.chunk_size,
        checkpoint_interval=args.checkpoint_interval,
        max_workers=args.max_workers
    )


if __name__ == "__main__":
    main()