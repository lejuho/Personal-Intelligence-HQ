import yfinance as yf
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

# --- [설정] ---
from src.config import paths
SAVE_DIR = paths.REPORTS_DATA_DIR
TODAY_STR = datetime.now().strftime("%Y-%m-%d")

# 1. 시장 지표 수집 (yfinance: history 모드)
def collect_market_indices():
    print("📉 주요 시장 지표 수집 중 (Yahoo Finance API)...")
    
    tickers = {
        "미국 10년물 국채": "^TNX",
        "달러 인덱스": "DX-Y.NYB",
        "원/달러 환율": "KRW=X",
        "WTI 원유": "CL=F",
        "구리 선물": "HG=F",
        "필라델피아 반도체": "^SOX",
        "공포지수(VIX)": "^VIX"
    }
    
    results = []
    
    for name, symbol in tickers.items():
        try:
            # [수정] fast_info 대신 history 사용 (주말/휴일 대응)
            ticker = yf.Ticker(symbol)
            # 최근 5일치 데이터를 가져와서 마지막 날짜(어제/금요일) 데이터를 씀
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                # 가장 최근 종가
                price = hist['Close'].iloc[-1]
                
                # 전일 종가 (데이터가 2개 이상일 때만)
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = ((price - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0
                
                res_str = f"[{name}] {price:,.2f} ({change_pct:+.2f}%)"
                results.append(res_str)
                print(f"   ✅ {res_str}")
            else:
                print(f"   ⚠️ 데이터 없음 (History Empty): {name}")
                
        except Exception as e:
            print(f"   ❌ 에러 ({name}): {e}")

    return "\n".join(results)

# 2. 경제 캘린더 수집 (Selenium: Eager 모드)
def collect_economic_calendar():
    print("\n📅 경제 캘린더 수집 중 (Investing.com via Selenium)...")
    
    url = "https://www.investing.com/economic-calendar/"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # [핵심 수정] 페이지 로드 전략 변경: 'eager'
    # HTML 콘텐츠만 로드되면(이미지/CSS/광고 로딩 전) 바로 넘어감 -> 타임아웃 방지
    chrome_options.page_load_strategy = 'eager'
    
    # 봇 탐지 회피
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    calendar_data = []

    try:
        # webdriver_manager로 드라이버 자동 설치 및 실행
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 타임아웃 설정 (최대 30초)
        driver.set_page_load_timeout(30)
        
        try:
            driver.get(url)
        except Exception as e:
            print(f"   ⚠️ 페이지 로딩 시간 초과 (무시하고 진행): {e}")
            # Eager 모드라 타임아웃 나도 HTML은 받아졌을 수 있음

        time.sleep(3) # 약간의 렌더링 대기

        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit() # 브라우저 닫기

        # 테이블 찾기
        table = soup.find('table', id='economicCalendarData')
        if not table:
            print("   ❌ 캘린더 테이블을 찾을 수 없습니다. (구조 변경 or 차단)")
            return "정보를 가져올 수 없음"

        rows = table.find_all('tr', class_='js-event-item')
        
        print(f"   🔎 오늘 예정된 중요 이벤트 필터링...")
        found_count = 0
        
        for row in rows:
            # 중요도 확인 logic
            bulls = row.select('.grayFullBullishIcon')
            importance = len(bulls)
            
            if importance >= 3:
                time_str = row.find('td', class_='time').text.strip()
                currency = row.find('td', class_='flagCur').text.strip()
                event_elem = row.find('td', class_='event')
                event = event_elem.text.strip() if event_elem else "이벤트명 없음"
                
                # 실제/예측 값 처리 (None 체크)
                actual_elem = row.find('td', class_='bold')
                actual = actual_elem.text.strip() if actual_elem else "-"
                
                fore_elem = row.find('td', class_='fore')
                forecast = fore_elem.text.strip() if fore_elem else "-"
                
                if currency in ['USD', 'KRW']:
                    info = f"[{time_str}] ({currency}) {event} | 예측: {forecast} / 실제: {actual}"
                    calendar_data.append(info)
                    print(f"   🌟 {info}")
                    found_count += 1
        
        if found_count == 0:
            print("   ℹ️ 오늘 예정된 '별 3개' 중요 일정(USD/KRW)이 없습니다.")
            return "오늘 주요 일정 없음"

    except Exception as e:
        print(f"   ⚠️ 캘린더 수집 실패: {e}")
        return f"수집 에러: {e}"

    return "\n".join(calendar_data)

def save_report(market_text, calendar_text):
    filename = f"{SAVE_DIR}/Daily_Macro_{TODAY_STR}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== 🌎 Daily Macro Briefing ({TODAY_STR}) ===\n\n")
        f.write("[1. 주요 시장 지표]\n")
        f.write(market_text + "\n\n")
        f.write("[2. 오늘 주요 경제 일정 (별 3개)]\n")
        f.write(calendar_text + "\n")
    print(f"\n✅ 매크로 리포트 저장 완료: {filename}")

if __name__ == "__main__":
    # 라이브러리 설치 안내
    # pip install yfinance selenium webdriver-manager beautifulsoup4
    market_data = collect_market_indices()
    calendar_data = collect_economic_calendar()
    save_report(market_data, calendar_data)