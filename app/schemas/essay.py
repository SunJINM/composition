"""
作文相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class EssayBase(BaseModel):
    """作文基础模式"""
    batch_id: int = Field(..., description="批次ID")
    student_name: Optional[str] = Field(None, description="学生姓名")
    essay_content: str = Field(..., description="作文内容")
    essay_image_path: Optional[str] = Field(None, description="作文图片路径")
    score_system: int = Field(40, description="分制(10或40)")


class EssayCreate(EssayBase):
    """创建作文"""
    pass


class EssayListItem(BaseModel):
    """作文列表项"""
    id: int
    batch_id: int
    batch_title: str
    essay_image_path: str
    student_name: Optional[str]
    word_count: int
    score_system: int
    original_score: Optional[float]
    evaluation_count: int = 0
    latest_evaluation_date: Optional[datetime] = None
    create_date: datetime

    class Config:
        from_attributes = True


class EssayListResponse(BaseModel):
    """作文列表响应"""
    essays: list[EssayListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class EssayDetailResponse(BaseModel):
    """作文详情响应"""
    id: int
    batch: Dict[str, Any]  # 批次信息
    student_name: Optional[str]
    essay_content: str
    word_count: int
    score_system: int
    original_score: Optional[float]
    original_score_data: Optional[Dict[str, Any]]
    essay_image_path: Optional[str]
    create_date: datetime

    class Config:
        from_attributes = True
