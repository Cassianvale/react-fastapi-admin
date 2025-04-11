from fastapi import APIRouter
from app.api.v1.upload.upload import router as upload_router

router = APIRouter(prefix="/upload", tags=["文件上传"])

router.include_router(upload_router) 