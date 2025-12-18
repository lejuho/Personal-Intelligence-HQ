import sys
import os

# 1. 현재 파일의 위치: .../test/src/collectors
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 프로젝트 루트(test) 찾기: collectors -> src -> test (2번만 올라감)
project_root = os.path.dirname(os.path.dirname(current_dir))

# 3. 시스템 경로에 루트 추가
sys.path.append(project_root)

# 4. 모듈 임포트 (이제 루트에서 시작하므로 src.config로 불러옵니다)
import requests
import json
import time
from src.config import paths  # [수정] from config -> from src.config

# [설정]
SAVE_DIR = paths.TREND_DATA_DIR
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# regions.json 파일 경로 (src/config/regions.json)
REGIONS_FILE = os.path.join(project_root, "src", "config", "regions.json")

API_KEY = "5b2470f873cda1780ad680e23785c1a358bcdc957f983d173a5af4d76e2cad2d"

def load_regions():
    """지역 설정 파일 로드"""
    if not os.path.exists(REGIONS_FILE):
        print(f"⚠️ 설정 파일 없음: {REGIONS_FILE}")
        # 파일 없으면 강남구 기본값 리턴
        return [{"name": "서울 강남구", "code": "11680"}]
    
    with open(REGIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def collect_commercial_trend():
    print("🏪 상권 트렌드 멀티 스캔 중...")
    
    targets = load_regions()
    all_reports = []

    for target in targets:
        name = target['name']
        code = target['code']
        
        print(f"   🔎 분석 중: {name} ({code})...")
        
        url = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 200, 
            "divId": "signguCd", 
            "key": code, 
            "type": "json"         
        }
        
        try:
            res = requests.get(url, params=params, verify=False)
            data = res.json()
            
            if 'body' in data and 'items' in data['body']:
                items = data['body']['items']
                
                # 카테고리 카운팅
                categories = {}
                for item in items:
                    cat = item.get('indsMclsNm') 
                    if cat: categories[cat] = categories.get(cat, 0) + 1
                
                top_cat = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                total = len(items)
                
                # 지역별 리포트 작성
                region_report = f"### 📍 {name}\n"
                for k, v in top_cat:
                    ratio = (v / total) * 100
                    region_report += f"- {k}: {v}개 ({ratio:.1f}%)\n"
                
                all_reports.append(region_report)
                
            else:
                print(f"   ⚠️ 데이터 없음: {name}")

        except Exception as e:
            print(f"   ❌ {name} 수집 실패: {e}")
        
        time.sleep(1) # API 매너 호출 (초당 제한 방지)

    # 통합 저장
    if all_reports:
        content = f"[통합 상권 트렌드 분석]\n{'='*30}\n" + "\n".join(all_reports)
        with open(f"{SAVE_DIR}/commercial.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 총 {len(targets)}개 지역 상권 데이터 저장 완료.")

if __name__ == "__main__":
    collect_commercial_trend()