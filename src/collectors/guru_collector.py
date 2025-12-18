import os
from datetime import datetime
from duckduckgo_search import DDGS

# [설정]
# 프로젝트 구조에 맞춰 경로 설정 (상위 폴더로 이동하여 data 폴더 찾기)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
SAVE_DIR = os.path.join(project_root, "data", "guru_data")

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

TODAY_YEAR = datetime.now().year

# 1. 감시할 거장 리스트와 키워드
GURUS = {
    "Peter Thiel": "Peter Thiel investment portfolio opinion",
    "Cathie Wood": "Cathie Wood Ark Invest latest buying stock",
    "George Soros": "George Soros market outlook portfolio",
    "Larry Fink": "Larry Fink BlackRock annual letter investment strategy",
    "Ken Griffin": "Ken Griffin Citadel market forecast" # 시타델 추가
}

# 2. 블룸버그/주요 리포트 우회 검색
PREMIUM_SOURCES = {
    "Bloomberg_Brief": "Bloomberg market wrap today summary",
    "Goldman_Sachs": "Goldman Sachs global investment research summary",
    "Morgan_Stanley": "Morgan Stanley market outlook report summary"
}

def collect_guru_insights():
    print("🧠 투자 거장(Gurus) 및 기관 리포트 스캐닝 중...")
    
    report_lines = []
    
    with DDGS() as ddgs:
        # 1. 거장들의 최신 발언 수집
        for name, query in GURUS.items():
            full_query = f"{query} {TODAY_YEAR} news"
            print(f"   🕵️‍♂️ 추적 중: {name}...")
            
            try:
                # 상위 2개만 (핵심 발언 위주)
                results = list(ddgs.text(full_query, max_results=2))
                
                if results:
                    report_lines.append(f"\n### 🗣️ {name}")
                    for r in results:
                        title = r['title']
                        link = r['href']
                        body = r['body']
                        report_lines.append(f"- [{title}]({link})\n  : {body}")
            except Exception as e:
                print(f"   ⚠️ {name} 검색 실패: {e}")

        # 2. 기관 리포트 요약 수집
        print("   📰 주요 기관(Bloomberg 등) 요약 검색 중...")
        for source, query in PREMIUM_SOURCES.items():
            full_query = f"{query} {TODAY_YEAR} news"
            try:
                results = list(ddgs.text(full_query, max_results=2))
                if results:
                    report_lines.append(f"\n### 🏦 {source}")
                    for r in results:
                        report_lines.append(f"- {r['title']}: {r['body']}")
            except: continue

    if report_lines:
        content = f"[Gurus & Institutional Insights - {datetime.now().strftime('%Y-%m-%d')}]\n"
        content += "="*60 + "\n"
        content += "\n".join(report_lines)
        
        save_path = os.path.join(SAVE_DIR, "guru_insights.txt")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"🎉 거장들의 인사이트 수집 완료: {save_path}")
    else:
        print("☁️ 새로운 인사이트가 없습니다.")

if __name__ == "__main__":
    collect_guru_insights()