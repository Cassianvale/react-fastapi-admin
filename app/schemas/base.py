from typing import Any, Optional, Dict, List, Union
import json
from fastapi.responses import JSONResponse
from app.utils.json_encoder import safe_json_dumps


class BaseResponse(JSONResponse):
    """
    统一的基础响应类
    """

    def __init__(self, code: int = 200, msg: str = "成功", data: Optional[Any] = None, **kwargs):
        content = {"code": code, "msg": msg, "data": data}
        # 添加额外的字段
        content.update(kwargs)

        # 使用安全的JSON序列化工具处理复杂对象，然后解析回Python对象
        json_str = safe_json_dumps(content)
        json_compatible_content = json.loads(json_str)

        super().__init__(content=json_compatible_content, status_code=code)


class ApiResponse:
    """
    统一的API响应生成器
    """

    @staticmethod
    def success(data: Optional[Any] = None, msg: str = "成功", code: int = 200, **kwargs) -> BaseResponse:
        """成功响应"""
        return BaseResponse(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def fail(msg: str = "请求失败", code: int = 400, data: Optional[Any] = None, **kwargs) -> BaseResponse:
        """失败响应"""
        return BaseResponse(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def error(msg: str = "服务器内部错误", code: int = 500, data: Optional[Any] = None, **kwargs) -> BaseResponse:
        """错误响应"""
        return BaseResponse(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def paginate(
        data: Optional[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        msg: str = "成功",
        code: int = 200,
        **kwargs,
    ) -> BaseResponse:
        """分页响应"""
        return BaseResponse(code=code, msg=msg, data=data, total=total, page=page, page_size=page_size, **kwargs)

    @staticmethod
    def unauthorized(msg: str = "未授权访问", data: Optional[Any] = None) -> BaseResponse:
        """401 未授权响应"""
        return BaseResponse(code=401, msg=msg, data=data)

    @staticmethod
    def forbidden(msg: str = "禁止访问", data: Optional[Any] = None) -> BaseResponse:
        """403 禁止访问响应"""
        return BaseResponse(code=403, msg=msg, data=data)

    @staticmethod
    def not_found(msg: str = "资源不存在", data: Optional[Any] = None) -> BaseResponse:
        """404 资源不存在响应"""
        return BaseResponse(code=404, msg=msg, data=data)

    @staticmethod
    def validation_error(msg: str = "参数验证失败", data: Optional[Any] = None) -> BaseResponse:
        """422 参数验证失败响应"""
        return BaseResponse(code=422, msg=msg, data=data)


Success = ApiResponse.success
Fail = ApiResponse.fail
Error = ApiResponse.error
Paginate = ApiResponse.paginate
SuccessExtra = ApiResponse.paginate
