"""
数据库连接管理
使用SQLAlchemy ORM
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,   # 连接回收时间(秒)
    echo=settings.APP_DEBUG  # 是否打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库(创建所有表)"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """删除所有表(谨慎使用)"""
    Base.metadata.drop_all(bind=engine)
