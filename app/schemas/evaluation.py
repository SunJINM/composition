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

class AIScoreRequest(BaseModel):
    essay_content: str
    essay_title: Optional[str] = ""
    essay_requirement: Optional[str] = ""
    prompt: str
    essay_id: int = Field(..., description="作文ID")
    analyze_prompt_id: int = Field(..., description="评价提示词ID")
    user_phone: str = Field(..., description="用户手机号")

class AIScoreWithAnalysisRequest(BaseModel):
    essay_content: str
    essay_title: Optional[str] = ""
    essay_requirement: Optional[str] = ""
    prompt: str
    analysis: Optional[Dict] = None  # 分析结果(可选)
    original_score_data: Optional[Dict] = None  # 原始评分数据(用于判断分制)
    evaluation_id: int = Field(default=None, description="评价ID")
    score_prompt_id: int = Field(default=None, description="评分提示词ID")
    user_phone: str = Field(default=None, description="用户手机号")


class EvaluationListResponse(BaseModel):
    """评价列表响应"""
    evaluations: list[EvaluationListItem]


class CompleteAnalysisRequest(BaseModel):
    """一站式作文批改请求"""
    # 必填字段
    essay_content: str = Field(..., description="作文文本内容(必填)")

    # 可选字段
    user_phone: str = Field(default="18348056312", description="用户手机号")
    essay_image: Optional[str] = Field(None, description="作文图片路径")
    essay_title: Optional[str] = Field("", description="作文题目")
    essay_requirement: Optional[str] = Field("", description="作文要求")
    student_name: Optional[str] = Field(None, description="学生姓名")
    score_system: int = Field(40, description="分制(10或40)")


class CompleteAnalysisResponse(BaseModel):
    """一站式作文批改响应"""
    success: bool
    evaluation_id: int
    essay_id: int
    batch_id: int
    total_score: int
    analysis_result: Dict[str, Any]
