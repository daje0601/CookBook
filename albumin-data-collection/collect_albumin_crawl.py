"""
식품안전나라 특수용도식품 페이지 크롤링 스크립트

사용법:
    python collect_albumin_crawl.py

필요 패키지:
    pip install selenium pandas webdriver-manager beautifulsoup4

주의: Chrome 브라우저가 설치되어 있어야 합니다.
"""

import time
import json
import pandas as pd
from pathlib import Path
from typing import Optional

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError as e:
    print("필요한 패키지를 설치해주세요:")
    print("  pip install selenium pandas webdriver-manager beautifulsoup4")
    print(f"오류: {e}")
    exit(1)


class FoodSafetyKoreaCrawler:
    """식품안전나라 특수용도식품 크롤러"""

    BASE_URL = "https://www.foodsafetykorea.go.kr/portal/specialinfo/searchInfoProduct.do"

    def __init__(self, headless: bool = True):
        """
        크롤러 초기화

        Args:
            headless: 헤드리스 모드 (브라우저 창 숨김)
        """
        self.driver = self._setup_driver(headless)
        self.data = []

    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Chrome 드라이버 설정"""
        options = Options()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def navigate_to_page(self, page_num: int = 1):
        """
        특정 페이지로 이동

        Args:
            page_num: 페이지 번호
        """
        url = f"{self.BASE_URL}?menu_grp=MENU_NEW04&menu_no=2815"
        self.driver.get(url)
        time.sleep(2)

        if page_num > 1:
            try:
                # 페이지 번호 클릭
                page_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, str(page_num)))
                )
                page_link.click()
                time.sleep(2)
            except TimeoutException:
                print(f"페이지 {page_num} 이동 실패")

    def get_total_pages(self) -> int:
        """총 페이지 수 확인"""
        try:
            # 페이지네이션 영역에서 마지막 페이지 번호 찾기
            pagination = self.driver.find_element(By.CLASS_NAME, "paging")
            page_links = pagination.find_elements(By.TAG_NAME, "a")

            max_page = 1
            for link in page_links:
                try:
                    page_num = int(link.text)
                    max_page = max(max_page, page_num)
                except ValueError:
                    continue

            return max_page
        except NoSuchElementException:
            return 1

    def extract_table_data(self) -> list:
        """현재 페이지의 테이블 데이터 추출"""
        try:
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            tables = soup.find_all("table")

            page_data = []

            for table in tables:
                # 테이블 헤더 추출
                headers = []
                thead = table.find("thead")
                if thead:
                    for th in thead.find_all("th"):
                        headers.append(th.get_text(strip=True))

                # 테이블 본문 추출
                tbody = table.find("tbody")
                if tbody:
                    for row in tbody.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if cols:
                            row_data = {}
                            for i, col in enumerate(cols):
                                key = headers[i] if i < len(headers) else f"column_{i}"
                                row_data[key] = col.get_text(strip=True)
                            if row_data:
                                page_data.append(row_data)

            return page_data

        except Exception as e:
            print(f"데이터 추출 오류: {e}")
            return []

    def extract_product_details(self, product_url: str) -> dict:
        """제품 상세 페이지에서 정보 추출"""
        try:
            self.driver.get(product_url)
            time.sleep(1)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            details = {}

            # 상세 정보 테이블 추출
            detail_tables = soup.find_all("table", class_="tb_type")
            for table in detail_tables:
                rows = table.find_all("tr")
                for row in rows:
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        details[key] = value

            return details

        except Exception as e:
            print(f"상세 정보 추출 오류: {e}")
            return {}

    def search_keyword(self, keyword: str = "알부민"):
        """
        키워드로 검색

        Args:
            keyword: 검색어
        """
        try:
            # 검색어 입력
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "search_text"))
            )
            search_input.clear()
            search_input.send_keys(keyword)

            # 검색 버튼 클릭
            search_btn = self.driver.find_element(By.CLASS_NAME, "btn_search")
            search_btn.click()
            time.sleep(2)

        except Exception as e:
            print(f"검색 오류: {e}")

    def crawl_all_pages(self, max_pages: Optional[int] = None, keyword: Optional[str] = None):
        """
        모든 페이지 크롤링

        Args:
            max_pages: 최대 크롤링 페이지 수 (None이면 전체)
            keyword: 검색 키워드
        """
        # 초기 페이지 접속
        self.driver.get(f"{self.BASE_URL}?menu_grp=MENU_NEW04&menu_no=2815")
        time.sleep(3)

        # 키워드 검색
        if keyword:
            self.search_keyword(keyword)

        # 총 페이지 수 확인
        total_pages = self.get_total_pages()
        print(f"총 {total_pages} 페이지 발견")

        if max_pages:
            total_pages = min(total_pages, max_pages)

        print(f"{total_pages} 페이지 크롤링 시작...")

        all_data = []

        for page in range(1, total_pages + 1):
            print(f"페이지 {page}/{total_pages} 크롤링 중...")

            if page > 1:
                self.navigate_to_page(page)

            page_data = self.extract_table_data()
            all_data.extend(page_data)

            print(f"  -> {len(page_data)}개 항목 수집")
            time.sleep(1)

        self.data = all_data
        return all_data

    def save_to_csv(self, filename: str = "albumin_data.csv", output_dir: str = "output"):
        """CSV 파일로 저장"""
        if not self.data:
            print("저장할 데이터가 없습니다.")
            return

        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / filename

        df = pd.DataFrame(self.data)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {filepath}")
        return filepath

    def save_to_json(self, filename: str = "albumin_data.json", output_dir: str = "output"):
        """JSON 파일로 저장"""
        if not self.data:
            print("저장할 데이터가 없습니다.")
            return

        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {filepath}")
        return filepath

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()


def main():
    print("=" * 60)
    print("식품안전나라 특수용도식품 크롤링 시작")
    print("=" * 60)

    crawler = FoodSafetyKoreaCrawler(headless=True)

    try:
        # 알부민 키워드로 검색하여 크롤링
        # max_pages를 None으로 설정하면 전체 페이지 크롤링
        data = crawler.crawl_all_pages(max_pages=None, keyword="알부민")

        if data:
            print(f"\n총 {len(data)}개 항목 수집 완료")

            # 저장
            crawler.save_to_csv("albumin_special_food.csv")
            crawler.save_to_json("albumin_special_food.json")
        else:
            print("\n수집된 데이터가 없습니다.")
            print("키워드를 변경하거나 전체 데이터를 수집해보세요.")

            # 전체 데이터 수집 시도
            print("\n전체 데이터 수집을 시도합니다...")
            data = crawler.crawl_all_pages(max_pages=5, keyword=None)

            if data:
                crawler.save_to_csv("special_food_all.csv")
                crawler.save_to_json("special_food_all.json")

    except Exception as e:
        print(f"크롤링 오류: {e}")

    finally:
        crawler.close()

    print("\n크롤링 완료!")


if __name__ == "__main__":
    main()
