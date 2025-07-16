from fastapi import APIRouter

from .upload import router

upload_router = APIRouter()
upload_router.include_router(router, tags=["文件上传"])

__all__ = ["upload_router"]
