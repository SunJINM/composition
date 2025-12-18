"""
评价相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class EvaluationAnalyzeRequest(BaseModel):
    """作文评价请求"""
    essay_id: int = Field(..., description="作文ID")
    analyze_prompt_id: int = Field(..., description="评价提示词ID")
    user_phone: str = Field(..., description="用户手机号")


class GenreDetectionRequest(BaseModel):
    """文体判断请求"""
    essay_id: int = Field(..., description="作文ID")
    essay_requirement: str = Field(..., description="作文要求")
    essay_content: str = Field(..., description="作文内容")


class GenreDetectionResponse(BaseModel):
    """文体判断响应"""
    success: bool
    detected_genre: Dict[str, Any]
    detected_grade: Dict[str, Any]


class EvaluationResponse(BaseModel):
    """评价响应"""
    success: bool
    evaluation_id: int
    evaluation_result: Dict[str, Any]


class EvaluationListItem(BaseModel):
    """评价列表项"""
    evaluation_id: int
    user_phone: str
    genre_name: str
    grade_name: str
    analyze_prompt_version: str
    is_latest: bool
    create_date: datetime

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """评价列表响应"""
    evaluations: list[EvaluationListItem]
