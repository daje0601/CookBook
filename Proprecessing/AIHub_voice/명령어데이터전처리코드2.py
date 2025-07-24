#!/usr/bin/env python
# coding: utf-8

import pandas as pd 

from pathlib import Path
validation_path = "."
csv_path = Path(validation_path) / "extracted_data.csv"

df = pd.read_csv(csv_path)
validation_dir = Path(validation_path)
source_folders = [item for item in validation_dir.iterdir() 
                     if item.is_dir() and item.name.startswith('[원천]')]
len(source_folders), source_folders[-1]

from glob import glob
from pathlib import Path

all_files = []
for folder in source_folders:
    wav_files = list(folder.rglob("*.wav"))
    for wav_file in wav_files:
            all_files.append({
                'FileName': wav_file.name,
                'AudioPath': str(wav_file),
            })

source_df = pd.DataFrame(all_files)


# 두 DataFrame을 FileName으로 merge
merged_df = df.merge(source_df, on='FileName', how='left')

# 결과 확인
print(f"Original df: {len(df):,}개")
print(f"Source df: {len(source_df):,}개") 
print(f"Merged df: {len(merged_df):,}개")

# 매칭 결과
matched_count = merged_df['AudioPath'].notna().sum()
print(f"매칭된 레코드: {matched_count:,}개")
print(f"매칭률: {matched_count/len(merged_df)*100:.1f}%")

df = merged_df[merged_df['AudioPath'].notna()].copy()


print(f"📊 {len(df):,}개 샘플로 데이터셋 생성")

# 필요한 컬럼만
dataset_df = df[['LabelText', 'AudioPath', 'Gender', 'Age', 'Dialect']].copy()
dataset_df.columns = ['text', 'audio', 'gender', 'age', 'dialect']



from datasets import Dataset, Audio

dataset = Dataset.from_pandas(dataset_df)
dataset = dataset.cast_column("audio", Audio())

from datasets import DatasetDict

dataset_dict = DatasetDict({
    "validation": dataset
})

dataset.save_to_disk("./dataset_folder")
from huggingface_hub import create_repo
repo_id = "your_repo_id/your_dataset_name"
create_repo(repo_id, repo_type="dataset", private=True, exist_ok=True)



from huggingface_hub import HfApi
api = HfApi()

api.upload_large_folder(
    folder_path="./dataset_folder",
    repo_id=repo_id, 
    repo_type="dataset",
    private=True
)

print("✅ 업로드 완료!")

