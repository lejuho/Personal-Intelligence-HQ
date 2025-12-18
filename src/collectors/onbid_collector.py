import requests
import xml.etree.ElementTree as ET
import time
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, "../../"))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "assets")
OUTPUT_FILE = os.path.join(DATA_DIR, "onbid_investment_list.txt")

if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

API_KEY = "5b2470f873cda1780ad680e23785c1a358bcdc957f983d173a5af4d76e2cad2d"
TARGET_REGIONS = ["서울특별시", "경기도", "인천광역시", "부산광역시"]

def analyze_investment_type(name, category, detail):
    tags = []
    full_text = f"{name} {category} {detail}".replace(" ", "")
    if "도로" in full_text or "도" in category:
        if "대지" not in category: tags.append("[🛣️도로]")
    if "지분" in full_text or "여지" in full_text: tags.append("[🍰지분]")
    if any(x in full_text for x in ["아파트", "다세대", "빌라", "오피스텔", "주거"]): tags.append("[🏠갭/주거]")
    tags.append("[💸매각]")
    return tags

def run_collector():
    print("="*60)
    print("🚀 온비드 수집기 (1줄 요약 모드)")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"DATE: {time.strftime('%Y-%m-%d')}\n\n")

    total_collected = 0
    for region in TARGET_REGIONS:
        print(f"📡 {region} 스캔 중...")
        # 파라미터 최적화
        final_url = "http://openapi.onbid.co.kr/openapi/services/ThingInfoInquireSvc/getUnifyUsageCltr"
        params = {"serviceKey": API_KEY, "pageNo": "1", "numOfRows": "50", "DPSL_MTD_CD": "0001", "SIDO": region}
        
        try:
            res = requests.get(final_url, params=params, timeout=30)
            if res.status_code != 200: continue
            
            root = ET.fromstring(res.text)
            if root.find('.//resultCode').text != '00': continue
            
            items = root.findall('.//item')
            if not items: continue

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for item in items:
                    cltr_nm = item.find('CLTR_NM').text or ""
                    price = item.find('MIN_BID_PRC').text or "0"
                    ctgr = item.find('CTGR_FULL_NM').text or ""
                    addr = item.find('LDNM_ADRS').text or ""
                    
                    tags = analyze_investment_type(cltr_nm, ctgr, item.find('GOODS_NM').text or "")
                    tag_str = " ".join(tags)
                    
                    # [핵심] 1줄 포맷팅
                    line = f"- {tag_str} {cltr_nm} | 💰{int(price):,}원 | 📍{addr}"
                    f.write(line + "\n")
                    total_collected += 1
            time.sleep(0.5)
        except: pass

    print(f"🎉 총 {total_collected}건 저장 완료: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_collector()