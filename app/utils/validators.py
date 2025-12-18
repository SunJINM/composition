"""
验证工具函数
"""
import re


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式

    Args:
        phone: 手机号字符串

    Returns:
        是否有效
    """
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_score_system(score_system: int) -> bool:
    """
    验证分制是否有效

    Args:
        score_system: 分制值

    Returns:
        是否有效(10或40)
    """
    return score_system in [10, 40]
