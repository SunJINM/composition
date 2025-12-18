"""
提示词相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PromptBase(BaseModel):
    """提示词基础模式"""
    grade_id: int = Field(..., description="年级ID")
    genre_id: int = Field(..., description="文体ID")
    prompt_type: str = Field(..., description="提示词类型(analyze/score)")
    version_name: str = Field(..., description="版本名称")
    prompt_content: str = Field(..., description="提示词内容")
    is_default: bool = Field(False, description="是否默认")


class PromptCreate(PromptBase):
    """创建提示词"""
    created_by: Optional[str] = Field(None, description="创建人手机号")


class PromptUpdate(BaseModel):
    """更新提示词"""
    version_name: Optional[str] = None
    prompt_content: Optional[str] = None
    is_default: Optional[bool] = None


class PromptResponse(BaseModel):
    """提示词响应"""
    id: int
    grade_id: int
    grade_name: Optional[str] = None
    genre_id: int
    genre_name: Optional[str] = None
    prompt_type: str
    version_name: str
    prompt_content: str
    is_default: bool
    created_by: Optional[str] = None
    create_date: datetime
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    """提示词列表响应"""
    prompts: list[PromptResponse]
    total: int
