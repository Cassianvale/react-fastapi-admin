import json
import re
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.dependency import AuthControl
from app.models.admin import AuditLog, User

from .bgtask import BgTasks


class SimpleBaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        response = await self.before_request(request) or self.app
        await response(request.scope, request.receive, send)
        await self.after_request(request)

    async def before_request(self, request: Request):
        return self.app

    async def after_request(self, request: Request):
        return None


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    async def before_request(self, request):
        await BgTasks.init_bg_tasks_obj()

    async def after_request(self, request):
        await BgTasks.execute_tasks()


class HttpAuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, methods: list[str], exclude_paths: list[str]):
        super().__init__(app)
        self.methods = methods
        self.exclude_paths = exclude_paths
        self.audit_log_paths = ["/api/v1/auditlog/list"]
        self.max_body_size = 1024 * 1024  # 1MB 响应体大小限制

    async def get_request_args(self, request: Request) -> dict:
        args = {}

        try:
            # 获取查询参数
            for key, value in request.query_params.items():
                args[key] = value

            # 获取请求体
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # 尝试读取JSON请求体，最大尝试读取10KB以防止大型请求体导致问题
                    body_bytes = await request.body()
                    if body_bytes:
                        # 确保内容是有效的JSON
                        content_type = request.headers.get("content-type", "")
                        if "application/json" in content_type.lower():
                            try:
                                # 使用更安全的解析方式
                                body_str = body_bytes.decode("utf-8", errors="replace")
                                body = json.loads(body_str)
                                args.update(body)
                            except json.JSONDecodeError:
                                # JSON解析失败，尝试记录原始内容（限制大小）
                                args["raw_body"] = body_bytes.decode("utf-8", errors="replace")[:1000]
                        else:
                            # 不是JSON请求，尝试表单数据
                            try:
                                body = await request.form()
                                args.update({k: v for k, v in body.items()})
                            except Exception:
                                # 如果不是表单，存储原始内容（限制大小）
                                args["raw_body"] = body_bytes.decode("utf-8", errors="replace")[:1000]
                except Exception as e:
                    # 捕获所有异常，确保中间件不会崩溃
                    args["parse_error"] = str(e)[:200]
        except Exception as e:
            # 防止任何异常导致中间件崩溃
            args["middleware_error"] = str(e)[:200]
            
        return args

    async def get_response_body(self, request: Request, response: Response) -> Any:
        # 检查Content-Length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            return {"code": 0, "msg": "Response too large to log", "data": None}

        try:
            if hasattr(response, "body"):
                body = response.body
            else:
                body_chunks = []
                async for chunk in response.body_iterator:
                    if not isinstance(chunk, bytes):
                        chunk = chunk.encode(response.charset)
                    body_chunks.append(chunk)

                response.body_iterator = self._async_iter(body_chunks)
                body = b"".join(body_chunks)

            # 检查是否是审计日志路径，进行特殊处理
            if any(request.url.path.startswith(path) for path in self.audit_log_paths):
                try:
                    data = self.lenient_json(body)
                    # 只保留基本信息，去除详细的响应内容
                    if isinstance(data, dict):
                        data.pop("response_body", None)
                        if "data" in data and isinstance(data["data"], list):
                            for item in data["data"]:
                                item.pop("response_body", None)
                    return data
                except Exception:
                    return {"code": 0, "msg": "Failed to parse audit log response", "data": None}

            return self.lenient_json(body)
        except Exception as e:
            # 捕获所有异常，确保中间件不会崩溃
            return {"code": 0, "msg": f"Response parsing error: {str(e)[:200]}", "data": None}

    def lenient_json(self, v: Any) -> Any:
        if v is None:
            return {}
            
        if isinstance(v, bytes):
            try:
                v = v.decode("utf-8", errors="replace")
            except Exception:
                return {"raw_content": "Binary content"}
                
        if isinstance(v, str):
            if not v or v.isspace():
                return {}
                
            try:
                return json.loads(v)
            except (ValueError, TypeError, json.JSONDecodeError):
                # 返回截断的原始内容，避免存储过大的非JSON数据
                return {"raw_content": str(v)[:100] + ("..." if len(str(v)) > 100 else "")}
                
        return v

    async def _async_iter(self, items: list[bytes]) -> AsyncGenerator[bytes, None]:
        for item in items:
            yield item

    async def get_request_log(self, request: Request, response: Response) -> dict:
        """
        根据request和response对象获取对应的日志记录数据
        """
        data: dict = {"path": request.url.path, "status": response.status_code, "method": request.method}
        # 路由信息
        app: FastAPI = request.app
        for route in app.routes:
            if (
                isinstance(route, APIRoute)
                and route.path_regex.match(request.url.path)
                and request.method in route.methods
            ):
                data["module"] = ",".join(route.tags)
                data["summary"] = route.summary
        # 获取用户信息
        try:
            token = request.headers.get("token")
            user_obj = None
            if token:
                user_obj: User = await AuthControl.is_authed(token)
            data["user_id"] = user_obj.id if user_obj else 0
            data["username"] = user_obj.username if user_obj else ""
        except Exception:
            data["user_id"] = 0
            data["username"] = ""
        return data

    async def before_request(self, request: Request):
        request_args = await self.get_request_args(request)
        request.state.request_args = request_args

    async def after_request(self, request: Request, response: Response, process_time: int):
        if request.method in self.methods:
            for path in self.exclude_paths:
                if re.search(path, request.url.path, re.I) is not None:
                    return
            data: dict = await self.get_request_log(request=request, response=response)
            data["response_time"] = process_time

            # 确保 request_args 和 response_body 是有效的 JSON 值
            request_args = getattr(request.state, "request_args", {})
            if request_args == "":
                request_args = {}
            data["request_args"] = request_args
            
            response_body = await self.get_response_body(request, response)
            if response_body == "":
                response_body = {}
            data["response_body"] = response_body
            
            await AuditLog.create(**data)

        return response

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time: datetime = datetime.now()
        await self.before_request(request)
        response = await call_next(request)
        end_time: datetime = datetime.now()
        process_time = int((end_time.timestamp() - start_time.timestamp()) * 1000)
        await self.after_request(request, response, process_time)
        return response
