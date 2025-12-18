"""
作文管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import json
import math
from app.database import get_db
from app.models import Essay, Batch, Evaluation, Prompt, Score, Genre, Grade
from app.schemas import EssayListResponse, EssayListItem, EssayDetailResponse
from app.utils import logger
from app.config import settings

router = APIRouter()


@router.get("", response_model=EssayListResponse, summary="获取作文列表(支持筛选)")
async def get_essays(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    batch_id: Optional[int] = Query(None, description="批次ID筛选"),
    grade_id: Optional[int] = Query(None, description="年级ID筛选"),
    student_name: Optional[str] = Query(None, description="学生姓名搜索"),
    db: Session = Depends(get_db)
):
    """
    获取作文列表,支持分页和多种筛选条件
    - page: 页码(从1开始)
    - page_size: 每页数量(默认20)
    - batch_id: 按批次筛选
    - grade_id: 按年级筛选
    - student_name: 按学生姓名模糊搜索
    """
    try:
        # 构建查询
        query = db.query(Essay).filter_by(status=1)

        # 批次筛选
        if batch_id:
            query = query.filter(Essay.batch_id == batch_id)

        # 年级筛选(通过批次关联)
        if grade_id:
            query = query.join(Batch).filter(Batch.grade_id == grade_id)

        # 学生姓名搜索
        if student_name:
            query = query.filter(Essay.student_name.like(f"%{student_name}%"))

        # 总数统计
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        essays = query.order_by(Essay.create_date.desc()).offset(offset).limit(page_size).all()

        # 组装响应数据
        essay_items = []
        for essay in essays:
            # 获取评价次数和最新评价时间
            evaluation_info = db.query(
                func.count(Evaluation.id).label('count'),
                func.max(Evaluation.create_date).label('latest_date')
            ).filter(
                Evaluation.essay_id == essay.id,
                Evaluation.status == 1
            ).first()

            essay_data = {
                "id": essay.id,
                "batch_id": essay.batch_id,
                "batch_title": essay.batch.essay_title if essay.batch else "",
                "student_name": essay.student_name,
                "word_count": essay.word_count,
                "score_system": essay.score_system,
                "original_score": essay.original_score,
                "evaluation_count": evaluation_info.count if evaluation_info else 0,
                "latest_evaluation_date": evaluation_info.latest_date if evaluation_info else None,
                "create_date": essay.create_date
            }
            essay_items.append(EssayListItem(**essay_data))

        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return EssayListResponse(
            essays=essay_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"获取作文列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作文列表失败"
        )


@router.get("/{essay_id}", response_model=EssayDetailResponse, summary="获取作文详情")
async def get_essay_detail(
    essay_id: int,
    db: Session = Depends(get_db)
):
    """获取指定作文的详细信息,包含批次信息"""
    essay = db.query(Essay).filter_by(id=essay_id, status=1).first()

    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作文不存在"
        )

    # 批次信息
    batch_info = {
        "id": essay.batch.id,
        "essay_title": essay.batch.essay_title,
        "essay_requirement": essay.batch.essay_requirement
    } if essay.batch else {}

    # 解析原始评分数据
    original_score_data = None
    if essay.original_score_data:
        try:
            original_score_data = json.loads(essay.original_score_data)
        except:
            pass

    essay_data = {
        "id": essay.id,
        "batch": batch_info,
        "student_name": essay.student_name,
        "essay_content": essay.essay_content,
        "word_count": essay.word_count,
        "score_system": essay.score_system,
        "original_score": essay.original_score,
        "original_score_data": original_score_data,
        "essay_image_path": essay.essay_image_path,
        "create_date": essay.create_date
    }

    return EssayDetailResponse(**essay_data)

@router.get("/{essay_id}/evaluations", summary="获取作文的所有评价记录（含评分数据）")
async def get_essay_evaluations(
    essay_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定作文的所有评价记录（附带评分数据）
    - 返回解析后的评价结果（JSON对象，前端可直接渲染）
    - 附带每个评价对应的所有评分数据（AI/用户评分，含维度分数）
    """
    # 检查作文是否存在
    essay = db.query(Essay).filter_by(id=essay_id, status=1).first()
    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作文不存在"
        )

    # 获取评价记录（按创建时间倒序）
    evaluations = db.query(Evaluation).filter_by(
        essay_id=essay_id,
        status=1
    ).order_by(Evaluation.create_date.desc()).all()

    # 组装响应数据
    evaluation_items = []
    for evaluation in evaluations:
        # 1. 解析评价结果（JSON字符串转对象）
        try:
            evaluation_result = json.loads(evaluation.evaluation_result)
        except (json.JSONDecodeError, TypeError):
            # 解析失败时返回原始字符串+提示
            evaluation_result = {
                "error": "评价结果解析失败",
                "raw_data": evaluation.evaluation_result
            }

        # 2. 查询该评价对应的所有评分记录
        scores = db.query(Score).filter_by(
            evaluation_id=evaluation.id,
            status=1
        ).all()

        # 3. 组装评分数据
        score_items = []
        for score in scores:
            # 解析维度分数（JSON字符串转对象）
            try:
                dimension_scores = json.loads(score.dimension_scores)
            except (json.JSONDecodeError, TypeError):
                dimension_scores = {
                    "error": "维度分数解析失败",
                    "raw_data": score.dimension_scores
                }
            
            # 获取评分提示词版本名称
            score_prompt = db.query(Prompt).filter_by(id=score.score_prompt_id, status=1).first()
            
            score_items.append({
                "score_id": score.id,
                "user_phone": score.user_phone,
                "score_type": score.score_type,  # ai/user
                "score_prompt_id": score.score_prompt_id,
                "score_prompt_version": score_prompt.version_name if score_prompt else "",
                "total_score": float(score.total_score),  # 确保浮点型
                "dimension_scores": dimension_scores,  # 解析后的维度分数
                "is_default": bool(score.is_default),
                "create_date": score.create_date,
                "update_date": score.update_date
            })

        # 4. 获取关联的名称信息
        confirmed_genre = db.query(Genre).filter_by(id=evaluation.confirmed_genre_id, status=1).first()
        confirmed_grade = db.query(Grade).filter_by(id=evaluation.confirmed_grade_id, status=1).first()
        detected_genre = db.query(Genre).filter_by(id=evaluation.detected_genre_id, status=1).first() if evaluation.detected_genre_id else None
        detected_grade = db.query(Grade).filter_by(id=evaluation.detected_grade_id, status=1).first() if evaluation.detected_grade_id else None
        analyze_prompt = db.query(Prompt).filter_by(id=evaluation.analyze_prompt_id, status=1).first()

        # 5. 组装单条评价记录
        evaluation_items.append({
            "evaluation_id": evaluation.id,
            "essay_id": evaluation.essay_id,
            "user_phone": evaluation.user_phone,
            # 文体信息
            "detected_genre_id": evaluation.detected_genre_id,
            "detected_genre_name": detected_genre.genre_name if detected_genre else "",
            "confirmed_genre_id": evaluation.confirmed_genre_id,
            "confirmed_genre_name": confirmed_genre.genre_name if confirmed_genre else "",
            "genre_confidence": float(evaluation.genre_confidence) if evaluation.genre_confidence else 0.0,
            # 年级信息
            "detected_grade_id": evaluation.detected_grade_id,
            "detected_grade_name": detected_grade.grade_name if detected_grade else "",
            "confirmed_grade_id": evaluation.confirmed_grade_id,
            "confirmed_grade_name": confirmed_grade.grade_name if confirmed_grade else "",
            # 评价提示词信息
            "analyze_prompt_id": evaluation.analyze_prompt_id,
            "analyze_prompt_version": analyze_prompt.version_name if analyze_prompt else "",
            # 评价结果（解析后）
            "evaluation_result": evaluation_result,  # 前端可直接渲染的JSON
            # 评分数据
            "scores": score_items,  # 该评价下的所有评分
            # 基础状态
            "is_latest": bool(evaluation.is_latest),
            "create_date": evaluation.create_date,
            "update_date": evaluation.update_date
        })

    return {
        "essay_id": essay_id,
        "essay_title": essay.essay_title if hasattr(essay, 'essay_title') else "",  # 补充作文标题
        "total_evaluations": len(evaluation_items),
        "evaluations": evaluation_items
    }