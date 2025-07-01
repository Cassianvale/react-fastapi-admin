import jwt
from datetime import datetime, timedelta, timezone

from app.schemas.login import JWTPayload
from app.settings.config import settings


def create_access_token(*, data: JWTPayload):
    """
    创建访问令牌
    :param data: JWT有效载荷数据
    :return: 编码后的JWT
    """
    payload = data.model_dump().copy()
    
    # 添加JWT标准声明
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER
    
    # 确保包含exp字段（过期时间）
    if "exp" not in payload:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload["exp"] = expire
        
    # 添加签发时间
    payload["iat"] = datetime.now(timezone.utc)
    
    # 使用配置的算法和密钥签名并编码JWT
    encoded_jwt = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(*, user_id: int):
    """
    创建刷新令牌
    :param user_id: 用户ID
    :return: 编码后的刷新令牌
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": "refresh",
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    # 添加JWT标准声明
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER
    
    # 使用配置的算法和密钥签名并编码JWT
    encoded_jwt = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt
