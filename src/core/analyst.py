import sqlite3
import glob
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import os
import hashlib
import time
import sys
from pypdf import PdfReader

# ---------------------------------------------------------
# [1] 경로 설정 수정 (여기가 범인!)
# ---------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))

# [수정 전] dirname을 3번 씀 -> OneDrive 폴더로 가버림
# project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# [수정 후] src/core -> src -> test (2번만 올라가야 정답)
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.append(project_root)

# ---------------------------------------------------------
# [2] 안전한 모듈 임포트
# ---------------------------------------------------------
try:
    from src.config import paths
except ImportError:
    # 혹시 모를 경로 에러 대비 Fallback
    class paths:
        DB_FILE = os.path.join(project_root, "data", "database", "my_chat_log.db")
        # (필요한 다른 경로들도 여기에 추가되거나, config가 정상 작동해야 함)
        ASSET_DATA_DIR = os.path.join(project_root, "data", "assets")
        TREND_DATA_DIR = os.path.join(project_root, "data", "trends")
        IPO_DATA_DIR = os.path.join(project_root, "data", "ipo_data")
        GURU_DATA_DIR = os.path.join(project_root, "data", "guru_data")
        NEWS_DATA_DIR = os.path.join(project_root, "data", "news")
        AI_NEWS_DATA_DIR = os.path.join(project_root, "data", "ai_news")
        REPORTS_DATA_DIR = os.path.join(project_root, "data", "reports")
        COMMUNITY_DATA_DIR = os.path.join(project_root, "data", "community")
        WEATHER_DATA_DIR = os.path.join(project_root, "data", "weather")
        SECRETS_FILE = os.path.join(project_root, "src", "config", "secrets.json")
        ANALYSIS_STATE_FILE = os.path.join(project_root, "data", "analysis_state.json")

# --- [설정] ---
DB_FILE = str(paths.DB_FILE)
IPO_DATA_DIR = paths.IPO_DATA_DIR
GURU_DATA_DIR = paths.GURU_DATA_DIR

# 폴더를 성격별로 분류
# [NEW] ASSET_DIRS에 IPO_DATA_DIR 추가
ASSET_DIRS = [paths.ASSET_DATA_DIR, paths.TREND_DATA_DIR, IPO_DATA_DIR] # 부동산, 상권, 공매 + IPO

TECH_DIRS = [paths.NEWS_DATA_DIR, paths.AI_NEWS_DATA_DIR, paths.REPORTS_DATA_DIR, paths.COMMUNITY_DATA_DIR] # 뉴스, 기술, 리포트
WEATHER_FILE = paths.WEATHER_DATA_DIR / "current_weather.txt"
STATE_FILE = paths.ANALYSIS_STATE_FILE

def load_api_key():
    try:
        with open(paths.SECRETS_FILE, 'r', encoding='utf-8') as f:
            secrets = json.load(f)
            return secrets.get('google_api_key')
    except Exception as e:
        print(f"⚠️ Key Load Error: {e}")
        return None

API_KEY = load_api_key()
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("❌ API Key not found in secrets.json")

try:
    from src.collectors.calendar_agent import get_market_seasonality
except ImportError:
    try:
         # Fallback for direct execution where src is not in path but sibling is
         from ..collectors.calendar_agent import get_market_seasonality
    except ImportError:
         def get_market_seasonality(): return "캘린더 정보 없음"

CORE_INTERESTS = """
1. Tech & AI: LLM, Agentic Workflow, Backend Architecture
2. Macro Investment: US Tech Stocks, Bitcoin, Interest Rates
3. Real Estate (Alpha): Gangnam Commercial Trend, Auction(Onbid)
4. Career & Market Signal: Hiring Trends (Which stack is hot?)
"""

# ---------------------------------------------------------
# 1. 헬퍼 함수 (데이터 로드)
# ---------------------------------------------------------

def convert_pdf_to_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted: text += extracted + "\n"
        return text
    except: return ""

