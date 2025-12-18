"""
提示词模型
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Prompt(BaseModel):
    """提示词表"""
    __tablename__ = 'composition_prompts'

    grade_id = Column(Integer, ForeignKey('composition_grades.id'), nullable=False, comment='年级ID')
    genre_id = Column(Integer, ForeignKey('composition_genres.id'), nullable=False, comment='文体ID')
    prompt_type = Column(String(20), nullable=False, comment='提示词类型(analyze/score)')
    version_name = Column(String(50), nullable=False, comment='版本名称')
    prompt_content = Column(Text, nullable=False, comment='提示词内容')
    is_default = Column(TINYINT, default=0, comment='是否默认(1:是,0:否)')
    created_by = Column(String(11), comment='创建人手机号')

    # 关联关系
    grade = relationship("Grade", backref="prompts")
    genre = relationship("Genre", backref="prompts")

    __table_args__ = (
        Index('idx_grade_genre', 'grade_id', 'genre_id', 'prompt_type'),
        Index('idx_created_by', 'created_by'),
        {'comment': '提示词表'}
    )

    def __repr__(self):
        return f"<Prompt(id={self.id}, type={self.prompt_type}, version={self.version_name})>"
