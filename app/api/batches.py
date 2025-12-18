"""
批次管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Batch, Grade, Genre
from app.schemas import BatchResponse, BatchListResponse
from app.utils import logger

router = APIRouter()


@router.get("", response_model=BatchListResponse, summary="获取所有批次列表")
async def get_batches(
    db: Session = Depends(get_db)
):
    """
    获取所有批次列表
    返回批次信息,包含关联的年级和文体信息
    """
    try:
        batches = db.query(Batch).filter_by(status=1).order_by(Batch.create_date.desc()).all()

        # 组装响应数据
        batch_responses = []
        for batch in batches:
            batch_data = {
                "id": batch.id,
                "directory_name": batch.directory_name,
                "essay_title": batch.essay_title,
                "essay_requirement": batch.essay_requirement,
                "grade_id": batch.grade_id,
                "suggested_genre_id": batch.suggested_genre_id,
                "essay_count": batch.essay_count,
                "grade_name": batch.grade.grade_name if batch.grade else None,
                "suggested_genre_name": batch.suggested_genre.genre_name if batch.suggested_genre else None,
                "create_date": batch.create_date
            }
            batch_responses.append(BatchResponse(**batch_data))

        return BatchListResponse(
            batches=batch_responses,
            total=len(batch_responses)
        )

    except Exception as e:
        logger.error(f"获取批次列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取批次列表失败"
        )


@router.get("/{batch_id}", response_model=BatchResponse, summary="获取批次详情")
async def get_batch_detail(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """获取指定批次的详细信息"""
    batch = db.query(Batch).filter_by(id=batch_id, status=1).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在"
        )

    batch_data = {
        "id": batch.id,
        "directory_name": batch.directory_name,
        "essay_title": batch.essay_title,
        "essay_requirement": batch.essay_requirement,
        "grade_id": batch.grade_id,
        "suggested_genre_id": batch.suggested_genre_id,
        "essay_count": batch.essay_count,
        "grade_name": batch.grade.grade_name if batch.grade else None,
        "suggested_genre_name": batch.suggested_genre.genre_name if batch.suggested_genre else None,
        "create_date": batch.create_date
    }

    return BatchResponse(**batch_data)