def get_data_from_dirs(target_dirs):
    """특정 폴더 리스트에서 데이터 로드"""
    all_content = []
    for folder in target_dirs:
        # folder is a Path object, convert to str for checking existence if needed, 
        # but Path.exists() works. 
        if not folder.exists(): continue
        
        # Glob needs string path
        files = glob.glob(str(folder / "*"))
        files.sort(key=os.path.getmtime, reverse=True)
        
        count = 0
        for filepath in files:
            if count >= 3: break # 폴더별 3개 제한
            try:
                filename = os.path.basename(filepath)
                # 텍스트 제한을 조금 여유있게 (Flash 모델 기준)
                limit = 100000 
                
                if filepath.endswith(".json") and "state" not in filename:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        content = data.get('content', '')[:limit].replace('\n', ' ')
                        all_content.append(f"[{folder.name}] {data.get('title','No Title')}: {content}")
                    count += 1
                elif filepath.endswith(".txt"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text = f.read()[:limit].replace('\n', ' ')
                        all_content.append(f"[{folder.name}/{filename}] {text}")
                    count += 1
                elif filepath.endswith(".pdf"):
                    text = convert_pdf_to_text(filepath)
                    if text:
                        all_content.append(f"[{folder.name}] PDF: {text[:1000].replace('\n', ' ')}")
                        count += 1
            except: continue
    return "\n\n".join(all_content)

def get_recent_questions(days=1):
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute("SELECT question FROM chat_logs WHERE created_at >= ?", (since,))
        rows = cursor.fetchall()
        return "\n".join([f"- {r[0]}" for r in rows]) if rows else None
    except: return None
    finally: conn.close()

def save_insight_to_db(text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_insights 
                 (id INTEGER PRIMARY KEY, created_at DATETIME, content TEXT)''')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO daily_insights (created_at, content) VALUES (?, ?)", (now, text))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 2. 분석 에이전트 (Call Splitter)
# ---------------------------------------------------------

def call_gemini(prompt, model_name="gemini-2.5-pro"):
    """API 호출 및 재시도 로직"""
    model = genai.GenerativeModel(model_name)
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                print(f"   ⚠️ Quota Exceeded (429). 10초 대기 후 재시도... ({attempt+1}/3)")
                time.sleep(10) # 쿨타임
            else:
                print(f"   ❌ Error: {e}")
                return "분석 실패"
    return "분석 실패 (Resource Exhausted)"

def generate_daily_briefing():
    print("🧠 [Analyst] 멀티 스테이지 분석 시작...")

    # 데이터 로드 (섹터별 분리)
    asset_raw = get_data_from_dirs(ASSET_DIRS)
    tech_raw = get_data_from_dirs(TECH_DIRS)
    recent_qs = get_recent_questions()
    qs_text = recent_qs if recent_qs else CORE_INTERESTS
    
    # -----------------------------------------------------
    # Stage 1: 자산(부동산/공매) 분석
    # -----------------------------------------------------
    print("\n[Stage 1/3] 🏢 부동산 & 자산 분석 중...")
    prompt_asset = f"""
    당신은 '부동산 및 경매 전문가'입니다. 아래 데이터를 분석하여 핵심 인사이트를 추출하세요.
    
    [데이터]
    {asset_raw}
    
    [분석 목표]
    1. 강남구 상권 트렌드(뜨는 업종) 파악
    2. 공매(온비드)/실거래가 데이터에서 저평가(Road, Gap) 기회 포착
    3. 결론만 3줄로 요약.
    """
    asset_insight = call_gemini(prompt_asset)
    print("   ✅ 자산 분석 완료.")
    time.sleep(5) # API 쿨타임

    # -----------------------------------------------------
    # Stage 2: 기술 & 커리어 분석
    # -----------------------------------------------------
    print("\n[Stage 2/3] 💻 기술 & 채용 트렌드 분석 중...")
    prompt_tech = f"""
    당신은 'Tech HR 및 기술 전략가'입니다. 아래 지시와 **[나의 관심사/최근 질문]**을 참고하여 필요하면 검색하세요.

    [나의 관심사/최근 질문]
    {qs_text}
    
    [분석 목표]
    1. 채용 공고(Hiring)에서 가장 많이 요구하는 기술 스택 추출
    2. 글로벌 리포트/AI 뉴스에서 주목해야 할 기술 트렌드 파악
    3. 내 관심사와 어떤 연관이 있는지 분석
    4. 개발자가 준비해야 할 Action Item 3줄 요약.
    
    """
    tech_insight = call_gemini(prompt_tech)
    print("   ✅ 기술 분석 완료.")
    time.sleep(5) # API 쿨타임

    # -----------------------------------------------------
    # Stage 3: 최종 종합 (Synthesis)
    # -----------------------------------------------------
    print("\n[Stage 3/3] ⚡ 최종 전략 브리핑 작성 중...")
    
    final_prompt = f"""
    당신은 나의 **'Full-Stack 투자 전략 이사'**입니다.
    
    **[추가 데이터: 거장들의 시선(Gurus)]**
    {tech_insight} 

    

    ---
    **[나의 관심사]**
    {qs_text}

    **[분석 보고서 1: 자산/부동산]**
    {asset_insight}

    **[분석 보고서 2: 기술/커리어]**
    {tech_insight}
    
    ---
    **[최종 리포트 작성 지침: '거인의 어깨' 전략]**
    1. **Confluence Check:** 피터 틸(독점), 캐시 우드(성장), 조지 소로스(모멘텀), 래리 핑크(자본) 중 **2명 이상이 긍정적으로 보는 섹터**가 있다면 '강력 매수(Strong Buy)' 신호로 해석해.
    2. **Conflict Check:** 만약 래리 핑크(보수적)는 경고하는데 캐시 우드(공격적)가 매수한다면 '변동성 확대'로 해석해.
    

    앞서 분석한 두 가지 보고서를 융합하여 최종 데일리 브리핑을 작성하세요.
    ---
    **[최종 리포트 양식]**
    ## ⚡ Strategic Daily Briefing ({datetime.now().strftime('%Y-%m-%d')})

    ### 1. 🏙️ Real Estate Alpha (부동산/공매)
    * (자산 보고서 요약 및 구체적 투자 기회)

    ### 2. 🚀 Tech & Career Signal (기술/채용)
    * (기술 보고서 요약 및 학습 방향) 
    
    ### 3. 🔗 Insight Fusion (연결)
    * (예: "강남 상권에서 AI 기반 마케팅 솔루션 수요 증가 예상" 등 두 분야를 연결)
    
    ### 4. ✅ Action Plan
    * **Invest:** (확인할 매물/지역)
    * **Dev:** (학습할 기술)

    ### 5. ❓ Critical Question
    * (내 사고를 확장할 질문 1개)
    """
    
    final_report = call_gemini(final_prompt) # 모델 변경 가능
    
    # 저장
    save_insight_to_db(final_report)
    print("\n" + "="*50)
    print("🎉 모든 분석 완료! 결과:")
    print("="*50)
    print(final_report[:500] + "...\n(DB 저장됨)")

if __name__ == "__main__":
    generate_daily_briefing()
