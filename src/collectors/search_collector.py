import requests
import json
import os
import datetime
import time
import io
import sys
from pypdf import PdfReader # [추가] PDF 변환용

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from src.config import paths

# --- [설정] ---
SECRET_FILE = paths.SECRETS_FILE
HISTORY_FILE = paths.SEARCH_HISTORY_FILE
SAVE_DIR = paths.REPORTS_DATA_DIR # 기존 reports 폴더에 같이 저장
TODAY_YEAR = datetime.date.today().year

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def load_json(filepath):
    if not os.path.exists(filepath): return {} if filepath == SECRET_FILE else []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {} if filepath == SECRET_FILE else []

def save_history(history_list):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_list, f, indent=4)

def google_search(query, api_key, cx):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cx,
        'q': query,
        'fileType': 'pdf',
        'sort': 'date',
        'num': 2 # 상위 2개만 (API 절약)
    }
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json().get('items', [])
        return []
    except Exception as e:
        print(f"⚠️ 검색 에러: {e}")
        return []

def download_and_convert_pdf(url, title):
    """PDF 다운로드 후 텍스트로 변환하여 저장"""
    try:
        print(f"   📥 다운로드 중: {title}")
        res = requests.get(url, headers=HEADERS, timeout=15)
        
        if res.status_code == 200:
            # 1. 메모리 상에서 PDF 읽기
            pdf_file = io.BytesIO(res.content)
            reader = PdfReader(pdf_file)
            
            # 2. 텍스트 추출
            full_text = f"Title: {title}\nURL: {url}\nDATE: {datetime.date.today()}\n{'-'*30}\n\n"
            text_extracted = False
            
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    full_text += extracted + "\n"
                    text_extracted = True
            
            if not text_extracted:
                print("   ⚠️ 텍스트 추출 실패 (이미지 PDF일 가능성)")
                return False

            # 3. .txt 파일로 저장
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
            filename = f"{SAVE_DIR}/{safe_title}.txt" # 확장자를 txt로 변경
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_text)
                
            print(f"   ✅ 변환 및 저장 완료: {filename}")
            return True
        else:
            print(f"   ❌ 다운로드 실패 ({res.status_code})")
            return False
            
    except Exception as e:
        print(f"   ❌ 에러 발생: {e}")
        return False

def collect_reports():
    secrets = load_json(SECRET_FILE)
    api_key = secrets.get('google_api_key')
    cx = secrets.get('google_search_engine_id')
    
    if not api_key or not cx:
        print("❌ 구글 API 키가 없습니다.")
        return

    downloaded_urls = load_json(HISTORY_FILE)

    queries = [
        f"site:blackrock.com \"{TODAY_YEAR} Midyear Outlook\" filetype:pdf",
        f"site:blackrock.com \"{TODAY_YEAR} Global Outlook\" filetype:pdf",
        f"site:vanguard.com \"economic and market outlook\" {TODAY_YEAR} -fund -etf filetype:pdf",
        f"site:jpmorgan.com \"{TODAY_YEAR} Market Outlook\" filetype:pdf"
    ]

    print("🔎 글로벌 리포트 탐색 시작 (Weekly Check)...")
    
    new_count = 0
    for query in queries:
        print(f"\nQUERY: {query}")
        results = google_search(query, api_key, cx)
        
        if not results:
            print("   (결과 없음)")
            continue
        
        for item in results:
            link = item.get('link')
            title = item.get('title')
            
            if link in downloaded_urls:
                print(f"   ⏭️ [Pass] 이미 수집함")
                continue
            
            # PDF -> TXT 변환 저장 호출
            if download_and_convert_pdf(link, title):
                downloaded_urls.append(link)
                save_history(downloaded_urls)
                new_count += 1
            
            time.sleep(2)

    if new_count > 0:
        print(f"\n🎉 총 {new_count}개의 글로벌 리포트를 새로 추가했습니다.")
    else:
        print("\n💤 새로운 글로벌 리포트가 없습니다.")

if __name__ == "__main__":
    collect_reports()