from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import time
import glob # 파일 목록 조회용
from config import paths

# --- [설정] ---
SAVE_DIR = paths.AI_NEWS_DATA_DIR
# Directory creation handled in config/paths.py

def parse_news_text(text):
    """뉴스 카드 텍스트 파싱"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    category = "일반"
    title = "No Title"
    content = ""
    
    for line in lines:
        if line.startswith("📰"):
            category = line.replace("📰", "").strip()
        elif "━━" in line or "──" in line:
            continue
        elif "👁" in line: break
        elif title == "No Title":
            title = line
        else:
            content += line + " "
            
    return {
        "title": title,
        "content": content.strip(),
        "category": category,
        "source": "AI News Stream (Selenium)"
    }

def is_duplicate(new_data):
    """가장 최신 파일과 내용을 비교하여 중복 여부 확인"""
    # 1. 폴더 내 json 파일들을 찾음 (pathlib 객체와 glob 호환성 고려하여 str로 변환)
    files = glob.glob(f"{SAVE_DIR}/*.json")
    
    # 2. 파일이 하나도 없으면 중복 아님
    if not files:
        return False
    
    # 3. 최신 파일(가장 마지막에 수정된 것) 찾기
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            
        # 4. 내용 비교 (리스트 전체 비교)
        # *주의: 순서가 바뀌거나 내용이 조금이라도 다르면 '다르다'고 판단함
        if new_data == old_data:
            print(f"💤 데이터 변경 없음. (최신 파일: {os.path.basename(latest_file)})")
            return True # 중복임
            
    except Exception as e:
        print(f"⚠️ 비교 중 오류 (무시하고 저장): {e}")
        
    return False # 중복 아님 (저장해야 함)

def collect_ai_news():
    print("🤖 AI News Stream 접속 중 (Selenium)...")
    
    options = webdriver.ChromeOptions()
    # [옵션] 다시 백그라운드로 돌리고 싶으면 아래 주석 해제 (지금은 안정성을 위해 켜둠)
    # options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        url = "https://vidraft-news-stream.hf.space"
        driver.get(url)
        
        print("⏳ 데이터 로딩 대기 중...")
        wait = WebDriverWait(driver, 30) # 넉넉하게 30초 대기
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))
        
        # 확실한 로딩을 위해 추가 대기
        time.sleep(10)
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        news_list = []
        for btn in buttons:
            text = btn.text
            if "📰" in text and "👁" in text:
                item = parse_news_text(text)
                if item['title'] != "No Title":
                    news_list.append(item)

        if news_list:
            # [핵심] 중복 검사 로직 추가
            if is_duplicate(news_list):
                print("🚫 저장 건너뜀.")
            else:
                filename = SAVE_DIR / f"ai_trend_{int(time.time())}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(news_list, f, ensure_ascii=False, indent=4)
                print(f"✅ 새로운 뉴스 업데이트 완료! -> {filename}")
        else:
            print("⚠️ 뉴스 카드를 찾지 못했습니다.")

    except Exception as e:
        print(f"❌ 수집 중 오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    collect_ai_news()
