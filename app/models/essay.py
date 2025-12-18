"""
作文模型
"""
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Essay(BaseModel):
    """作文表"""
    __tablename__ = 'composition_essays'

    batch_id = Column(Integer, ForeignKey('composition_batches.id'), nullable=False, comment='批次ID')
    student_name = Column(String(100), comment='学生姓名')
    essay_content = Column(Text, nullable=False, comment='作文内容')
    essay_image_path = Column(String(500), comment='作文图片路径')
    analysis_report_path = Column(String(500), comment='分析报告路径')
    word_count = Column(Integer, nullable=False, comment='字数统计')
    score_system = Column(TINYINT, nullable=False, default=40, comment='分制(10:10分制, 40:40分制)')
    original_score = Column(Float, comment='原始评分')
    original_score_data = Column(Text, comment='原始评分详情(JSON字符串)')

    # 关联关系
    batch = relationship("Batch", back_populates="essays")
    evaluations = relationship("Evaluation", back_populates="essay")

    __table_args__ = (
        Index('idx_batch', 'batch_id'),
        Index('idx_student', 'student_name'),
        Index('idx_score_system', 'score_system'),
        {'comment': '作文表'}
    )

    def __repr__(self):
        return f"<Essay(id={self.id}, student={self.student_name}, batch_id={self.batch_id})>"
