"""
식품안전나라 API를 통한 알부민/특수용도식품 데이터 수집 스크립트

사용법:
    # 환경변수로 API 키 설정
    export FOODSAFETY_API_KEY="your_api_key_here"

    # 또는 .env 파일 사용
    python collect_albumin_api.py

    # 사용 가능한 서비스 확인
    python collect_albumin_api.py --check

    # 특정 서비스 전체 데이터 수집
    python collect_albumin_api.py --service C003 --full

    # 키워드로 검색
    python collect_albumin_api.py --keyword 알부민

필요 패키지:
    pip install requests pandas python-dotenv
"""

import os
import requests
import pandas as pd
import json
import time
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv가 없어도 동작


class FoodSafetyKoreaAPI:
    """식품안전나라 Open API 클라이언트"""

    BASE_URL = "https://openapi.foodsafetykorea.go.kr/api"

    # 건강기능식품 및 특수용도식품 관련 서비스코드 목록
    # 서비스코드는 식품안전나라 API 상세페이지에서 확인 가능
    # https://www.foodsafetykorea.go.kr/api/main.do
    SERVICE_CODES = {
        # 건강기능식품 관련
        "C003": "건강기능식품 품목제조신고(원재료)",
        "I0030": "건강기능식품 품목제조신고(영업)",
        "I0040": "건강기능식품 품목제조신고(품목)",
        "I0490": "건강기능식품 영양DB",
        "I0500": "건강기능식품 기능성 원료인정현황",
        "I0510": "건강기능식품 개별인정형 정보",
        "I0520": "건강기능식품 생산실적 보고 품목 현황",
        "I0530": "건강기능식품GMP 지정 현황",
        "I0540": "건강기능식품 품목분류정보",
        "I0550": "건강기능식품 표시기준",
        "I0560": "건강기능식품 이상사례 신고 현황 정보",
        "I0570": "건강기능식품 폐업정보",
        "I0580": "건강기능식품공전",
        "I0590": "건강기능식품 전문벤처제조업인허가 현황",
        "I0600": "건강기능식품업소 인허가 변경 정보",
        "I0610": "건강기능식품판매업",
        "I0620": "건강기능식품제조업 지도단속계획 및 실적현황",
        "I0630": "개별기준규격",
        # HACCP 관련
        "I0640": "HACCP 적용업소 지정 현황",
        "I0650": "HACCP 교육훈련기관 지정 현황",
        # LMO 관련
        "I0660": "LMO 수입 승인 현황",
        # 식품영양성분 관련
        "I2790": "식품영양성분DB(음식)",
        "I2570": "식품영양성분(가공식품)",
        "C002": "식품품목제조보고(원재료)",
        "I1250": "식품품목제조보고",
        # 특수용도식품 관련
        "I2710": "특수용도식품 영양성분DB",
        "I2715": "특수의료용도등식품",
        "I2720": "영유아용식품",
        "I2730": "체중조절용조제식품",
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    def call_api(self, service_code: str, start: int = 1, end: int = 100,
                 response_type: str = "json") -> dict:
        """
        API 호출

        Args:
            service_code: 서비스 코드
            start: 시작 인덱스
            end: 종료 인덱스
            response_type: 응답 형식 (json/xml)

        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}/{self.api_key}/{service_code}/{response_type}/{start}/{end}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 호출 오류: {e}")
            return {}

    def search_with_keyword(self, service_code: str, keyword: str = "알부민",
                           start: int = 1, end: int = 1000) -> list:
        """
        키워드로 검색

        Args:
            service_code: 서비스 코드
            keyword: 검색 키워드
            start: 시작 인덱스
            end: 종료 인덱스

        Returns:
            검색 결과 리스트
        """
        data = self.call_api(service_code, start, end)

        if not data:
            return []

        # 서비스코드에 따라 데이터 키가 다름
        service_data = data.get(service_code, {})

        if "RESULT" in service_data:
            result = service_data["RESULT"]
            if result.get("CODE") != "INFO-000":
                print(f"API 오류: {result.get('MSG', '알 수 없는 오류')}")
                return []

        rows = service_data.get("row", [])

        if not rows:
            return []

        # 키워드 필터링
        filtered = []
        for row in rows:
            row_str = json.dumps(row, ensure_ascii=False).lower()
            if keyword.lower() in row_str:
                filtered.append(row)

        return filtered

    def get_total_count(self, service_code: str) -> int:
        """해당 서비스의 총 데이터 수 조회"""
        data = self.call_api(service_code, 1, 1)

        if not data:
            return 0

        service_data = data.get(service_code, {})
        return int(service_data.get("total_count", 0))

    def collect_all_data(self, service_code: str, batch_size: int = 1000) -> list:
        """
        해당 서비스의 전체 데이터 수집

        Args:
            service_code: 서비스 코드
            batch_size: 배치 크기

        Returns:
            전체 데이터 리스트
        """
        total = self.get_total_count(service_code)

        if total == 0:
            print(f"서비스 {service_code}: 데이터 없음 또는 접근 불가")
            return []

        print(f"서비스 {service_code}: 총 {total}개 데이터 수집 시작...")

        all_data = []
        for start in range(1, total + 1, batch_size):
            end = min(start + batch_size - 1, total)
            print(f"  수집 중: {start} ~ {end}")

            data = self.call_api(service_code, start, end)
            service_data = data.get(service_code, {})
            rows = service_data.get("row", [])

            if rows:
                all_data.extend(rows)

            time.sleep(0.5)  # API 부하 방지

        return all_data

    def find_albumin_data(self, keyword: str = "알부민") -> dict:
        """
        모든 서비스에서 알부민 관련 데이터 검색

        Args:
            keyword: 검색 키워드

        Returns:
            서비스별 검색 결과
        """
        results = {}

        for code, name in self.SERVICE_CODES.items():
            print(f"\n[{code}] {name} 검색 중...")

            # 먼저 총 데이터 수 확인
            total = self.get_total_count(code)

            if total == 0:
                print(f"  -> 데이터 없음 또는 서비스 미제공")
                continue

            print(f"  -> 총 {total}개 데이터 확인")

            # 키워드 검색
            found = self.search_with_keyword(code, keyword, 1, min(total, 5000))

            if found:
                results[code] = {
                    "name": name,
                    "total_count": total,
                    "found_count": len(found),
                    "data": found
                }
                print(f"  -> '{keyword}' 관련 {len(found)}개 발견!")
            else:
                print(f"  -> '{keyword}' 관련 데이터 없음")

            time.sleep(1)  # API 부하 방지

        return results


def save_to_csv(data: list, filename: str, output_dir: str = "output"):
    """데이터를 CSV로 저장"""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / filename

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {filepath}")
    return filepath


def save_to_json(data, filename: str, output_dir: str = "output"):
    """데이터를 JSON으로 저장"""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {filepath}")
    return filepath


def check_available_services(api: FoodSafetyKoreaAPI) -> dict:
    """사용 가능한 서비스 확인"""
    print("=" * 60)
    print("사용 가능한 API 서비스 확인 중...")
    print("=" * 60)

    available = {}
    unavailable = []

    for code, name in api.SERVICE_CODES.items():
        total = api.get_total_count(code)
        if total > 0:
            available[code] = {"name": name, "total_count": total}
            print(f"✓ [{code}] {name}: {total}개")
        else:
            unavailable.append((code, name))
            print(f"✗ [{code}] {name}: 접근 불가 또는 데이터 없음")
        time.sleep(0.3)

    print(f"\n사용 가능: {len(available)}개, 사용 불가: {len(unavailable)}개")
    return available


def collect_specific_service(api: FoodSafetyKoreaAPI, service_code: str,
                            keyword: Optional[str] = None) -> list:
    """특정 서비스의 데이터 수집"""
    name = api.SERVICE_CODES.get(service_code, service_code)

    print(f"\n[{service_code}] {name} 데이터 수집 중...")

    if keyword:
        # 키워드 검색
        data = api.search_with_keyword(service_code, keyword)
        print(f"'{keyword}' 키워드로 {len(data)}개 데이터 발견")
    else:
        # 전체 수집
        data = api.collect_all_data(service_code)
        print(f"총 {len(data)}개 데이터 수집 완료")

    return data


def main():
    import argparse

    parser = argparse.ArgumentParser(description="식품안전나라 API 데이터 수집")
    parser.add_argument("--check", action="store_true", help="사용 가능한 서비스 확인")
    parser.add_argument("--service", type=str, help="특정 서비스코드 수집 (예: C003)")
    parser.add_argument("--keyword", type=str, default="알부민", help="검색 키워드 (기본: 알부민)")
    parser.add_argument("--all", action="store_true", help="모든 서비스에서 검색")
    parser.add_argument("--full", action="store_true", help="키워드 없이 전체 데이터 수집")

    args = parser.parse_args()

    # API 키 설정 (환경변수에서 읽기)
    API_KEY = os.getenv("FOODSAFETY_API_KEY")

    if not API_KEY:
        print("오류: API 키가 설정되지 않았습니다.")
        print("환경변수를 설정해주세요:")
        print('  export FOODSAFETY_API_KEY="your_api_key_here"')
        print("또는 .env 파일에 FOODSAFETY_API_KEY=your_api_key 를 추가해주세요.")
        return

    # API 클라이언트 생성
    api = FoodSafetyKoreaAPI(API_KEY)

    print("=" * 60)
    print("식품안전나라 데이터 수집 도구")
    print("=" * 60)

    # 1. 서비스 확인 모드
    if args.check:
        available = check_available_services(api)
        save_to_json(available, "available_services.json")
        return

    # 2. 특정 서비스 수집
    if args.service:
        keyword = None if args.full else args.keyword
        data = collect_specific_service(api, args.service, keyword)

        if data:
            name = api.SERVICE_CODES.get(args.service, args.service).replace(" ", "_")
            suffix = f"_{args.keyword}" if keyword else "_full"
            save_to_csv(data, f"{args.service}_{name}{suffix}.csv")
            save_to_json(data, f"{args.service}_{name}{suffix}.json")
        return

    # 3. 모든 서비스에서 검색 (기본)
    print(f"\n키워드 '{args.keyword}'로 모든 서비스 검색...")
    results = api.find_albumin_data(args.keyword)

    if results:
        # 전체 결과 JSON 저장
        save_to_json(results, f"{args.keyword}_search_results.json")

        # 서비스별 CSV 저장
        for code, result in results.items():
            if result["data"]:
                filename = f"{args.keyword}_{code}_{result['name'].replace(' ', '_')}.csv"
                save_to_csv(result["data"], filename)

        print("\n" + "=" * 60)
        print("수집 완료 요약")
        print("=" * 60)
        for code, result in results.items():
            print(f"[{code}] {result['name']}: {result['found_count']}개")
    else:
        print(f"\n'{args.keyword}' 관련 데이터를 찾지 못했습니다.")
        print("다른 키워드로 시도해보세요. (예: '단백질', '영양', '특수용도식품')")


if __name__ == "__main__":
    main()
