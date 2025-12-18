import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# [설정]
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ipo_data")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def collect_korea_ipo():
    """38커뮤니케이션에서 한국 공모주 청약 일정 수집"""
    print("🇰🇷 한국 IPO 일정(38커뮤니케이션) 수집 중...")
    url = "http://www.38.co.kr/html/fund/index.htm?o=k"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'EUC-KR' # 38커뮤니케이션은 인코딩 주의
        soup = BeautifulSoup(res.text, "html.parser")
        
        table = soup.find("table", summary="공모주 청약일정")
        rows = table.find_all("tr")
        
        ipo_list = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5: continue
            
            try:
                name = cols[0].text.strip()
                schedule = cols[1].text.strip() # 청약일
                price = cols[2].text.strip()    # 공모가
                host = cols[4].text.strip()     # 주관사
                
                # 날짜 정보가 있는 유효한 행만 추출
                if "~" in schedule:
                    ipo_list.append(f"- [KR] {name} | 청약일: {schedule} | 공모가: {price} | 주관사: {host}")
            except:
                continue

        return ipo_list[:10] # 최신 10개만
        
    except Exception as e:
        print(f"⚠️ 한국 IPO 수집 실패: {e}")
        return []

def collect_us_ipo():
    """StockAnalysis에서 미국 IPO 캘린더 수집"""
    print("🇺🇸 미국 IPO 캘린더(StockAnalysis) 수집 중...")
    url = "https://stockanalysis.com/ipos/calendar/"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 테이블 찾기 (클래스명은 사이트 업데이트에 따라 변할 수 있어 보편적으로 탐색)
        tables = soup.find_all("table")
        if not tables:
            return []
            
        rows = tables[0].find_all("tr")[1:] # 헤더 제외
        
        ipo_list = []
        for row in rows[:10]: # 10개만
            cols = row.find_all("td")
            if len(cols) < 3: continue
            
            date = cols[0].text.strip()
            symbol = cols[1].text.strip()
            name = cols[2].text.strip()
            price = cols[3].text.strip() if len(cols) > 3 else "N/A"
            
            ipo_list.append(f"- [US] {name} ({symbol}) | 날짜: {date} | 예상가: {price}")
            
        return ipo_list
        
    except Exception as e:
        print(f"⚠️ 미국 IPO 수집 실패: {e}")
        return []

def run_collector():
    korea_ipos = collect_korea_ipo()
    us_ipos = collect_us_ipo()
    
    all_ipos = korea_ipos + us_ipos
    
    if all_ipos:
        content = f"[Global IPO Calendar Update: {datetime.now().strftime('%Y-%m-%d')}]\n"
        content += "="*50 + "\n"
        content += "\n".join(all_ipos)
        
        # 저장
        save_path = os.path.join(SAVE_DIR, "ipo_calendar.txt")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"🎉 IPO 데이터 수집 완료: {len(all_ipos)}건 저장됨.")
        print(f"📂 저장 경로: {save_path}")
    else:
        print("☁️ 수집된 예정 IPO 정보가 없습니다.")

if __name__ == "__main__":
    run_collector()