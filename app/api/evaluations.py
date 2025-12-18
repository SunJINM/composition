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
    ScoreResponse,
    AIScoreRequest,
    AIScoreWithAnalysisRequest
)
from openai import OpenAI
from app.services.ai_service import ai_service
from app.utils import logger, convert_score_to_system
from app.config import settings

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



@router.post("/ai-analyze")
async def ai_analyze_essay(
    request: AIScoreRequest,
    db: Session = Depends(get_db)
):
    """使用AI对作文进行分析(第一步)"""
    try:
        # 统计作文字数（去除空白字符）
        word_count = len(request.essay_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', ''))

        # 创建OpenAI客户端
        client = OpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )

        # 构建完整用户提示词
        user_prompt = request.prompt.format(
            essay_title=request.essay_title or "无题目",
            essay_requirement=request.essay_requirement or "无特定要求",
            essay_content=request.essay_content,
            word_count=word_count
        )

        # 系统提示词
        system_prompt = """你是一位资深的语文教师和作文分析专家，拥有20年的教学经验。

你的职责：
1. 对作文进行全面、客观、细致的分析
2. 准确识别错别字和语病
3. 发现作文的优点和亮点
4. 提出具体可行的改进建议

分析原则：
- 客观公正：基于事实进行分析
- 具体详细：标注位置，给出实例
- 建设性：提供可操作的改进建议
- 鼓励为主：既指出问题也肯定优点

输出规范：
- 必须输出纯JSON格式，不要有任何额外文字
- 不要使用markdown代码块标记
- 严格按照指定的JSON结构输出"""

        # 调用AI接口
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,  # 适度随机性，保证分析的多样性
            max_tokens=4000    # 分析需要更多tokens
        )

        # 提取回复内容
        ai_response = response.choices[0].message.content.strip()

        # 尝试解析JSON
        # 移除可能的markdown代码块标记
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()

        # 解析分析结果
        analysis = json.loads(ai_response)

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
            evaluation_result=json.dumps(analysis, ensure_ascii=False),
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

        # 验证必需字段
        required_fields = ["overall_evaluation", "typos", "typo_count", "grammar_errors", "grammar_error_count", "strengths", "improvement_suggestions"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"缺少字段: {field}")

        return {
            "success": True,
            "analysis": analysis,
            "evaluation_id": evaluation.id,
            "raw_response": ai_response
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI返回格式错误: {str(e)}",
            "raw_response": ai_response if 'ai_response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI分析失败: {str(e)}"
        }


