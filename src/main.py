from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
from src.core.database import engine, Base
from src.core.scheduler import start_scheduler, shutdown_scheduler, run_full_batch
from src.config import paths

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB 테이블 생성
    print("Checking and creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables ready.")
    
    # [확장프로그램용] my_chat_log.db 초기화
    init_ext_db()

    # 2. 스케줄러 시작
    start_scheduler()
    
    yield
    
    # 앱 종료 시 스케줄러 종료
    shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

# CORS 설정 (확장프로그램 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [확장프로그램 지원용 코드] ---
class ChatLog(BaseModel):
    question: str
    answer: str

def init_ext_db():
    try:
        conn = sqlite3.connect(paths.DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      created_at TEXT,
                      question TEXT,
                      answer TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS daily_insights
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      created_at TEXT,
                      content TEXT)''')
        conn.commit()
        conn.close()
        print(f"✅ Extension Database initialized: {paths.DB_FILE}")
    except Exception as e:
        print(f"⚠️ Extension DB Init Error: {e}")

@app.post("/save_all")
async def save_all_chats(logs: List[ChatLog]):
    try:
        conn = sqlite3.connect(paths.DB_FILE)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        saved_count = 0
        for log in logs:
            c.execute("SELECT id FROM chat_logs WHERE question = ?", (log.question,))
            if c.fetchone() is None:
                c.execute("INSERT INTO chat_logs (created_at, question, answer) VALUES (?, ?, ?)", 
                          (now, log.question, log.answer))
                saved_count += 1
        
        conn.commit()
        conn.close()
        return {"status": "success", "saved_count": saved_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest_insight")
async def get_latest_insight():
    try:
        conn = sqlite3.connect(paths.DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM daily_insights ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return {"status": "success", "content": row[0]} if row else {"status": "empty", "content": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Investment HQ API is running. Scheduler is active."}

from src.core.analyst import generate_daily_briefing

@app.post("/run-analysis")
def trigger_analysis(background_tasks: BackgroundTasks):
    """수동으로 분석(Analyst)만 실행합니다 (백그라운드)"""
    background_tasks.add_task(generate_daily_briefing)
    return {"message": "Analysis started in background."}
