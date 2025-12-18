import os
from datetime import datetime
from duckduckgo_search import DDGS

# [설정]
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ipo_data")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

TODAY_YEAR = datetime.now().year

# 감시할 주요 권역 및 키워드
REGIONS = {
    "Europe": "Europe major IPO upcoming",
    "India": "India IPO market hot list", # 인도가 요즘 핫함
    "Japan": "Japan Tokyo Stock Exchange IPO upcoming",
    "Global": "Global biggest IPOs to watch"
}

def collect_global_ipo_news():
    print("🌍 글로벌 주요 IPO(비미국권) 뉴스 스캐닝 중...")
    
    report_lines = []
    
    with DDGS() as ddgs:
        for region, keyword in REGIONS.items():
            query = f"{keyword} {TODAY_YEAR} news"
            print(f"   🔎 검색 중: {region}...")
            
            try:
                # 상위 3개 기사만 추출 (핵심만)
                results = list(ddgs.text(query, max_results=3))
                
                if results:
                    report_lines.append(f"\n### 🌐 Region: {region}")
                    for r in results:
                        title = r['title']
                        link = r['href']
                        body = r['body']
                        report_lines.append(f"- [{title}]({link})\n  : {body}")
            except Exception as e:
                print(f"   ⚠️ {region} 검색 실패: {e}")

    if report_lines:
        content = f"[Global IPO Trends (Non-US) - {datetime.now().strftime('%Y-%m-%d')}]\n"
        content += "="*60 + "\n"
        content += "\n".join(report_lines)
        
        save_path = os.path.join(SAVE_DIR, "global_ipo_news.txt")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"🎉 글로벌 IPO 트렌드 수집 완료: {save_path}")
    else:
        print("☁️ 수집된 글로벌 뉴스가 없습니다.")

if __name__ == "__main__":
    collect_global_ipo_news()