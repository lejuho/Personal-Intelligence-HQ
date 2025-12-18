import requests
import os
import json
import time

from config import paths
SAVE_DIR = paths.TREND_DATA_DIR
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

def load_settings():
    try:
        with open("settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def collect_hiring_trends():
    settings = load_settings()
    api_key = settings.get("api_keys", {}).get("saramin_api_key", "")
    
    # 키가 없거나 기본값이면 실행 중단 (에러 방지)
    if not api_key or "YOUR" in api_key:
        print("⚠️ 사람인 API 키가 설정되지 않았습니다. (건너뜀)")
        return

    print("👔 채용 트렌드(Saramin) 분석 중...")
    
    url = "https://oapi.saramin.co.kr/job-search"
    headers = {"Accept": "application/json"}
    
    # [전략] 사용자의 핵심 기술 스택 위주로 검색
    keywords = "backend java spring ai llm"
    
    params = {
        "access-key": api_key,
        "keywords": keywords,
        "count": 20,       # 20개 정도면 트렌드 파악 충분
        "sort": "rc",      # 등록일순 (최신 트렌드)
        "fields": "posting-date,expiration-date,keyword-code,count"
    }
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        
        if res.status_code != 200:
            print(f"❌ 사람인 API 연결 실패: {res.status_code}")
            return

        data = res.json()
        jobs = data.get('jobs', {}).get('job', [])
        
        report = []
        for job in jobs:
            try:
                company = job['company']['detail']['name']
                title = job['position']['title']
                # 기술 스택 정보가 있으면 가져오기
                tech_list = job['position'].get('job-code', {}).get('name', 'N/A')
                date = job['opening-timestamp'] # 등록일
                
                report.append(f"- [{company}] {title} | Tech: {tech_list}")
            except:
                continue
            
        if report:
            content = f"[Tech Hiring Trend (Keywords: {keywords})]\n" + "\n".join(report)
            with open(f"{SAVE_DIR}/hiring.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 채용 데이터 저장 완료 ({len(report)}건)")
        else:
            print("⚠️ 검색된 채용 공고가 없습니다.")
            
    except Exception as e:
        print(f"⚠️ 채용 수집 실패: {e}")

if __name__ == "__main__":
    collect_hiring_trends()