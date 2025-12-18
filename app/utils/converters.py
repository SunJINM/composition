"""
转换工具函数
包含分制转换等
"""
from typing import Dict, Any


def convert_score_to_system(dimensions_sum: float, score_system: int) -> float:
    """
    将百分制的维度总分转换为对应分制

    Args:
        dimensions_sum: 各维度分数之和(百分制)
        score_system: 目标分制(10或40)

    Returns:
        转换后的总分
    """
    if score_system == 10:
        return round((dimensions_sum / 100) * 10, 1)
    else:
        return round((dimensions_sum / 100) * 40, 1)


def get_score_system_from_original(original_score_data: Dict[str, Any]) -> int:
    """
    从原始评分数据判断分制

    Args:
        original_score_data: 原始评分数据字典

    Returns:
        分制(10或40)
    """
    if original_score_data and 'total_score' in original_score_data:
        total_score = original_score_data['total_score']
        return 10 if total_score and total_score <= 10 else 40
    return 40  # 默认40分制
