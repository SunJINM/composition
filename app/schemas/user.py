"""
用户相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserLogin(BaseModel):
    """用户登录请求"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    phone: str
    first_login_at: datetime
    last_login_at: datetime
    login_count: int

    class Config:
        from_attributes = True
