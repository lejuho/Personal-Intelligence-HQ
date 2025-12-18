from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from src.core.database import engine, Base
from src.core.scheduler import start_scheduler, shutdown_scheduler, run_full_batch

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB 테이블 생성
    print("Checking and creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables ready.")

    # 2. 스케줄러 시작
    start_scheduler()
    
    yield
    
    # 앱 종료 시 스케줄러 종료
    shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Investment HQ API is running. Scheduler is active."}

@app.post("/run-batch")
def trigger_batch(background_tasks: BackgroundTasks):
    """수동으로 전체 배치 작업을 실행합니다 (백그라운드)"""
    background_tasks.add_task(run_full_batch)
    return {"message": "Batch job triggered in background."}
