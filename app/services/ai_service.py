"""
AI服务层
调用OpenAI API进行作文评价和评分
"""
from typing import Dict, Any
from openai import OpenAI
from app.config import settings
from app.utils.logger import logger
import json


class AIService:
    """AI服务类"""

    def __init__(self):
        """初始化OpenAI客户端"""
        self.client = OpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )
        self.model = settings.OPENAI_MODEL

    def analyze_essay(
        self,
        essay_content: str,
        essay_title: str,
        essay_requirement: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        作文评价

        Args:
            essay_content: 作文内容
            essay_title: 作文题目
            essay_requirement: 作文要求
            prompt: 评价提示词

        Returns:
            评价结果字典
        """
        try:
            # 构建完整提示词
            full_prompt = f"""{prompt}

作文题目: {essay_title}

作文要求: {essay_requirement}

学生作文:
{essay_content}
"""

            logger.info(f"调用AI评价作文,长度: {len(essay_content)}")

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # 解析响应
            result = json.loads(response.choices[0].message.content)
            logger.info("AI评价完成")

            return result

        except Exception as e:
            logger.error(f"AI评价失败: {str(e)}")
            raise

    def detect_genre(
        self,
        essay_content: str,
        essay_requirement: str
    ) -> Dict[str, Any]:
        """
        文体判断

        Args:
            essay_content: 作文内容
            essay_requirement: 作文要求

        Returns:
            文体判断结果
        """
        try:
            prompt = """请分析这篇作文的文体类型和适合的年级。

请以JSON格式返回结果:
{
    "genre_code": "narrative或argumentative",
    "genre_name": "记叙文或议论文",
    "confidence": 0.0-1.0的置信度,
    "grade_level": 7或8或9,
    "reasoning": "判断理由"
}

作文要求:
{requirement}

作文内容:
{content}
"""

            full_prompt = prompt.format(
                requirement=essay_requirement,
                content=essay_content[:1000]  # 只取前1000字分析
            )

            logger.info("调用AI判断文体")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"文体判断完成: {result.get('genre_name')}, 置信度: {result.get('confidence')}")

            return result

        except Exception as e:
            logger.error(f"文体判断失败: {str(e)}")
            raise

    def score_essay(
        self,
        essay_content: str,
        essay_title: str,
        essay_requirement: str,
        evaluation_result: Dict[str, Any],
        prompt: str,
        score_system: int
    ) -> Dict[str, Any]:
        """
        作文评分

        Args:
            essay_content: 作文内容
            essay_title: 作文题目
            essay_requirement: 作文要求
            evaluation_result: 评价结果
            prompt: 评分提示词
            score_system: 分制(10或40)

        Returns:
            评分结果字典(已转换为对应分制)
        """
        try:
            # 构建完整提示词
            full_prompt = f"""{prompt}

作文题目: {essay_title}

作文要求: {essay_requirement}

评价结果:
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

学生作文:
{essay_content}

请注意: 最终评分需要按照{score_system}分制计算总分。
"""

            logger.info(f"调用AI评分,分制: {score_system}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI评分完成: {result.get('total_score')}/{score_system}")

            return result

        except Exception as e:
            logger.error(f"AI评分失败: {str(e)}")
            raise


# 创建单例
ai_service = AIService()
