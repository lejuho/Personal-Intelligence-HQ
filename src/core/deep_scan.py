from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from config import paths
SAVE_DIR = paths.AI_NEWS_DATA_DIR
# Directory creation handled in config/paths.py

def collect_via_selenium():
    print("🌐 브라우저를 열어 직접 수집합니다...")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # 화면 안 띄우고 백그라운드 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        url = "https://vidraft-news-stream.hf.space"
        driver.get(url)
        
        print("⏳ 페이지 로딩 대기 중... (약 10초)")
        # 뉴스 카드가 뜰 때까지 기다림 (최대 20초)
        wait = WebDriverWait(driver, 20)
        # 뉴스 카드 버튼의 클래스명 일부('news-card-button')가 로딩될 때까지 대기
        # *주의: svelte 클래스명은 바뀔 수 있으니 button 태그 자체를 기다림
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))
        
        # 데이터가 렌더링될 시간 추가 확보
        time.sleep(5) 
        
        print("🔍 뉴스 카드 추출 중...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        news_list = []
        for btn in buttons:
            text = btn.text
            # 뉴스 카드 특징: '📰' 아이콘과 '👁' 아이콘이 있음
            if "📰" in text and "👁" in text:
                # 텍스트 파싱 (제목, 내용 분리)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                title = "No Title"
                content = ""
                category = "일반"
                
                # 간단 파싱 로직
                if len(lines) > 0:
                    if "[" in lines[0]: category = lines[0]
                    else: title = lines[0]
                
                # 제목 찾기 (구분선 다음 줄)
                for i, line in enumerate(lines):
                    if "━━" not in line and "──" not in line and "📰" not in line:
                        if title == "No Title": title = line
                        elif "👁" not in line: content += line + " "

                if title != "No Title":
                    news_list.append({
                        "title": title,
                        "content": content.strip(),
                        "category": category,
                        "source": "AI News Stream (Selenium)"
                    })

        if news_list:
            filename = SAVE_DIR / f"ai_trend_selenium_{int(time.time())}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(news_list, f, ensure_ascii=False, indent=4)
            print(f"🎉 수집 성공! {len(news_list)}개 뉴스 저장됨 -> {filename}")
        else:
            print("⚠️ 뉴스 카드를 찾지 못했습니다. (로딩 지연 또는 선택자 문제)")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    collect_via_selenium()
