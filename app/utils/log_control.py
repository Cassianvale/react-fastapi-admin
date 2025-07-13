#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志控制模块
基于loguru的统一日志系统，包含日志配置、访问日志中间件等功能
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.settings import settings


class LogManager:
    """日志管理器，统一管理应用的日志配置"""

    def __init__(self):
        # 是否已配置
        self._is_configured = False

    def get_log_config(self) -> dict:
        """获取日志配置"""
        config = {
            "log_dir": str(settings.logs_path),
            "log_retention_days": settings.LOG_RETENTION_DAYS,
            "log_rotation": settings.LOG_ROTATION,
            "debug_mode": settings.DEBUG,
            "max_file_size": settings.LOG_MAX_FILE_SIZE,
        }

        # 生产环境优化配置
        if settings.is_production:
            config.update(
                {
                    "log_retention_days": 30,
                    "log_rotation": "00:00",
                    "debug_mode": False,
                    "max_file_size": "50 MB",
                }
            )

        return config

    def setup_logger(self, **kwargs):
        """
        设置日志记录器

        Args:
            **kwargs: 日志配置参数
        """
        if self._is_configured:
            return logger

        config = self.get_log_config()
        config.update(kwargs)

        # 移除默认的日志处理器
        logger.remove()

        # 设置日志级别
        log_level = "DEBUG" if config["debug_mode"] else "INFO"

        # 确保日志目录存在
        log_path = Path(config["log_dir"])
        log_path.mkdir(parents=True, exist_ok=True)

        # 获取当前日期作为日志文件名的一部分
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_path / f"{today}.log"

        # 控制台输出配置
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        # 文件输出配置
        file_format = "{time:YYYY-MM-DD HH:mm:ss} | " "{level: <8} | " "{name}:{function}:{line} | " "{message}"

        # 添加控制台输出
        logger.add(
            sink=lambda msg: print(msg, end=""),
            format=console_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=config["debug_mode"],
        )

        # 添加文件日志处理器
        logger.add(
            sink=str(log_file),
            rotation=config["log_rotation"],
            retention=f"{config['log_retention_days']} days",
            format=file_format,
            level=log_level,
            encoding="utf-8",
            backtrace=True,
            diagnose=config["debug_mode"],
            enqueue=True,
            compression="zip",
        )

        # 错误日志单独记录
        error_log_file = log_path / f"error_{today}.log"
        logger.add(
            sink=str(error_log_file),
            rotation=config["log_rotation"],
            retention=f"{config['log_retention_days']} days",
            format=file_format,
            level="ERROR",
            encoding="utf-8",
            backtrace=True,
            diagnose=config["debug_mode"],
            enqueue=True,
            compression="zip",
        )

        self._is_configured = True

        # 记录配置信息
        logger.info(f"日志系统已配置 - 环境: {settings.APP_ENV}")
        logger.info(f"日志目录: {config['log_dir']}")
        logger.info(f"调试模式: {config['debug_mode']}")
        logger.info(f"日志保留天数: {config['log_retention_days']}")

        return logger


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    HTTP访问日志中间件
    记录所有HTTP请求的访问日志
    """

    def __init__(self, app, skip_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]

    def should_skip_logging(self, path: str) -> bool:
        """判断是否应该跳过日志记录"""
        return any(skip_path in path for skip_path in self.skip_paths)

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳过不需要记录的路径
        if self.should_skip_logging(request.url.path):
            return await call_next(request)

        start_time = datetime.now()

        # 安全地获取客户端IP
        client_host = "unknown"
        if request.client:
            client_host = request.client.host

        # 获取用户代理
        user_agent = request.headers.get("user-agent", "")

        try:
            response = await call_next(request)
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()

            # 记录访问日志
            log_message = (
                f"HTTP {response.status_code} | "
                f"{client_host} | "
                f"{request.method} | "
                f"{request.url} | "
                f"{process_time:.3f}s | "
                f"UA: {user_agent[:100]}"
            )

            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logger.error(log_message)
            elif response.status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            return response

        except Exception as e:
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()

            # 记录异常日志
            logger.error(
                f"HTTP ERROR | "
                f"{client_host} | "
                f"{request.method} | "
                f"{request.url} | "
                f"{process_time:.3f}s | "
                f"Exception: {str(e)}"
            )
            raise


# 创建全局日志管理器
log_manager = LogManager()


def init_logging():
    """
    初始化日志系统
    在应用启动时调用
    """
    log_manager.setup_logger()

    # 记录系统启动信息
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_TITLE} 正在启动...")
    logger.info(f"📍 环境: {settings.APP_ENV}")
    logger.info(f"🔧 调试模式: {settings.DEBUG}")
    logger.info(f"📂 项目根目录: {settings.BASE_DIR}")
    logger.info(f"📋 日志目录: {settings.logs_path}")
    logger.info("=" * 50)

    return logger


def get_logger(name: Optional[str] = None):
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    if not log_manager._is_configured:
        log_manager.setup_logger()

    if name:
        return logger.bind(name=name)
    return logger


# 便捷的日志记录函数
def log_info(message: str, **kwargs):
    """记录信息日志"""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录警告日志"""
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """记录错误日志"""
    logger.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """记录调试日志"""
    logger.debug(message, **kwargs)


def log_exception(message: str, **kwargs):
    """记录异常日志"""
    logger.exception(message, **kwargs)


def log_critical(message: str, **kwargs):
    """记录严重错误日志"""
    logger.critical(message, **kwargs)
