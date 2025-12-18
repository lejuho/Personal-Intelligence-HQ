import sys
import os

# 1. 현재 파일 위치: .../src/collectors
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 프로젝트 루트 찾기: collectors -> src -> ProjectRoot (2단계 상위)
project_root = os.path.dirname(os.path.dirname(current_dir))

# 3. 시스템 경로에 추가
sys.path.append(project_root)

# 4. 모듈 임포트 (src.config로 접근)
import requests
import json
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from src.config import paths  # [수정] 경로 문제 해결

# [설정]
SAVE_DIR = paths.ASSET_DATA_DIR
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# regions.json 경로: ProjectRoot/src/config/regions.json
REGIONS_FILE = os.path.join(project_root, "src", "config", "regions.json")
API_KEY = "5b2470f873cda1780ad680e23785c1a358bcdc957f983d173a5af4d76e2cad2d"

def get_text(parent, tag_name, default="-"):
    element = parent.find(tag_name)
    return element.text.strip() if (element is not None and element.text) else default

def load_regions():
    if not os.path.exists(REGIONS_FILE):
        # 파일이 없으면 기본값(강남구) 리턴
        return [{"name": "서울 강남구", "code": "11680"}]
    
    with open(REGIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def collect_commercial_real_estate():
    print("🏗️ 상업용 부동산 멀티 수집 중...")
    
    targets = load_regions()
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    deal_ym = last_month.strftime("%Y%m")
    
    full_report = [f"[통합 상업용 부동산 실거래 ({deal_ym})]\n{'='*40}"]
    
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"

    for target in targets:
        name = target['name']
        code = target['code']
        print(f"   🔎 수집 중: {name}...")

        params = {
            "serviceKey": API_KEY, "LAWD_CD": code, "DEAL_YMD": deal_ym,
            "numOfRows": "50", "pageNo": "1" # 지역별 50개 제한
        }

        try:
            res = requests.get(url, params=params, verify=False)
            if res.status_code != 200: continue

            root = ET.fromstring(res.content)
            items = root.findall('.//item')
            
            if not items:
                continue

            region_deals = []
            for item in items:
                price = get_text(item, 'dealAmount')
                date = f"{get_text(item, 'dealMonth')}/{get_text(item, 'dealDay')}"
                b_type = get_text(item, 'buildingType')
                usage = get_text(item, 'buildingUse')
                
                if b_type == '일반':
                    area = get_text(item, 'plottageAr')
                    desc = f"🏢통건물 | {usage} | 대지 {area}㎡ | {price}만"
                else:
                    floor = get_text(item, 'floor')
                    area = get_text(item, 'excluUseAr')
                    desc = f"🏬집합 | {usage}({floor}층) | 전용 {area}㎡ | {price}만"
                
                region_deals.append(f"{date} | {desc}")

            # 지역별 헤더 추가
            if region_deals:
                # 가격순 정렬 (문자열 길이 대용)
                region_deals.sort(key=lambda x: len(x), reverse=True)
                full_report.append(f"\n### 📍 {name}")
                full_report.extend(region_deals[:10]) # 지역별 상위 10개만 기록 (너무 길면 안읽음)
        
        except Exception as e:
            print(f"   ⚠️ {name} 에러: {e}")
        
        time.sleep(0.5)

    # 최종 저장
    if len(full_report) > 1:
        with open(f"{SAVE_DIR}/commercial_real_estate.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(full_report))
        print(f"✅ 부동산 데이터 통합 저장 완료.")
    else:
        print("☁️ 수집된 거래 내역이 없습니다.")

if __name__ == "__main__":
    collect_commercial_real_estate()