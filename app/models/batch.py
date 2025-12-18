"""
作文批次模型
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Batch(BaseModel):
    """作文批次表"""
    __tablename__ = 'composition_batches'

    directory_name = Column(String(100), unique=True, nullable=False, comment='批次目录名(唯一标识)')
    essay_title = Column(Text, nullable=False, comment='作文题目')
    essay_requirement = Column(Text, comment='作文要求(纯文本)')
    grade_id = Column(Integer, ForeignKey('composition_grades.id'), comment='年级ID')
    suggested_genre_id = Column(Integer, ForeignKey('composition_genres.id'), comment='建议文体ID')
    essay_count = Column(Integer, default=0, comment='该批次作文数量')

    # 关联关系
    grade = relationship("Grade", backref="batches")
    suggested_genre = relationship("Genre", backref="batches")
    essays = relationship("Essay", back_populates="batch")

    __table_args__ = (
        Index('idx_directory', 'directory_name'),
        Index('idx_grade', 'grade_id'),
        {'comment': '作文批次表'}
    )

    def __repr__(self):
        return f"<Batch(id={self.id}, directory={self.directory_name}, count={self.essay_count})>"
