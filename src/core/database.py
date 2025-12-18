from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발 환경용)
load_dotenv()

# Docker Compose 환경 변수에서 URL 가져오기 (기본값 설정)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:securepass123@localhost:5432/investment_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI 및 스크립트에서 사용할 DB 세션 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
