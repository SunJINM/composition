"""
文体模型
"""
from sqlalchemy import Column, String, Integer, UniqueConstraint
from app.models.base import BaseModel


class Genre(BaseModel):
    """文体表"""
    __tablename__ = 'composition_genres'

    genre_name = Column(String(50), nullable=False, comment='文体名称(记叙文/议论文)')
    genre_code = Column(String(20), nullable=False, comment='文体编码(narrative/argumentative)')
    description = Column(String(200), comment='文体描述')
    sort_order = Column(Integer, nullable=False, comment='排序')

    __table_args__ = (
        UniqueConstraint('genre_code', name='uk_genre_code'),
        {'comment': '文体表'}
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name={self.genre_name}, code={self.genre_code})>"
