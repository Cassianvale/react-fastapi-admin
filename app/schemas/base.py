from typing import Any, Optional
import json
from decimal import Decimal

from fastapi.responses import JSONResponse


# 自定义JSON编码器，处理Decimal类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # 将Decimal转换为字符串
        return super().default(obj)


class Success(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = "OK",
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        
        # 使用自定义JSON编码器处理content
        json_content = json.loads(json.dumps(content, cls=CustomJSONEncoder))
        super().__init__(content=json_content, status_code=code)


class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        
        # 使用自定义JSON编码器处理content
        json_content = json.loads(json.dumps(content, cls=CustomJSONEncoder))
        super().__init__(content=json_content, status_code=code)


class SuccessExtra(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ):
        content = {
            "code": code,
            "msg": msg,
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        content.update(kwargs)
        
        # 使用自定义JSON编码器处理content
        json_content = json.loads(json.dumps(content, cls=CustomJSONEncoder))
        super().__init__(content=json_content, status_code=code)
