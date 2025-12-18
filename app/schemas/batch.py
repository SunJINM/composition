"""
批次相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BatchBase(BaseModel):
    """批次基础模式"""
    directory_name: str = Field(..., description="批次目录名")
    essay_title: str = Field(..., description="作文题目")
    essay_requirement: Optional[str] = Field(None, description="作文要求")
    grade_id: Optional[int] = Field(None, description="年级ID")
    suggested_genre_id: Optional[int] = Field(None, description="建议文体ID")


class BatchCreate(BatchBase):
    """创建批次"""
    pass


class BatchResponse(BatchBase):
    """批次响应"""
    id: int
    essay_count: int
    grade_name: Optional[str] = None
    suggested_genre_name: Optional[str] = None
    create_date: datetime

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    """批次列表响应"""
    batches: list[BatchResponse]
    total: int
