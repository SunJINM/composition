"""
评价模型
"""
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Evaluation(BaseModel):
    """评价表"""
    __tablename__ = 'composition_evaluations'

    essay_id = Column(Integer, ForeignKey('composition_essays.id'), nullable=False, comment='作文ID')
    user_phone = Column(String(11), ForeignKey('composition_users.phone'), nullable=False, comment='评价人手机号')
    analyze_prompt_id = Column(Integer, ForeignKey('composition_prompts.id'), nullable=False, comment='使用的评价提示词ID')
    detected_genre_id = Column(Integer, ForeignKey('composition_genres.id'), comment='AI判断的文体ID')
    detected_grade_id = Column(Integer, ForeignKey('composition_grades.id'), comment='AI判断的年级ID')
    confirmed_genre_id = Column(Integer, ForeignKey('composition_genres.id'), nullable=False, comment='用户确认的文体ID')
    confirmed_grade_id = Column(Integer, ForeignKey('composition_grades.id'), nullable=False, comment='用户确认的年级ID')
    genre_confidence = Column(Float, comment='AI判断文体的置信度(0-1)')
    evaluation_result = Column(Text, nullable=False, comment='评价结果(JSON字符串)')
    is_latest = Column(TINYINT, default=1, comment='是否最新评价(1:是,0:否)')

    # 关联关系
    essay = relationship("Essay", back_populates="evaluations")
    user = relationship("User", backref="evaluations")
    analyze_prompt = relationship("Prompt", foreign_keys=[analyze_prompt_id])
    detected_genre = relationship("Genre", foreign_keys=[detected_genre_id])
    detected_grade = relationship("Grade", foreign_keys=[detected_grade_id])
    confirmed_genre = relationship("Genre", foreign_keys=[confirmed_genre_id])
    confirmed_grade = relationship("Grade", foreign_keys=[confirmed_grade_id])
    scores = relationship("Score", back_populates="evaluation")

    __table_args__ = (
        Index('idx_essay', 'essay_id'),
        Index('idx_user', 'user_phone'),
        Index('idx_latest', 'essay_id', 'is_latest'),
        {'comment': '评价表'}
    )

    def __repr__(self):
        return f"<Evaluation(id={self.id}, essay_id={self.essay_id}, user={self.user_phone})>"
