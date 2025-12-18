"""
通用响应模式
"""
from pydantic import BaseModel
from typing import Optional, Any


class Response(BaseModel):
    """通用响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    detail: Optional[str] = None
