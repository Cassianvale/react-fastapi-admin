import os
import sys
from granian import Granian
from app.settings.reload_config import RELOAD_CONFIG


def run_server():
    """启动服务器"""
    Granian(
        "app:app",  # app\__init__.py中创建的app实例
        interface="asgi",
        address="0.0.0.0",
        port=9999,
        reload=True,
        # 使用配置模块中的热重载设置
        **RELOAD_CONFIG,
    ).serve()


if __name__ == "__main__":
    run_server()
