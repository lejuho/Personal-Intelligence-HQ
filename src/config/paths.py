import os
from pathlib import Path

# [핵심] 이제 파일이 src/config 안에 있으므로 3번 올라가야 test 폴더(Root)가 나옵니다.
# 1. parent -> config
# 2. parent -> src
# 3. parent -> test (Project Root) ✅ 정답!
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------
# [1] 데이터 저장 경로 (test/data)
# ---------------------------------------------------------
DATA_DIR = BASE_DIR / "data"

# 하위 폴더들 정의
AI_NEWS_DATA_DIR = DATA_DIR / "ai_news"
WEATHER_DATA_DIR = DATA_DIR / "weather"
ASSET_DATA_DIR = DATA_DIR / "assets"
COMMUNITY_DATA_DIR = DATA_DIR / "community"
NEWS_DATA_DIR = DATA_DIR / "news"
REPORTS_DATA_DIR = DATA_DIR / "reports"
TREND_DATA_DIR = DATA_DIR / "trends"
IPO_DATA_DIR = DATA_DIR / "ipo_data"
GURU_DATA_DIR = DATA_DIR / "guru_data"
DB_DIR = DATA_DIR / "database"

# 폴더 없으면 자동 생성
for d in [DATA_DIR, AI_NEWS_DATA_DIR, WEATHER_DATA_DIR, ASSET_DATA_DIR, 
          COMMUNITY_DATA_DIR, NEWS_DATA_DIR, REPORTS_DATA_DIR, TREND_DATA_DIR, 
          IPO_DATA_DIR, GURU_DATA_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# [2] 설정 파일 경로 (test/src/config)
# ---------------------------------------------------------
# paths.py가 있는 바로 그 폴더(config)를 가리킵니다.
CONFIG_DIR = BASE_DIR / "src" / "config"

SETTINGS_FILE = CONFIG_DIR / "settings.json"
SECRETS_FILE = CONFIG_DIR / "secrets.json"

# ---------------------------------------------------------
# [3] 기타 파일 경로
# ---------------------------------------------------------
DB_FILE = DB_DIR / "my_chat_log.db"
ANALYSIS_STATE_FILE = DATA_DIR / "analysis_state.json"
DOWNLOAD_HISTORY_FILE = DATA_DIR / "download_history.json"
SEARCH_HISTORY_FILE = DATA_DIR / "search_history.json"