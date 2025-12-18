from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# ---------------------------------------------------------
# [1] 경로 설정 (Project Root 연결 - 안전장치)
# ---------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
# core -> src -> project_root (2단계 상위)
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.append(project_root)

# 안전하게 config 로드
try:
    from src.config import paths
    DB_FILE = str(paths.DB_FILE)
except ImportError:
    # fallback
    DB_FILE = os.path.join(project_root, "data", "database", "my_chat_log.db")

# ---------------------------------------------------------
# [2] DB 초기화 함수 (테이블 생성)
# ---------------------------------------------------------
def init_db():
    """DB 파일과 테이블이 없으면 생성합니다."""
    # 폴더가 없으면 생성
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. 채팅 로그 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  created_at TEXT,
                  question TEXT,
                  answer TEXT)''')
    
    # 2. 데일리 인사이트 테이블 생성 (get_latest_insight용)
    c.execute('''CREATE TABLE IF NOT EXISTS daily_insights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  created_at TEXT,
                  content TEXT)''')
                  
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_FILE}")

# 서버 시작 전 DB 초기화 실행
init_db()

# ---------------------------------------------------------
# [3] FastAPI 앱 설정
# ---------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatLog(BaseModel):
    question: str
    answer: str

@app.get("/")
def read_root():
    return {"status": "running", "db_path": DB_FILE}

@app.get("/latest_insight")
async def get_latest_insight():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 가장 최근 인사이트 가져오기
        cursor.execute("SELECT content FROM daily_insights ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"status": "success", "content": row[0]}
        else:
            return {"status": "empty", "content": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/save_all")
async def save_all_chats(logs: List[ChatLog]):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        saved_count = 0
        
        for log in logs:
            # [중복 방지] 똑같은 질문 내용이 이미 DB에 있는지 확인
            c.execute("SELECT id FROM chat_logs WHERE question = ?", (log.question,))
            data = c.fetchone()
            
            if data is None: # DB에 없을 때만 저장
                c.execute("INSERT INTO chat_logs (created_at, question, answer) VALUES (?, ?, ?)", 
                          (now, log.question, log.answer))
                saved_count += 1
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "saved_count": saved_count}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0으로 열어야 외부(확장프로그램 등)에서 접속이 원활할 수 있음
    uvicorn.run(app, host="127.0.0.1", port=8000)