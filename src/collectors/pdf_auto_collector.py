import requests
import json
import io
import sys
import os
from pypdf import PdfReader
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from src.config import paths

# --- [설정] ---
SECRET_FILE = paths.SECRETS_FILE
HISTORY_FILE = paths.DOWNLOAD_HISTORY_FILE # ID 기록 대장
SAVE_DIR = paths.REPORTS_DATA_DIR

# 저장소 생성
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def load_token():
    try:
        with open(SECRET_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('auth_token', '')
    except FileNotFoundError:
        print(f"❌ {SECRET_FILE} 파일이 없습니다.")
        return None

# [NEW] 히스토리 로드 함수
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# [NEW] 히스토리 저장 함수
def save_history(history_list):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_list, f, indent=4)

def get_latest_report_info(headers):
    """리포트 목록 API에서 최신 ID와 제목 가져오기"""
    list_url = "https://api.saveticker.com/api/reports/list?page=1&page_size=1&sort=created_at_desc"
    try:
        response = requests.get(list_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # 리스트 키 확인 (reports 혹은 report_list)
            report_list = data.get('reports', []) or data.get('report_list', [])
            
            if report_list:
                latest = report_list[0]
                return latest['id'], latest['title']
    except Exception as e:
        print(f"⚠️ 목록 조회 에러: {e}")
    return None, None

def collect_pdf_report():
    # 1. 준비
    token = load_token()
    if not token: return
    
    headers = {
        "User-Agent": "Mozilla/5.0 ...",
        "Authorization": token
    }
    
    # 2. 이미 받은 ID 목록 불러오기
    downloaded_ids = load_history()

    # 3. 최신 리포트 확인
    print("📡 최신 리포트 탐색 중...")
    report_id, title = get_latest_report_info(headers)
    
    if not report_id:
        print("❌ 리포트 정보를 가져오지 못했습니다.")
        return

    # 4. [핵심] ID로 중복 체크 (파일명 비교 X)
    if report_id in downloaded_ids:
        print(f"⏭️ [Pass] 이미 수집한 리포트입니다. (ID: {report_id})")
        return

    print(f"🆕 새 리포트 발견! 수집을 시작합니다: {title}")

    # 5. 상세 정보 및 다운로드 로직 (기존과 동일)
    detail_url = f"https://api.saveticker.com/api/reports/detail/{report_id}"
    res = requests.get(detail_url, headers=headers)
    
    if res.status_code != 200:
        print("❌ 상세 조회 실패 (토큰 만료 가능성)")
        return

    data = res.json()
    pdf_relative_url = data.get('report', {}).get('pdf_url')
    
    if not pdf_relative_url:
        print("⚠️ PDF 파일이 없습니다.")
        # PDF가 없더라도 ID는 기록해서 다시 체크 안 하게 할지 결정 필요
        # 여기서는 저장 안 함 (다음에 다시 시도하도록)
        return

    pdf_url = f"https://api.saveticker.com{pdf_relative_url}"
    pdf_res = requests.get(pdf_url, headers=headers)
    
    if pdf_res.status_code == 200:
        # 변환 및 저장
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{SAVE_DIR}/{safe_title}.txt"
        
        pdf_file = io.BytesIO(pdf_res.content)
        reader = PdfReader(pdf_file)
        
        full_text = f"Title: {title}\nID: {report_id}\nSource: {detail_url}\n{'-'*30}\n\n"
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"✅ 저장 완료: {filename}")
        
        # 6. [중요] 성공했으므로 ID 대장에 기록
        downloaded_ids.append(report_id)
        save_history(downloaded_ids)
        
    else:
        print("❌ PDF 다운로드 실패")

if __name__ == "__main__":
    collect_pdf_report()