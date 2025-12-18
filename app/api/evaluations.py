"""
评价和评分API
核心业务流程: 评价 → 文体判断 → 评分
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from app.database import get_db
from app.models import Essay, Evaluation, Score, Prompt, Genre, Grade
from app.schemas import (
    EvaluationAnalyzeRequest,
    EvaluationResponse,
    GenreDetectionRequest,
    GenreDetectionResponse,
    ScoreCreateRequest,
    ScoreResponse
)
from app.services.ai_service import ai_service
from app.utils import logger, convert_score_to_system

router = APIRouter()


@router.post("/analyze", response_model=EvaluationResponse, summary="步骤1: 作文评价")
async def analyze_essay(
    request: EvaluationAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    作文评价接口
    - 调用AI分析作文内容
    - 保存评价结果到数据库
    - 返回评价结果和evaluation_id
    """
    try:
        # 1. 获取作文信息
        essay = db.query(Essay).filter_by(id=request.essay_id, status=1).first()
        if not essay:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作文不存在"
            )

        # 2. 获取提示词
        prompt = db.query(Prompt).filter_by(id=request.analyze_prompt_id, status=1).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词不存在"
            )

        # 3. 调用AI评价
        evaluation_result = ai_service.analyze_essay(
            essay_content=essay.essay_content,
            essay_title=essay.batch.essay_title if essay.batch else "",
            essay_requirement=essay.batch.essay_requirement if essay.batch else "",
            prompt=prompt.prompt_content
        )

        # 4. 将之前的评价标记为非最新
        db.query(Evaluation).filter_by(
            essay_id=request.essay_id,
            is_latest=1
        ).update({"is_latest": 0})

        # 5. 保存评价结果(暂不填充文体和年级信息,等待用户确认)
        evaluation = Evaluation(
            essay_id=request.essay_id,
            user_phone=request.user_phone,
            analyze_prompt_id=request.analyze_prompt_id,
            evaluation_result=json.dumps(evaluation_result, ensure_ascii=False),
            is_latest=1,
            status=1,
            # 注意: confirmed_genre_id 和 confirmed_grade_id 需要在文体判断后填充
            confirmed_genre_id=1,  # 临时默认值,需要后续更新
            confirmed_grade_id=1   # 临时默认值,需要后续更新
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        logger.info(f"作文评价完成: essay_id={request.essay_id}, evaluation_id={evaluation.id}")

        return EvaluationResponse(
            success=True,
            evaluation_id=evaluation.id,
            evaluation_result=evaluation_result
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"作文评价失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作文评价失败: {str(e)}"
        )


@router.post("/detect-genre", response_model=GenreDetectionResponse, summary="步骤2: 文体判断")
async def detect_genre(
    request: GenreDetectionRequest,
    db: Session = Depends(get_db)
):
    """
    文体判断接口
    - 调用AI判断作文的文体和年级
    - 返回判断结果供用户确认
    """
    try:
        # 调用AI判断文体
        detection_result = ai_service.detect_genre(
            essay_content=request.essay_content,
            essay_requirement=request.essay_requirement
        )

        # 查找对应的文体ID
        genre_code = detection_result.get('genre_code', 'narrative')
        genre = db.query(Genre).filter_by(genre_code=genre_code, status=1).first()
        if not genre:
            genre = db.query(Genre).filter_by(genre_code='narrative', status=1).first()

        # 查找对应的年级ID
        grade_level = detection_result.get('grade_level', 7)
        grade = db.query(Grade).filter_by(sort_order=grade_level, status=1).first()
        if not grade:
            grade = db.query(Grade).filter_by(sort_order=7, status=1).first()

        logger.info(f"文体判断完成: {genre.genre_name}, 年级: {grade.grade_name}, 置信度: {detection_result.get('confidence')}")

        return GenreDetectionResponse(
            success=True,
            detected_genre={
                "genre_id": genre.id,
                "genre_name": genre.genre_name,
                "genre_code": genre.genre_code,
                "confidence": detection_result.get('confidence', 0.8)
            },
            detected_grade={
                "grade_id": grade.id,
                "grade_name": grade.grade_name
            }
        )

    except Exception as e:
        logger.error(f"文体判断失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文体判断失败: {str(e)}"
        )


@router.post("/score", response_model=ScoreResponse, summary="步骤3: 作文评分")
async def score_essay(
    request: ScoreCreateRequest,
    db: Session = Depends(get_db)
):
    """
    作文评分接口
    - 更新评价记录的文体和年级信息
    - 调用AI进行评分
    - 根据作文的分制自动转换分数
    - 保存评分结果
    """
    try:
        # 1. 获取评价记录
        evaluation = db.query(Evaluation).filter_by(id=request.evaluation_id, status=1).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )

        # 2. 更新评价记录的文体和年级(用户确认后的值)
        evaluation.confirmed_genre_id = request.confirmed_genre_id
        evaluation.confirmed_grade_id = request.confirmed_grade_id

        # 3. 获取作文和提示词
        essay = evaluation.essay
        prompt = db.query(Prompt).filter_by(id=request.score_prompt_id, status=1).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评分提示词不存在"
            )

        # 4. 解析评价结果
        evaluation_result = json.loads(evaluation.evaluation_result)

        # 5. 调用AI评分(传入作文的分制)
        score_data = ai_service.score_essay(
            essay_content=essay.essay_content,
            essay_title=essay.batch.essay_title if essay.batch else "",
            essay_requirement=essay.batch.essay_requirement if essay.batch else "",
            evaluation_result=evaluation_result,
            prompt=prompt.prompt_content,
            score_system=essay.score_system
        )

        # 6. 保存评分结果
        score = Score(
            evaluation_id=request.evaluation_id,
            user_phone=request.user_phone,
            score_prompt_id=request.score_prompt_id,
            score_type='ai' if request.user_phone == 'system' else 'user',
            total_score=score_data.get('total_score', 0),
            dimension_scores=json.dumps(score_data.get('dimensions', {}), ensure_ascii=False),
            is_default=1,
            status=1
        )
        db.add(score)
        db.commit()
        db.refresh(score)

        logger.info(f"作文评分完成: evaluation_id={request.evaluation_id}, score_id={score.id}, total={score.total_score}/{essay.score_system}")

        return ScoreResponse(
            success=True,
            score_id=score.id,
            score_system=essay.score_system,
            score_data=score_data
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"作文评分失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作文评分失败: {str(e)}"
        )


@router.get("/{evaluation_id}/scores", summary="获取某次评价的所有评分记录")
async def get_evaluation_scores(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """获取指定评价的所有评分记录"""
    # 检查评价是否存在
    evaluation = db.query(Evaluation).filter_by(id=evaluation_id, status=1).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评价记录不存在"
        )

    # 获取评分记录
    scores = db.query(Score).filter_by(
        evaluation_id=evaluation_id,
        status=1
    ).order_by(Score.create_date.desc()).all()

    # 组装响应数据
    score_items = []
    for score in scores:
        score_data = {
            "score_id": score.id,
            "user_phone": score.user_phone,
            "score_type": score.score_type,
            "total_score": score.total_score,
            "score_system": evaluation.essay.score_system,
            "is_default": bool(score.is_default),
            "score_prompt_version": score.score_prompt.version_name if score.score_prompt else "",
            "create_date": score.create_date
        }
        score_items.append(score_data)

    return {
        "scores": score_items
    }
