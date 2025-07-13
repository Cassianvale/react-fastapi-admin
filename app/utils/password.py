import re
import secrets
import string
from typing import Dict, List, Union, Tuple, Optional

import bcrypt

from app.settings.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    :param plain_password: 明文密码
    :param hashed_password: 哈希后的密码
    :return: 验证结果
    """
    try:
        # 将字符串转换为字节
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值
    :param password: 明文密码
    :return: 哈希后的密码
    """
    # 生成盐值并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def generate_password(length: Optional[int] = None) -> str:
    """
    生成随机密码
    :param length: 密码长度
    :return: 随机密码
    """
    min_length = settings.PASSWORD_MIN_LENGTH
    actual_length = length if length and length >= min_length else min_length

    # 根据配置决定生成密码的字符集
    characters = string.ascii_lowercase  # 基础字符集（小写字母）

    # 根据配置添加字符类型
    if settings.PASSWORD_REQUIRE_UPPERCASE:
        characters += string.ascii_uppercase
    if settings.PASSWORD_REQUIRE_DIGITS:
        characters += string.digits
    if settings.PASSWORD_REQUIRE_SPECIAL:
        characters += '!@#$%^&*(),.?":{}|<>'

    # 确保密码包含必需的字符类型
    password_chars = []

    # 如果需要特定字符类型，先添加至少一个
    if settings.PASSWORD_REQUIRE_LOWERCASE:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if settings.PASSWORD_REQUIRE_UPPERCASE:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if settings.PASSWORD_REQUIRE_DIGITS:
        password_chars.append(secrets.choice(string.digits))
    if settings.PASSWORD_REQUIRE_SPECIAL:
        password_chars.append(secrets.choice('!@#$%^&*(),.?":{}|<>'))

    # 用随机字符填充剩余长度
    remaining_length = actual_length - len(password_chars)
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(characters))

    # 打乱字符顺序
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    验证密码强度
    :param password: 要验证的密码
    :return: (是否通过验证, 失败原因)
    """
    # 检查长度
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"密码长度不能少于{settings.PASSWORD_MIN_LENGTH}个字符"

    # 检查大写字母
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"

    # 检查小写字母
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"

    # 检查数字
    if settings.PASSWORD_REQUIRE_DIGITS and not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"

    # 检查特殊字符
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"

    return True, ""


def get_password_strength_score(password: str) -> Dict[str, Union[int, List[str]]]:
    """
    获取密码强度评分和建议
    :param password: 密码
    :return: 强度评分（0-100）和改进建议
    """
    score = 0
    suggestions = []

    # 基础长度得分（最高40分）
    length_score = min(40, len(password) * 4)
    score += length_score

    # 如果长度不足，添加建议
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        suggestions.append(f"密码长度至少应为{settings.PASSWORD_MIN_LENGTH}个字符")

    # 字符类型多样性得分（每种类型15分，最高60分）
    if re.search(r"[a-z]", password):
        score += 15
    else:
        suggestions.append("添加小写字母可以提高密码强度")

    if re.search(r"[A-Z]", password):
        score += 15
    else:
        suggestions.append("添加大写字母可以提高密码强度")

    if re.search(r"\d", password):
        score += 15
    else:
        suggestions.append("添加数字可以提高密码强度")

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 15
    else:
        suggestions.append("添加特殊字符可以提高密码强度")

    # 返回评分和建议
    return {"score": score, "suggestions": suggestions}
