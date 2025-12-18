"""
用户反馈模型
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Feedback(BaseModel):
    """用户反馈表"""
    __tablename__ = 'composition_user_feedbacks'

    evaluation_id = Column(Integer, ForeignKey('composition_evaluations.id'), nullable=False, comment='评价ID')
    score_id = Column(Integer, ForeignKey('composition_scores.id'), comment='评分ID(针对评分的反馈)')
    user_phone = Column(String(11), ForeignKey('composition_users.phone'), nullable=False, comment='反馈人手机号')
    feedback_type = Column(String(50), nullable=False, comment='反馈类型(comparison/custom_score/comment/issue_mark)')
    feedback_data = Column(Text, nullable=False, comment='反馈数据(JSON字符串)')

    # 关联关系
    evaluation = relationship("Evaluation", backref="feedbacks")
    score = relationship("Score", backref="feedbacks")
    user = relationship("User", backref="feedbacks")

    __table_args__ = (
        Index('idx_evaluation', 'evaluation_id'),
        Index('idx_score', 'score_id'),
        Index('idx_user', 'user_phone'),
        {'comment': '用户反馈表'}
    )

    def __repr__(self):
        return f"<Feedback(id={self.id}, type={self.feedback_type}, user={self.user_phone})>"
