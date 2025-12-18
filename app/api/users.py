"""
用户相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User
from app.schemas import UserLogin, UserResponse
from app.utils import validate_phone, logger

router = APIRouter()


@router.post("/login", response_model=UserResponse, summary="用户登录")
async def login(
    request: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    - 如果用户不存在,自动创建新用户
    - 如果用户已存在,更新登录时间和次数
    """
    # 验证手机号格式
    if not validate_phone(request.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )

    try:
        # 查找用户
        user = db.query(User).filter_by(phone=request.phone, status=1).first()

        if user:
            # 用户已存在,更新登录信息
            user.last_login_at = datetime.now()
            user.login_count += 1
            logger.info(f"用户登录: {request.phone}, 登录次数: {user.login_count}")
        else:
            # 新用户,创建记录
            user = User(
                phone=request.phone,
                first_login_at=datetime.now(),
                last_login_at=datetime.now(),
                login_count=1,
                status=1
            )
            db.add(user)
            logger.info(f"新用户注册: {request.phone}")

        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        db.rollback()
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    user_phone: str,
    db: Session = Depends(get_db)
):
    """获取当前登录用户的信息"""
    user = db.query(User).filter_by(phone=user_phone, status=1).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return user
