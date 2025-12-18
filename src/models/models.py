from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from src.core.database import Base

class AiNews(Base):
    __tablename__ = "ai_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    source = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(String, primary_key=True)  # 원본 ID 유지
    title = Column(String, index=True)
    content = Column(JSON)  # 복잡한 구조는 JSON으로 저장
    author = Column(String)
    view_count = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    source = Column(String)
    created_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
