import os
import json
import sys
from datetime import datetime

# 프로젝트 루트 경로를 path에 추가하여 src 모듈 임포트 가능하게 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import engine, SessionLocal
from src.models.models import Base, AiNews, CommunityPost

def init_db():
    """테이블 생성"""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

def migrate_ai_news(db, data_dir):
    """AI 뉴스 데이터 마이그레이션"""
    news_dir = os.path.join(data_dir, "ai_news")
    if not os.path.exists(news_dir):
        print(f"Directory not found: {news_dir}")
        return

    print(f"Migrating AI News from {news_dir}...")
    files = [f for f in os.listdir(news_dir) if f.endswith(".json")]
    
    count = 0
    for filename in files:
        filepath = os.path.join(news_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data_list = json.load(f)
                
                # 파일 형식이 리스트인지 단일 객체인지 확인
                if isinstance(data_list, dict):
                    data_list = [data_list]
                
                for item in data_list:
                    # 중복 체크 (제목 기준)
                    exists = db.query(AiNews).filter(AiNews.title == item.get("title")).first()
                    if not exists:
                        news = AiNews(
                            title=item.get("title"),
                            content=item.get("content"),
                            source=item.get("source", "Unknown")
                        )
                        db.add(news)
                        count += 1
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    db.commit()
    print(f"Migrated {count} AI News items.")

def migrate_community(db, data_dir):
    """커뮤니티 데이터 마이그레이션"""
    comm_dir = os.path.join(data_dir, "community")
    if not os.path.exists(comm_dir):
        print(f"Directory not found: {comm_dir}")
        return

    print(f"Migrating Community Posts from {comm_dir}...")
    files = [f for f in os.listdir(comm_dir) if f.endswith(".json")]
    
    count = 0
    for filename in files:
        filepath = os.path.join(comm_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                item = json.load(f)
                
                # ID 기준으로 중복 체크
                exists = db.query(CommunityPost).filter(CommunityPost.id == item.get("id")).first()
                if not exists:
                    # 날짜 파싱 처리
                    created_at_str = item.get("created_at")
                    created_at = None
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str)
                        except ValueError:
                            pass # 파싱 실패시 None

                    post = CommunityPost(
                        id=str(item.get("id")),
                        title=item.get("title"),
                        content=item.get("content"),
                        author=item.get("author"),
                        view_count=item.get("view_count", 0),
                        likes=item.get("likes", 0),
                        source=item.get("source"),
                        created_at=created_at
                    )
                    db.add(post)
                    count += 1
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    db.commit()
    print(f"Migrated {count} Community Posts.")

def main():
    # 데이터 디렉토리 경로 (프로젝트 루트의 data 폴더)
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        # 1. 테이블 생성
        init_db()
        
        # 2. 데이터 마이그레이션 실행
        migrate_ai_news(db, data_dir)
        migrate_community(db, data_dir)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
