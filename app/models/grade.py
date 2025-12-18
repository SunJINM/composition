"""
年级模型
"""
from sqlalchemy import Column, String, Integer, UniqueConstraint
from app.models.base import BaseModel


class Grade(BaseModel):
    """年级表"""
    __tablename__ = 'composition_grades'

    grade_name = Column(String(50), nullable=False, comment='年级名称(7年级/8年级/9年级)')
    grade_code = Column(String(20), nullable=False, comment='年级编码(grade_7/grade_8/grade_9)')
    grade_level = Column(String(20), nullable=False, comment='学段(初中)')
    sort_order = Column(Integer, nullable=False, comment='排序')

    __table_args__ = (
        UniqueConstraint('grade_code', name='uk_grade_code'),
        {'comment': '年级表'}
    )

    def __repr__(self):
        return f"<Grade(id={self.id}, name={self.grade_name}, code={self.grade_code})>"
