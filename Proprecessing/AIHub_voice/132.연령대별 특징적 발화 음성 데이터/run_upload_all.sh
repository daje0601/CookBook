#!/bin/bash

# HuggingFace 업로드 실행 스크립트 (전체 데이터)

echo "🚀 한국어 음성 데이터 HuggingFace 업로드"
echo "Repository: your_hf_id/korean-general-speech"
echo ""

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source .venv/bin/activate

# 필요한 패키지 설치 확인
# echo "📦 필요한 패키지 확인 중..."
# pip3 install -q datasets huggingface_hub pandas tqdm

# 모드 선택
MODE=${1:-test}

echo ""
echo "📋 실행 모드: $MODE"
echo ""

if [ "$MODE" == "test" ]; then
    echo "🧪 테스트 모드: 각 split에서 2개 파일씩 처리"
elif [ "$MODE" == "validation" ]; then
    echo "📊 Validation 데이터 전체 처리"
elif [ "$MODE" == "training" ]; then
    echo "📚 Training 데이터 전체 처리"
elif [ "$MODE" == "all" ]; then
    echo "🌟 전체 데이터 처리 (Training + Validation)"
else
    echo "❌ 잘못된 모드: $MODE"
    echo "사용법: ./run_upload_all.sh [test|validation|training|all]"
    exit 1
fi

python upload_simple.py \
      --repo-id "your_hf_id/korean-general-speech" \
      --token "your_hf_token" \
      --mode all \
      --batch-size 5

echo ""
echo "✅ 작업 완료!"
echo "🔗 확인: https://huggingface.co/datasets/your_hf_id/korean-general-speech"