@router.post("/ai-score")
async def ai_score_essay(
    request: AIScoreWithAnalysisRequest,
    db: Session = Depends(get_db)
):
    """使用AI对作文进行评分(第二步,可选地基于分析结果)"""
    try:
        # 统计作文字数（去除空白字符）
        word_count = len(request.essay_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', ''))

        # 创建OpenAI客户端
        client = OpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )

        # 如果有分析结果,将完整分析结果添加到提示词中
        analysis_context = ""
        if request.analysis:
            analysis_context = f"""

## 作文分析结果(完整)

以下是对本篇作文的详细分析结果,请在评分时充分参考:

### 综合评价
{json.dumps(request.analysis.get("综合评价", {}), ensure_ascii=False, indent=2)}

### 错别字详细列表(共 {request.analysis.get("错别字总数", 0)} 个)
{json.dumps(request.analysis.get("错别字", []), ensure_ascii=False, indent=2)}

### 语病详细列表(共 {request.analysis.get("语病总数", 0)} 处)
{json.dumps(request.analysis.get("语病", []), ensure_ascii=False, indent=2)}

### 优点亮点详细列表(共 {len(request.analysis.get("优点亮点", []))} 处)
{json.dumps(request.analysis.get("优点亮点", []), ensure_ascii=False, indent=2)}

### 改进建议详细列表(共 {len(request.analysis.get("改进建议", []))} 条)
{json.dumps(request.analysis.get("改进建议", []), ensure_ascii=False, indent=2)}

**评分要求**:
- 请充分参考上述分析结果进行评分
- 特别注意错别字和语病数量对"语言表达"维度的影响
- 优点亮点应提升相应维度的分数
- 改进建议指出的问题应在相应维度扣分
"""

        # 构建完整用户提示词
        user_prompt = request.prompt.format(
            essay_title=request.essay_title or "无题目",
            essay_requirement=request.essay_requirement or "无特定要求",
            essay_content=request.essay_content,
            word_count=word_count
        ) + analysis_context

        # 优化的系统提示词
        system_prompt = """你是一位资深的语文教师和作文评分专家，拥有20年的教学经验。

你的职责：
1. 严格按照评分标准对作文进行客观、公正的评价
2. 参考各个分数段的具体标准，给出精准的分数
3. 评分要有区分度，避免集中在某个分数段
4. 既要看到优点，也要发现不足

评分原则：
- 客观性：基于文本内容，不受主观情感影响
- 准确性：严格对照评分标准的每个层次
- 一致性：保持评分尺度的统一和稳定
- 公正性：对所有作文一视同仁

输出规范：
- 必须输出纯JSON格式，不要有任何额外文字
- 不要使用markdown代码块标记
- 分数必须是整数，且在规定范围内"""

        # 调用AI接口
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 降低随机性，提高一致性
        )
        # 提取回复内容
        ai_response = response.choices[0].message.content.strip()

        # 尝试解析JSON
        # 移除可能的markdown代码块标记
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()

        # 解析分数
        scores = json.loads(ai_response)

        # 验证分数格式
        required_dimensions = ["theme_and_intent", "language_expression", "structure", "content_selection", "emotion_and_content"]
        max_scores = {
            "theme_and_intent": 20,       # 中心立意
            "language_expression": 25,    # 语言表达
            "structure": 15,              # 篇章结构
            "content_selection": 15,      # 文章选材
            "emotion_and_content": 25     # 内容情感
        }

        dimensions = {}
        dimensions_sum = 0
    
        def get_cn_dim_name(en_dim):
            dim_mapping = {
                "theme_and_intent": "中心立意",
                "language_expression": "语言表达",
                "structure": "篇章结构",
                "content_selection": "文章选材",
                "emotion_and_content": "内容情感"
            }
            return dim_mapping.get(en_dim, en_dim)

        for dim in required_dimensions:
            if dim not in scores:
                raise ValueError(f"缺少维度: {dim}（{get_cn_dim_name(dim)}）")  # 可选：加中文提示更友好
            score = float(scores[dim])
            if score < 0 or score > max_scores[dim]:
                raise ValueError(f"维度 {dim}（{get_cn_dim_name(dim)}）分数超出范围: {score}（有效值0-{max_scores[dim]}）")
            dimensions[dim] = {
                "score": score,
                "max_score": max_scores[dim]
            }
            dimensions_sum += score

        # 根据原始评分数据判断分制,计算总分
        use_10_point_scale = False
        if request.original_score_data and "total_score" in request.original_score_data:
            if request.original_score_data["total_score"] <= 10:
                use_10_point_scale = True

        if use_10_point_scale:
            total_score = int((dimensions_sum / 100) * 10)
        else:
            total_score = int((dimensions_sum / 100) * 40)
        score_data = {
            "total_score": total_score,
            "dimensions": dimensions
        }

        db.query(Score).filter_by(
            evaluation_id=request.evaluation_id,
            is_default=1
        ).update({"is_default": 0})


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

        logger.info(f"作文评分完成: evaluation_id={request.evaluation_id}, score_id={score.id}")

        return {
            "success": True,
            "score_data": score_data,
            "raw_response": ai_response
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI返回格式错误: {str(e)}",
            "raw_response": ai_response
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI评分失败: {str(e)}"
        }