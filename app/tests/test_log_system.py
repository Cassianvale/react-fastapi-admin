#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志系统测试
验证重构后的日志系统是否正常工作
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["DEBUG"] = "true"
os.environ["LOG_RETENTION_DAYS"] = "3"
os.environ["LOG_ROTATION"] = "1 day"
os.environ["LOG_MAX_FILE_SIZE"] = "5 MB"
os.environ["LOG_ENABLE_ACCESS_LOG"] = "true"


def test_basic_logging():
    """测试基本日志功能"""
    print("🧪 测试基本日志功能...")

    try:
        from app.utils.log_control import logger, init_logging

        # 初始化日志系统
        init_logging()

        # 测试不同级别的日志
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        logger.debug("这是一条调试日志")

        print("✅ 基本日志功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 基本日志功能测试失败: {e}")
        return False


def test_convenience_functions():
    """测试便捷函数"""
    print("🧪 测试便捷函数...")

    try:
        from app.utils.log_control import log_info, log_warning, log_error, log_debug, log_exception, log_critical

        log_info("测试info函数")
        log_warning("测试warning函数")
        log_error("测试error函数")
        log_debug("测试debug函数")
        log_critical("测试critical函数")

        print("✅ 便捷函数测试通过")
        return True

    except Exception as e:
        print(f"❌ 便捷函数测试失败: {e}")
        return False


def test_named_logger():
    """测试具名日志器"""
    print("🧪 测试具名日志器...")

    try:
        from app.utils.log_control import get_logger

        # 获取具名日志器
        user_logger = get_logger("user_service")
        api_logger = get_logger("api_handler")

        user_logger.info("用户服务日志")
        api_logger.error("API处理日志")

        print("✅ 具名日志器测试通过")
        return True

    except Exception as e:
        print(f"❌ 具名日志器测试失败: {e}")
        return False


def test_log_manager():
    """测试日志管理器"""
    print("🧪 测试日志管理器...")

    try:
        from app.utils.log_control import log_manager

        # 获取配置
        config = log_manager.get_log_config()
        print(f"📋 当前日志配置: {config}")

        print("✅ 日志管理器测试通过")
        return True

    except Exception as e:
        print(f"❌ 日志管理器测试失败: {e}")
        return False


def test_exception_logging():
    """测试异常日志"""
    print("🧪 测试异常日志...")

    try:
        from app.utils.log_control import logger

        # 模拟异常
        try:
            result = 1 / 0
        except ZeroDivisionError:
            logger.exception("测试异常日志记录")

        print("✅ 异常日志测试通过")
        return True

    except Exception as e:
        print(f"❌ 异常日志测试失败: {e}")
        return False


def test_structured_logging():
    """测试结构化日志"""
    print("🧪 测试结构化日志...")

    try:
        from app.utils.log_control import logger

        # 结构化日志记录
        logger.info("用户登录", user_id=123, username="admin", ip_address="192.168.1.100", action="login")

        # 绑定上下文信息
        request_logger = logger.bind(request_id="req_123", user_id=456)
        request_logger.info("处理用户请求")

        print("✅ 结构化日志测试通过")
        return True

    except Exception as e:
        print(f"❌ 结构化日志测试失败: {e}")
        return False


def test_access_log_middleware():
    """测试访问日志中间件"""
    print("🧪 测试访问日志中间件...")

    try:
        from app.utils.log_control import AccessLogMiddleware

        # 创建中间件实例
        middleware = AccessLogMiddleware(app=None, skip_paths=["/health", "/metrics"])  # 测试中不需要实际的app

        # 测试路径判断
        should_skip = middleware.should_skip_logging("/health")
        assert should_skip == True, "应该跳过/health路径"

        should_not_skip = middleware.should_skip_logging("/api/users")
        assert should_not_skip == False, "不应该跳过/api/users路径"

        print("✅ 访问日志中间件测试通过")
        return True

    except Exception as e:
        print(f"❌ 访问日志中间件测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试重构后的日志系统...")
    print("=" * 60)

    tests = [
        test_basic_logging,
        test_convenience_functions,
        test_named_logger,
        test_log_manager,
        test_exception_logging,
        test_structured_logging,
        test_access_log_middleware,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 出现异常: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 测试结果: 通过 {passed} 个, 失败 {failed} 个")

    if failed == 0:
        print("🎉 所有测试通过! 日志系统重构成功!")
        return 0
    else:
        print("⚠️  部分测试失败，请检查日志系统配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
