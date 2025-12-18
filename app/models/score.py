"""
评分模型
"""
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Score(BaseModel):
    """评分表"""
    __tablename__ = 'composition_scores'

    evaluation_id = Column(Integer, ForeignKey('composition_evaluations.id'), nullable=False, comment='评价ID')
    user_phone = Column(String(11), ForeignKey('composition_users.phone'), nullable=False, comment='评分人手机号(system表示AI)')
    score_prompt_id = Column(Integer, ForeignKey('composition_prompts.id'), nullable=False, comment='使用的评分提示词ID')
    score_type = Column(String(20), nullable=False, comment='评分类型(ai/user)')
    total_score = Column(Float, nullable=False, comment='总分')
    dimension_scores = Column(Text, nullable=False, comment='各维度分数(JSON字符串)')
    is_default = Column(TINYINT, default=0, comment='是否默认评分(1:是,0:否)')

    # 关联关系
    evaluation = relationship("Evaluation", back_populates="scores")
    user = relationship("User", backref="scores")
    score_prompt = relationship("Prompt", foreign_keys=[score_prompt_id])

    __table_args__ = (
        Index('idx_evaluation', 'evaluation_id'),
        Index('idx_user', 'user_phone'),
        {'comment': '评分表'}
    )

    def __repr__(self):
        return f"<Score(id={self.id}, evaluation_id={self.evaluation_id}, type={self.score_type}, total={self.total_score})>"
