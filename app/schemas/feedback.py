"""
用户反馈相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional


class FeedbackComparisonRequest(BaseModel):
    """评分对比反馈请求"""
    evaluation_id: int = Field(..., description="评价ID")
    score_id: int = Field(..., description="评分ID")
    user_phone: str = Field(..., description="用户手机号")
    which_accurate: str = Field(..., description="哪个更准确(original/ai)")
    reason: Optional[str] = Field(None, description="选择理由")


class FeedbackCustomScoreRequest(BaseModel):
    """自定义评分反馈请求"""
    evaluation_id: int = Field(..., description="评价ID")
    score_id: int = Field(..., description="评分ID")
    user_phone: str = Field(..., description="用户手机号")
    custom_scores: Dict[str, float] = Field(..., description="自定义评分维度分数")
    total_score: float = Field(..., description="总分")
    comment: Optional[str] = Field(None, description="评分说明")


class FeedbackCommentRequest(BaseModel):
    """文字点评反馈请求"""
    evaluation_id: int = Field(..., description="评价ID")
    score_id: int = Field(..., description="评分ID")
    user_phone: str = Field(..., description="用户手机号")
    comment: str = Field(..., description="点评内容")
    comment_type: str = Field("general", description="点评类型(general/suggestion/praise)")


class FeedbackIssueMarkRequest(BaseModel):
    """问题标注反馈请求"""
    evaluation_id: int = Field(..., description="评价ID")
    score_id: int = Field(..., description="评分ID")
    user_phone: str = Field(..., description="用户手机号")
    issue_type: str = Field(..., description="问题类型(grammar/logic/expression/structure)")
    issue_position: Dict[str, int] = Field(..., description="问题位置{start: 0, end: 10}")
    issue_description: str = Field(..., description="问题描述")
    suggested_fix: Optional[str] = Field(None, description="建议修改")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    feedback_id: int
    message: str = "反馈提交成功"


class FeedbackListItem(BaseModel):
    """反馈列表项"""
    feedback_id: int
    user_phone: str
    feedback_type: str
    feedback_data: Dict[str, Any]
    create_date: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    feedbacks: list[FeedbackListItem]
