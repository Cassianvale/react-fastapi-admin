#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JSON编码器工具模块
提供自定义JSON编码器，支持复杂数据类型的序列化
"""

import json
import decimal
from datetime import datetime
from typing import Any

from app.settings.config import settings


class ModelJSONEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器，支持 Tortoise ORM 模型和复杂数据类型序列化

    支持的数据类型：
    - datetime: 转换为格式化字符串
    - Decimal: 转换为字符串
    - BaseModel: 提示使用 to_json() 方法
    """

    def default(self, obj: Any) -> Any:
        """
        重写默认序列化方法

        Args:
            obj: 要序列化的对象

        Returns:
            Any: 序列化后的值

        Raises:
            TypeError: 当对象无法序列化时
        """
        # 避免循环导入，在运行时导入
        from app.models.base import BaseModel

        if isinstance(obj, BaseModel):
            # 对于Tortoise ORM模型，建议使用异步的to_json()方法
            raise TypeError(f"对象 {obj} 不支持直接JSON序列化，请使用 await obj.to_json() 方法")
        elif isinstance(obj, datetime):
            # 日期时间格式化
            return obj.strftime(settings.DATETIME_FORMAT)
        elif isinstance(obj, decimal.Decimal):
            # Decimal类型转换为字符串，保持精度
            return str(obj)

        # 调用父类默认处理
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全的JSON序列化函数

    Args:
        obj: 要序列化的对象
        **kwargs: json.dumps的额外参数

    Returns:
        str: JSON字符串
    """
    kwargs.setdefault("cls", ModelJSONEncoder)
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("default", str)

    return json.dumps(obj, **kwargs)


def safe_json_loads(s: str, **kwargs) -> Any:
    """
    安全的JSON反序列化函数

    Args:
        s: JSON字符串
        **kwargs: json.loads的额外参数

    Returns:
        Any: 反序列化后的对象
    """
    return json.loads(s, **kwargs)
