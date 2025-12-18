"""
提示词管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Prompt, Grade, Genre
from app.schemas import PromptCreate, PromptUpdate, PromptResponse, PromptListResponse
from app.utils import logger

router = APIRouter()


@router.get("", response_model=PromptListResponse, summary="获取提示词列表")
async def get_prompts(
    grade_id: Optional[int] = None,
    genre_id: Optional[int] = None,
    prompt_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取提示词列表
    - grade_id: 年级ID筛选
    - genre_id: 文体ID筛选
    - prompt_type: 提示词类型筛选(analyze/score)
    """
    try:
        query = db.query(Prompt).filter_by(status=1)

        # 应用筛选条件
        if grade_id:
            query = query.filter_by(grade_id=grade_id)
        if genre_id:
            query = query.filter_by(genre_id=genre_id)
        if prompt_type:
            query = query.filter_by(prompt_type=prompt_type)

        prompts = query.order_by(Prompt.create_date.desc()).all()

        # 查询年级和文体信息并组装响应
        result = []
        for prompt in prompts:
            grade = db.query(Grade).filter_by(id=prompt.grade_id).first()
            genre = db.query(Genre).filter_by(id=prompt.genre_id).first()

            result.append({
                "id": prompt.id,
                "grade_id": prompt.grade_id,
                "grade_name": grade.grade_name if grade else None,
                "genre_id": prompt.genre_id,
                "genre_name": genre.genre_name if genre else None,
                "prompt_type": prompt.prompt_type,
                "version_name": prompt.version_name,
                "prompt_content": prompt.prompt_content,
                "is_default": prompt.is_default,
                "created_by": prompt.created_by,
                "create_date": prompt.create_date,
                "update_date": prompt.update_date
            })

        return {
            "prompts": result,
            "total": len(result)
        }

    except Exception as e:
        logger.error(f"获取提示词列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取提示词列表失败"
        )


@router.get("/{prompt_id}", response_model=PromptResponse, summary="获取提示词详情")
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """获取单个提示词的详细信息"""
    prompt = db.query(Prompt).filter_by(id=prompt_id, status=1).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )

    # 查询年级和文体信息
    grade = db.query(Grade).filter_by(id=prompt.grade_id).first()
    genre = db.query(Genre).filter_by(id=prompt.genre_id).first()

    return {
        "id": prompt.id,
        "grade_id": prompt.grade_id,
        "grade_name": grade.grade_name if grade else None,
        "genre_id": prompt.genre_id,
        "genre_name": genre.genre_name if genre else None,
        "prompt_type": prompt.prompt_type,
        "version_name": prompt.version_name,
        "prompt_content": prompt.prompt_content,
        "is_default": prompt.is_default,
        "created_by": prompt.created_by,
        "create_date": prompt.create_date,
        "update_date": prompt.update_date
    }


@router.post("", response_model=PromptResponse, summary="创建提示词")
async def create_prompt(
    request: PromptCreate,
    db: Session = Depends(get_db)
):
    """
    创建新提示词
    - 验证年级和文体是否存在
    - 如果设置为默认,取消同类型的其他默认提示词
    """
    try:
        # 验证年级存在
        grade = db.query(Grade).filter_by(id=request.grade_id, status=1).first()
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="年级不存在"
            )

        # 验证文体存在
        genre = db.query(Genre).filter_by(id=request.genre_id, status=1).first()
        if not genre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文体不存在"
            )

        # 如果设置为默认,取消同年级、同文体、同类型的其他默认提示词
        if request.is_default:
            db.query(Prompt).filter_by(
                grade_id=request.grade_id,
                genre_id=request.genre_id,
                prompt_type=request.prompt_type,
                status=1
            ).update({"is_default": 0})

        # 创建新提示词
        prompt = Prompt(
            grade_id=request.grade_id,
            genre_id=request.genre_id,
            prompt_type=request.prompt_type,
            version_name=request.version_name,
            prompt_content=request.prompt_content,
            is_default=request.is_default,
            created_by=request.created_by,
            status=1
        )

        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        logger.info(f"创建提示词成功: ID={prompt.id}, 版本={prompt.version_name}")

        return {
            "id": prompt.id,
            "grade_id": prompt.grade_id,
            "grade_name": grade.grade_name,
            "genre_id": prompt.genre_id,
            "genre_name": genre.genre_name,
            "prompt_type": prompt.prompt_type,
            "version_name": prompt.version_name,
            "prompt_content": prompt.prompt_content,
            "is_default": prompt.is_default,
            "created_by": prompt.created_by,
            "create_date": prompt.create_date,
            "update_date": prompt.update_date
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建提示词失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建提示词失败"
        )


@router.put("/{prompt_id}", response_model=PromptResponse, summary="更新提示词")
async def update_prompt(
    prompt_id: int,
    request: PromptUpdate,
    db: Session = Depends(get_db)
):
    """
    更新提示词
    - 可以修改版本名称、内容、是否默认
    - 如果设置为默认,取消同类型的其他默认提示词
    """
    try:
        # 查找提示词
        prompt = db.query(Prompt).filter_by(id=prompt_id, status=1).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词不存在"
            )

        # 如果设置为默认,取消同年级、同文体、同类型的其他默认提示词
        if request.is_default:
            db.query(Prompt).filter(
                Prompt.id != prompt_id,
                Prompt.grade_id == prompt.grade_id,
                Prompt.genre_id == prompt.genre_id,
                Prompt.prompt_type == prompt.prompt_type,
                Prompt.status == 1
            ).update({"is_default": 0})

        # 更新字段
        if request.version_name is not None:
            prompt.version_name = request.version_name
        if request.prompt_content is not None:
            prompt.prompt_content = request.prompt_content
        if request.is_default is not None:
            prompt.is_default = request.is_default

        db.commit()
        db.refresh(prompt)

        logger.info(f"更新提示词成功: ID={prompt.id}")

        # 查询年级和文体信息
        grade = db.query(Grade).filter_by(id=prompt.grade_id).first()
        genre = db.query(Genre).filter_by(id=prompt.genre_id).first()

        return {
            "id": prompt.id,
            "grade_id": prompt.grade_id,
            "grade_name": grade.grade_name if grade else None,
            "genre_id": prompt.genre_id,
            "genre_name": genre.genre_name if genre else None,
            "prompt_type": prompt.prompt_type,
            "version_name": prompt.version_name,
            "prompt_content": prompt.prompt_content,
            "is_default": prompt.is_default,
            "created_by": prompt.created_by,
            "create_date": prompt.create_date,
            "update_date": prompt.update_date
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新提示词失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新提示词失败"
        )


@router.delete("/{prompt_id}", summary="删除提示词")
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    删除提示词(软删除)
    - 将status设置为0
    """
    try:
        prompt = db.query(Prompt).filter_by(id=prompt_id, status=1).first()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词不存在"
            )

        # 软删除
        prompt.status = 0
        db.commit()

        logger.info(f"删除提示词成功: ID={prompt_id}")

        return {
            "success": True,
            "message": "删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除提示词失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除提示词失败"
        )
