"""
API依赖注入
提供通用的依赖项,如数据库会话、当前用户等
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User


def get_current_user(
    user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户(从请求头中获取手机号)

    Args:
        user_phone: 请求头中的用户手机号
        db: 数据库会话

    Returns:
        用户对象或None
    """
    if not user_phone:
        return None

    user = db.query(User).filter_by(phone=user_phone, status=1).first()
    return user


def require_user(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    要求必须登录

    Args:
        user: 当前用户

    Returns:
        用户对象

    Raises:
        HTTPException: 如果用户未登录
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或用户不存在"
        )
    return user
