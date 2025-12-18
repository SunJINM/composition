"""
数据库模型基类
包含所有表的通用字段
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql import func
from app.database import Base


class BaseModel(Base):
    """
    抽象基类,包含所有表的通用字段:
    - id: 主键
    - status: 状态(1:正常, 0:删除)
    - create_date: 创建时间
    - update_date: 更新时间
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    status = Column(TINYINT, default=1, comment='状态(1:正常,0:删除)')
    create_date = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_date = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment='更新时间'
    )
