import os
import tarfile
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict, Audio

# 1. 압축 해제 (이미 했다면 스킵)
# with tarfile.open('cv-corpus-22.0-2025-06-25-ko.tar.gz', 'r:gz') as tar:
#     tar.extractall(path='./cv_ko_22')

# 2. 경로 설정
base_path = './ko'

# 모든 TSV 파일 로드
dfs = {
    'train': pd.read_csv(f'{base_path}/train.tsv', sep='\t'),
    'validation': pd.read_csv(f'{base_path}/dev.tsv', sep='\t'),
    'test': pd.read_csv(f'{base_path}/test.tsv', sep='\t'),
    'validated': pd.read_csv(f'{base_path}/validated.tsv', sep='\t')  # 추가!
}

print("데이터셋 크기:")
for name, df in dfs.items():
    print(f"{name}: {len(df)} 샘플")

# Audio 경로 추가 및 Dataset 변환
datasets = {}
for split, df in dfs.items():
    df['audio'] = df['path'].apply(lambda x: f"{base_path}/clips/{x}")
    datasets[split] = Dataset.from_pandas(df, preserve_index=False)

# DatasetDict 생성 및 Audio feature 추가
dataset = DatasetDict(datasets)
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))


dataset.push_to_hub(
    "daje/common-voice-ko-22",  # 원하는 이름으로 변경
    private=True,  # 비공개로 시작
    token=""
)

print("업로드 완료!")