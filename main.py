import os
import sys
import uvicorn
from uvicorn.config import LOGGING_CONFIG

def run_server():
    """启动服务器"""
    # 修改默认日志配置
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    
    # 启动服务器
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=9999, 
        reload=True,  # 启用热重载
        timeout_graceful_shutdown=10,  # 优雅关闭超时时间
        log_config=LOGGING_CONFIG
    )

if __name__ == "__main__":
    # 处理命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ["development", "production", "testing"]:
        # 设置环境变量，会被app/__init__.py中的load_environment()读取
        os.environ["APP_ENV"] = sys.argv[1]
        print(f"正在以 {sys.argv[1]} 环境启动服务...")
    
    run_server()
