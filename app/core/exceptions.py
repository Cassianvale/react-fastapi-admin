from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.base import ApiResponse
from app.utils.log_control import logger
import traceback


class SettingNotFound(Exception):
    """配置文件未找到异常"""

    pass


class CustomHTTPException(HTTPException):
    """自定义HTTP异常类，支持额外的错误信息"""

    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.data = data


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器，统一返回格式
    """
    status_code = exc.status_code
    detail = exc.detail
    data = getattr(exc, "data", None)

    # 记录异常信息
    logger.warning(f"HTTP异常 - 状态码: {status_code}, 详情: {detail}, 路径: {request.url.path}")

    # 根据状态码返回相应的响应
    if status_code == 401:
        return ApiResponse.unauthorized(msg=detail, data=data)
    elif status_code == 403:
        return ApiResponse.forbidden(msg=detail, data=data)
    elif status_code == 404:
        return ApiResponse.not_found(msg=detail, data=data)
    elif status_code == 422:
        return ApiResponse.validation_error(msg=detail, data=data)
    elif status_code == 429:
        return ApiResponse.fail(msg=detail, code=429, data=data)
    elif 400 <= status_code < 500:
        return ApiResponse.fail(msg=detail, code=status_code, data=data)
    else:
        return ApiResponse.error(msg=detail, code=status_code, data=data)


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Starlette HTTP异常处理器
    """
    return await http_exception_handler(request, HTTPException(status_code=exc.status_code, detail=exc.detail))


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器，处理所有未捕获的异常
    """
    # 记录完整的异常信息
    logger.error(f"未捕获的异常: {type(exc).__name__}: {str(exc)}")
    logger.error(f"请求路径: {request.url.path}")
    logger.error(f"异常堆栈:\n{traceback.format_exc()}")

    # 返回统一的错误响应
    return ApiResponse.error(msg="服务器内部错误", data=None)


# 异常处理器映射
exception_handlers = {
    HTTPException: http_exception_handler,
    StarletteHTTPException: starlette_exception_handler,
    Exception: global_exception_handler,
}


# 认证相关异常
class AuthenticationError(CustomHTTPException):
    """认证错误"""

    def __init__(self, detail: str = "认证失败", data: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, detail=detail, data=data)


class AuthorizationError(CustomHTTPException):
    """授权错误"""

    def __init__(self, detail: str = "权限不足", data: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, detail=detail, data=data)


class RateLimitError(CustomHTTPException):
    """频率限制错误"""

    def __init__(self, detail: str = "请求过于频繁", data: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=429, detail=detail, data=data)


class ValidationError(CustomHTTPException):
    """验证错误"""

    def __init__(self, detail: str = "数据验证失败", data: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=422, detail=detail, data=data)
