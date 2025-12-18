"""
用户反馈API
支持4种反馈类型: 评分对比、自定义评分、文字点评、问题标注
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from app.database import get_db
from app.models import Feedback, Evaluation, Score
from app.schemas import (
    FeedbackComparisonRequest,
    FeedbackCustomScoreRequest,
    FeedbackCommentRequest,
    FeedbackIssueMarkRequest,
    FeedbackResponse,
    FeedbackListResponse
)
from app.utils import logger

router = APIRouter()


@router.post("/comparison", response_model=FeedbackResponse, summary="提交评分对比反馈")
async def submit_comparison_feedback(
    request: FeedbackComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    提交评分对比反馈
    - 用户选择原始评分或AI评分哪个更准确
    - 可选填写理由
    """
    try:
        # 验证评价和评分是否存在
        evaluation = db.query(Evaluation).filter_by(id=request.evaluation_id, status=1).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )

        score = db.query(Score).filter_by(id=request.score_id, status=1).first()
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评分记录不存在"
            )

        # 构建反馈数据
        feedback_data = {
            "which_accurate": request.which_accurate,
            "reason": request.reason
        }

        # 保存反馈
        feedback = Feedback(
            evaluation_id=request.evaluation_id,
            score_id=request.score_id,
            user_phone=request.user_phone,
            feedback_type="comparison",
            feedback_data=json.dumps(feedback_data, ensure_ascii=False),
            status=1
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"评分对比反馈提交成功: feedback_id={feedback.id}, which_accurate={request.which_accurate}")

        return FeedbackResponse(
            success=True,
            feedback_id=feedback.id,
            message="评分对比反馈提交成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交评分对比反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.post("/custom-score", response_model=FeedbackResponse, summary="提交自定义评分反馈")
async def submit_custom_score_feedback(
    request: FeedbackCustomScoreRequest,
    db: Session = Depends(get_db)
):
    """
    提交自定义评分反馈
    - 用户对各个维度进行自定义评分
    - 可选填写评分说明
    """
    try:
        # 验证评价和评分是否存在
        evaluation = db.query(Evaluation).filter_by(id=request.evaluation_id, status=1).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )

        score = db.query(Score).filter_by(id=request.score_id, status=1).first()
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评分记录不存在"
            )

        # 构建反馈数据
        feedback_data = {
            "custom_scores": request.custom_scores,
            "total_score": request.total_score,
            "comment": request.comment
        }

        # 保存反馈
        feedback = Feedback(
            evaluation_id=request.evaluation_id,
            score_id=request.score_id,
            user_phone=request.user_phone,
            feedback_type="custom_score",
            feedback_data=json.dumps(feedback_data, ensure_ascii=False),
            status=1
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"自定义评分反馈提交成功: feedback_id={feedback.id}, total={request.total_score}")

        return FeedbackResponse(
            success=True,
            feedback_id=feedback.id,
            message="自定义评分反馈提交成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交自定义评分反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.post("/comment", response_model=FeedbackResponse, summary="提交文字点评反馈")
async def submit_comment_feedback(
    request: FeedbackCommentRequest,
    db: Session = Depends(get_db)
):
    """
    提交文字点评反馈
    - 用户对作文或评分进行文字点评
    - 支持不同点评类型(一般/建议/表扬)
    """
    try:
        # 验证评价和评分是否存在
        evaluation = db.query(Evaluation).filter_by(id=request.evaluation_id, status=1).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )

        score = db.query(Score).filter_by(id=request.score_id, status=1).first()
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评分记录不存在"
            )

        # 构建反馈数据
        feedback_data = {
            "comment": request.comment,
            "comment_type": request.comment_type
        }

        # 保存反馈
        feedback = Feedback(
            evaluation_id=request.evaluation_id,
            score_id=request.score_id,
            user_phone=request.user_phone,
            feedback_type="comment",
            feedback_data=json.dumps(feedback_data, ensure_ascii=False),
            status=1
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"文字点评反馈提交成功: feedback_id={feedback.id}, type={request.comment_type}")

        return FeedbackResponse(
            success=True,
            feedback_id=feedback.id,
            message="文字点评反馈提交成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交文字点评反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.post("/issue-mark", response_model=FeedbackResponse, summary="提交问题标注反馈")
async def submit_issue_mark_feedback(
    request: FeedbackIssueMarkRequest,
    db: Session = Depends(get_db)
):
    """
    提交问题标注反馈
    - 用户标注作文中的问题位置和类型
    - 可选提供修改建议
    """
    try:
        # 验证评价和评分是否存在
        evaluation = db.query(Evaluation).filter_by(id=request.evaluation_id, status=1).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )

        score = db.query(Score).filter_by(id=request.score_id, status=1).first()
        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评分记录不存在"
            )

        # 构建反馈数据
        feedback_data = {
            "issue_type": request.issue_type,
            "issue_position": request.issue_position,
            "issue_description": request.issue_description,
            "suggested_fix": request.suggested_fix
        }

        # 保存反馈
        feedback = Feedback(
            evaluation_id=request.evaluation_id,
            score_id=request.score_id,
            user_phone=request.user_phone,
            feedback_type="issue_mark",
            feedback_data=json.dumps(feedback_data, ensure_ascii=False),
            status=1
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"问题标注反馈提交成功: feedback_id={feedback.id}, type={request.issue_type}")

        return FeedbackResponse(
            success=True,
            feedback_id=feedback.id,
            message="问题标注反馈提交成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交问题标注反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.get("/evaluation/{evaluation_id}", response_model=FeedbackListResponse, summary="获取评价的所有反馈")
async def get_evaluation_feedbacks(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """获取指定评价的所有反馈记录"""
    # 检查评价是否存在
    evaluation = db.query(Evaluation).filter_by(id=evaluation_id, status=1).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评价记录不存在"
        )

    # 获取反馈记录
    feedbacks = db.query(Feedback).filter_by(
        evaluation_id=evaluation_id,
        status=1
    ).order_by(Feedback.create_date.desc()).all()

    # 组装响应数据
    feedback_items = []
    for feedback in feedbacks:
        feedback_data = json.loads(feedback.feedback_data)
        feedback_items.append({
            "feedback_id": feedback.id,
            "user_phone": feedback.user_phone,
            "feedback_type": feedback.feedback_type,
            "feedback_data": feedback_data,
            "create_date": feedback.create_date
        })

    return FeedbackListResponse(
        feedbacks=feedback_items
    )


@router.get("/score/{score_id}", response_model=FeedbackListResponse, summary="获取评分的所有反馈")
async def get_score_feedbacks(
    score_id: int,
    db: Session = Depends(get_db)
):
    """获取指定评分的所有反馈记录"""
    # 检查评分是否存在
    score = db.query(Score).filter_by(id=score_id, status=1).first()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评分记录不存在"
        )

    # 获取反馈记录
    feedbacks = db.query(Feedback).filter_by(
        score_id=score_id,
        status=1
    ).order_by(Feedback.create_date.desc()).all()

    # 组装响应数据
    feedback_items = []
    for feedback in feedbacks:
        feedback_data = json.loads(feedback.feedback_data)
        feedback_items.append({
            "feedback_id": feedback.id,
            "user_phone": feedback.user_phone,
            "feedback_type": feedback.feedback_type,
            "feedback_data": feedback_data,
            "create_date": feedback.create_date
        })

    return FeedbackListResponse(
        feedbacks=feedback_items
    )
