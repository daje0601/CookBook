#!/usr/bin/env python3
"""
한국어 음성 데이터를 HuggingFace에 배치 단위로 업로드
간단한 흐름: 읽기 → 처리 → 푸시 → 삭제 → 반복
"""

import os
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from datasets import Dataset, DatasetDict, Audio, Features, Value, concatenate_datasets
from huggingface_hub import HfApi, create_repo
import argparse
from tqdm import tqdm
import gc

class KoreanSpeechBatchUploader:
    def __init__(self, repo_id: str, token: str = None):
        self.repo_id = repo_id
        self.api = HfApi(token=token)
        
        # Features 정의
        self.features = Features({
            'audio': Audio(sampling_rate=44100),
            'text': Value('string'),
            'gender': Value('string'),
            'age': Value('string'),
            'dialect': Value('string'),
            'category': Value('string'),
            'subcategory': Value('string'),
            'dialog_id': Value('string'),
            'word_type': Value('string'),
            'word_define': Value('string'),
        })
        
        # 저장소 생성
        try:
            create_repo(self.repo_id, repo_type="dataset", private=True, exist_ok=True, token=self.api.token)
        except Exception as e:
            print(f"저장소 생성/확인: {e}")
        
        self.first_push = {'train': True, 'validation': True}
    
    def process_batch(self, batch_pairs: List[Tuple[str, str]], split_name: str, batch_num: int, total_batches: int):
        """
        배치 처리: ZIP 읽기 → 처리 → 푸시 → 임시파일 삭제
        """
        print(f"\n📦 배치 [{batch_num}/{total_batches}] 처리 시작...")
        
        # 1. 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp(prefix=f"korean_speech_{split_name}_")
        
        try:
            all_data = []
            
            # 2. 배치 내 모든 ZIP 파일 처리
            for i, (source_zip, label_zip) in enumerate(batch_pairs, 1):
                print(f"  파일 {i}/{len(batch_pairs)}: {os.path.basename(source_zip)}")
                
                # ZIP 파일 압축 해제
                filename = os.path.basename(source_zip).replace('.zip', '')
                for prefix in ['VS_', 'VL_', 'TS_', 'TL_']:
                    filename = filename.replace(prefix, '')
                
                audio_dir = os.path.join(temp_dir, filename, 'audio')
                label_dir = os.path.join(temp_dir, filename, 'label')
                os.makedirs(audio_dir, exist_ok=True)
                os.makedirs(label_dir, exist_ok=True)
                
                # 원천데이터(오디오) 압축 해제
                with zipfile.ZipFile(source_zip, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.endswith('.wav'):
                            filename_only = os.path.basename(member)
                            target_path = os.path.join(audio_dir, filename_only)
                            source = zip_ref.open(member)
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                
                # 라벨링데이터(JSON) 압축 해제
                with zipfile.ZipFile(label_zip, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.endswith('.json'):
                            filename_only = os.path.basename(member)
                            target_path = os.path.join(label_dir, filename_only)
                            source = zip_ref.open(member)
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                
                # 오디오 파일 맵핑
                audio_files = {}
                for file in os.listdir(audio_dir):
                    if file.endswith('.wav'):
                        file_id = file.replace('.wav', '')
                        audio_files[file_id] = os.path.join(audio_dir, file)
                
                # JSON과 매칭하여 데이터 생성
                for file in os.listdir(label_dir):
                    if file.endswith('.json'):
                        file_id = file.replace('.json', '')
                        json_path = os.path.join(label_dir, file)
                        
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if file_id in audio_files:
                                record = {
                                    'audio': audio_files[file_id],
                                    'dialog_id': data.get('DialogID', ''),
                                    'category': data.get('Category', ''),
                                    'subcategory': data.get('SubCategory', ''),
                                    'text': '',
                                    'gender': '',
                                    'age': '',
                                    'dialect': '',
                                    'word_type': '',
                                    'word_define': ''
                                }
                                
                                # 화자 정보
                                speakers = data.get('Speakers', [])
                                if speakers:
                                    speaker = speakers[0]
                                    record['gender'] = speaker.get('Gender', '')
                                    record['age'] = speaker.get('AgeGroup', '')
                                    record['dialect'] = speaker.get('Locate', '')
                                
                                # 대화 정보
                                dialogs = data.get('Dialogs', [])
                                if dialogs:
                                    dialog = dialogs[0]
                                    record['text'] = dialog.get('SpeakerText', '')
                                    
                                    words = dialog.get('WordInfo', [])
                                    if words:
                                        word_info = words[0]
                                        record['word_type'] = word_info.get('WordType', '')
                                        record['word_define'] = word_info.get('WordDefine', '')
                                
                                all_data.append(record)
                        
                        except Exception as e:
                            print(f"    JSON 오류 ({file}): {e}")
            
            # 3. Dataset 생성 및 푸시
            if all_data:
                print(f"  데이터셋 생성 중... ({len(all_data)}개 샘플)")
                df = pd.DataFrame(all_data)
                dataset = Dataset.from_pandas(df, features=self.features)
                
                print(f"  📤 HuggingFace에 푸시 중...")
                dataset_dict = DatasetDict({split_name: dataset})
                
                # 첫 번째 푸시인지 확인
                if self.first_push[split_name]:
                    # 처음이면 새로 생성
                    dataset_dict.push_to_hub(
                        self.repo_id,
                        token=self.api.token,
                        private=True,
                        commit_message=f"Add {split_name} batch {batch_num}"
                    )
                    self.first_push[split_name] = False
                else:
                    # 이후는 추가 (append는 자동으로 됨)
                    dataset_dict.push_to_hub(
                        self.repo_id,
                        token=self.api.token,
                        private=True,
                        commit_message=f"Add {split_name} batch {batch_num}"
                    )
                
                print(f"  ✅ 배치 {batch_num} 완료")
        
        finally:
            # 4. 임시 디렉토리 삭제
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"  🧹 임시 파일 삭제 완료")
            
            # 메모리 정리
            gc.collect()
            
            # 디스크 공간 확인
            import subprocess
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 3:
                    print(f"  💾 남은 디스크 공간: {parts[3]}")
    
    def upload_split(self, zip_pairs: List[Tuple[str, str]], split_name: str, batch_size: int):
        """
        전체 split을 배치 단위로 처리
        """
        total_batches = (len(zip_pairs) + batch_size - 1) // batch_size
        
        for batch_num, batch_start in enumerate(range(0, len(zip_pairs), batch_size), 1):
            batch_end = min(batch_start + batch_size, len(zip_pairs))
            batch_pairs = zip_pairs[batch_start:batch_end]
            
            self.process_batch(batch_pairs, split_name, batch_num, total_batches)

def get_file_pairs(base_path: str, split: str) -> List[Tuple[str, str]]:
    """파일 쌍 목록 생성"""
    source_dir = os.path.join(base_path, split, "01.원천데이터")
    label_dir = os.path.join(base_path, split, "02.라벨링데이터")
    
    if split == "Training":
        source_prefix, label_prefix = "TS_", "TL_"
    else:
        source_prefix, label_prefix = "VS_", "VL_"
    
    pairs = []
    source_files = sorted([f for f in os.listdir(source_dir) if f.startswith(source_prefix) and f.endswith('.zip')])
    
    for source_file in source_files:
        base_name = source_file.replace(source_prefix, '')
        label_file = label_prefix + base_name
        
        source_path = os.path.join(source_dir, source_file)
        label_path = os.path.join(label_dir, label_file)
        
        if os.path.exists(label_path):
            pairs.append((source_path, label_path))
    
    return pairs

def main():
    parser = argparse.ArgumentParser(description="한국어 음성 데이터 배치 업로드")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--token", help="HuggingFace API token")
    parser.add_argument("--mode", choices=['test', 'validation', 'training', 'all'], default='test')
    parser.add_argument("--batch-size", type=int, default=5, help="배치 크기")
    
    args = parser.parse_args()
    
    base_path = "./132.연령대별 특징적 발화(은어·속어 등) 음성 데이터/01-1.정식개방데이터"
    
    uploader = KoreanSpeechBatchUploader(args.repo_id, args.token)
    
    if args.mode == 'test':
        print("🧪 테스트 모드")
        val_pairs = get_file_pairs(base_path, "Validation")[:2]
        uploader.upload_split(val_pairs, 'validation', args.batch_size)
        
    elif args.mode == 'validation':
        print("📊 Validation 데이터 처리")
        val_pairs = get_file_pairs(base_path, "Validation")
        print(f"총 {len(val_pairs)}개 파일")
        uploader.upload_split(val_pairs, 'validation', args.batch_size)
        
    elif args.mode == 'training':
        print("📚 Training 데이터 처리")
        train_pairs = get_file_pairs(base_path, "Training")
        print(f"총 {len(train_pairs)}개 파일")
        uploader.upload_split(train_pairs, 'train', args.batch_size)
        
    elif args.mode == 'all':
        print("🌟 전체 데이터 처리")
        
        # Validation
        val_pairs = get_file_pairs(base_path, "Validation")
        print(f"\n🔍 Validation: {len(val_pairs)}개 파일")
        uploader.upload_split(val_pairs, 'validation', args.batch_size)
        
        # Training
        train_pairs = get_file_pairs(base_path, "Training")
        print(f"\n📚 Training: {len(train_pairs)}개 파일")
        uploader.upload_split(train_pairs, 'train', args.batch_size)
        
        print(f"\n✅ 모든 작업 완료!")
        print(f"🔗 https://huggingface.co/datasets/{args.repo_id}")

if __name__ == "__main__":
    main()