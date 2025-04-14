from typing import Optional, Dict, Set
import time
from datetime import datetime

import jwt
from fastapi import Depends, Header, HTTPException, Request, Query
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings


class AuthControl:
    # 用于存储已吊销的token（简单实现，生产环境建议使用Redis）
    _token_blacklist: Set[str] = set()
    
    # 用于存储用户请求频率限制
    _rate_limit_data: Dict[str, Dict[str, int]] = {}
    
    # 从配置文件加载IP白名单
    _ip_whitelist: Set[str] = set(settings.IP_WHITELIST)
    
    @classmethod
    async def initialize(cls):
        """初始化身份验证控制器"""
        # 加载白名单
        cls._ip_whitelist = set(settings.IP_WHITELIST)
        # 清空过期数据
        cls._clear_expired_data()
    
    @classmethod
    def _clear_expired_data(cls):
        """清理过期的频率限制数据"""
        current_time = int(time.time())
        expired_keys = []
        
        for key, data in cls._rate_limit_data.items():
            if current_time - data["timestamp"] > settings.RATE_LIMIT_WINDOW_SECONDS * 2:
                expired_keys.append(key)
                
        for key in expired_keys:
            cls._rate_limit_data.pop(key, None)
    
    @classmethod
    def add_to_blacklist(cls, token: str) -> None:
        """将token添加到黑名单"""
        cls._token_blacklist.add(token)
    
    @classmethod
    def is_in_blacklist(cls, token: str) -> bool:
        """检查token是否在黑名单中"""
        return token in cls._token_blacklist
    
    @classmethod
    async def logout(cls, token: str, user_id: int = None) -> None:
        """
        用户注销
        :param token: 要吊销的token
        :param user_id: 用户ID（可选）
        """
        # 将token加入黑名单
        cls.add_to_blacklist(token)
        
        # 清理该用户的请求频率限制数据
        if user_id:
            expired_keys = []
            for key in cls._rate_limit_data:
                if key.endswith(f":{user_id}"):
                    expired_keys.append(key)
                    
            for key in expired_keys:
                cls._rate_limit_data.pop(key, None)
    
    @classmethod
    def check_rate_limit(cls, client_ip: str, user_id: int = 0) -> bool:
        """
        检查请求频率限制
        :param client_ip: 客户端IP
        :param user_id: 用户ID，为0表示未认证用户
        :return: True表示通过检查，False表示超过限制
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True
            
        current_time = int(time.time())
        key = f"{client_ip}:{user_id}" if user_id else client_ip
        max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        time_window = settings.RATE_LIMIT_WINDOW_SECONDS
        
        # 初始化或更新计数器
        if key not in cls._rate_limit_data:
            cls._rate_limit_data[key] = {"count": 1, "timestamp": current_time}
            return True
        
        # 检查是否在同一时间窗口内
        data = cls._rate_limit_data[key]
        if current_time - data["timestamp"] > time_window:
            # 重置计数器
            cls._rate_limit_data[key] = {"count": 1, "timestamp": current_time}
            return True
        
        # 增加计数并检查是否超过限制
        data["count"] += 1
        if data["count"] > max_requests:
            return False
        
        return True
    
    @classmethod
    def check_ip_whitelist(cls, client_ip: str) -> bool:
        """检查IP是否在白名单中，如果白名单为空则不检查"""
        if not cls._ip_whitelist:
            return True
        return client_ip in cls._ip_whitelist
    
    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证"), request: Request = None) -> Optional["User"]:
        try:
            # 获取客户端IP
            client_ip = request.client.host if request and request.client else "0.0.0.0"
            
            # 检查IP白名单
            if not cls.check_ip_whitelist(client_ip):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, 
                    detail="IP地址未授权访问"
                )
            
            # 检查请求频率
            if not cls.check_rate_limit(client_ip):
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS, 
                    detail="请求过于频繁，请稍后再试"
                )
            
            # 检查token是否在黑名单中
            if cls.is_in_blacklist(token):
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, 
                    detail="Token已被吊销"
                )
            
            # 开发者模式token处理
            if settings.DEBUG and token == "dev":
                user = await User.filter().first()
                if not user:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="无法找到开发用户"
                    )
                user_id = user.id
            else:
                # 正常JWT token解析
                try:
                    decode_options = {
                        "verify_signature": True, 
                        "verify_exp": True, 
                        "verify_aud": bool(settings.JWT_AUDIENCE),  # 只有设置了受众才验证
                        "verify_iss": bool(settings.JWT_ISSUER),    # 只有设置了签发者才验证
                    }
                    
                    decode_data = jwt.decode(
                        token, 
                        settings.SECRET_KEY, 
                        algorithms=[settings.JWT_ALGORITHM],
                        audience=settings.JWT_AUDIENCE if settings.JWT_AUDIENCE else None,
                        issuer=settings.JWT_ISSUER if settings.JWT_ISSUER else None,
                        options=decode_options
                    )
                    
                    # 获取必要的用户信息
                    user_id = decode_data.get("user_id")
                    if not user_id:
                        raise HTTPException(
                            status_code=HTTP_401_UNAUTHORIZED, 
                            detail="Token中缺少用户标识"
                        )
                        
                except jwt.InvalidTokenError:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="无效的Token"
                    )
                except jwt.ExpiredSignatureError:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="登录已过期"
                    )
                except jwt.InvalidAlgorithmError:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="无效的签名算法"
                    )
                except jwt.InvalidAudienceError:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="无效的Token受众"
                    )
                except jwt.InvalidIssuerError:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED, 
                        detail="无效的Token签发者"
                    )
                        
            # 验证用户是否存在
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, 
                    detail="用户不存在或已被删除"
                )
                
            # 检查用户状态
            if not user.is_active:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, 
                    detail="用户已被禁用"
                )
                
            # 记录用户ID到上下文
            CTX_USER_ID.set(int(user_id))
            
            # 更新用户请求频率限制数据
            cls.check_rate_limit(client_ip, user_id)
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, 
                detail=f"认证失败: {repr(e)}"
            )


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles: list[Role] = await current_user.roles
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        apis = [await role.apis for role in roles]
        permission_apis = list(set((api.method, api.path) for api in sum(apis, [])))
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")


async def get_page_params(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """
    页码参数依赖，用于分页查询
    """
    return {"page": page, "page_size": page_size}


DependAuth = Depends(AuthControl.is_authed)
DependPermisson = Depends(PermissionControl.has_permission)
