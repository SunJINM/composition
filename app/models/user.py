"""
用户模型
"""
from sqlalchemy import Column, String, DateTime, Integer, Index
from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = 'composition_users'

    phone = Column(String(11), unique=True, nullable=False, comment='手机号')
    first_login_at = Column(DateTime, nullable=False, comment='首次登录时间')
    last_login_at = Column(DateTime, nullable=False, comment='最后登录时间')
    login_count = Column(Integer, default=1, comment='登录次数')

    __table_args__ = (
        Index('idx_phone', 'phone'),
        {'comment': '用户表'}
    )

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone})>"
