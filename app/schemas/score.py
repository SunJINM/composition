"""
评分相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class ScoreCreateRequest(BaseModel):
    """创建评分请求"""
    evaluation_id: int = Field(..., description="评价ID")
    score_prompt_id: int = Field(..., description="评分提示词ID")
    user_phone: str = Field(..., description="用户手机号")
    confirmed_genre_id: int = Field(..., description="确认的文体ID")
    confirmed_grade_id: int = Field(..., description="确认的年级ID")


class ScoreResponse(BaseModel):
    """评分响应"""
    success: bool
    score_id: int
    score_system: int
    score_data: Dict[str, Any]


class ScoreListItem(BaseModel):
    """评分列表项"""
    score_id: int
    user_phone: str
    score_type: str
    total_score: float
    score_system: int
    is_default: bool
    score_prompt_version: str
    create_date: datetime

    class Config:
        from_attributes = True


class ScoreListResponse(BaseModel):
    """评分列表响应"""
    scores: list[ScoreListItem]
