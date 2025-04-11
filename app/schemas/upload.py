from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """文件信息"""
    url: str = Field(..., description="文件URL")
    name: str = Field(..., description="文件原始名称")
    size: int = Field(..., description="文件大小(字节)")


class OSSFileInfo(BaseModel):
    """OSS文件信息"""
    url: str = Field(..., description="文件URL")
    name: str = Field(..., description="文件名称")
    key: str = Field(..., description="文件在OSS中的键值")
    size: int = Field(..., description="文件大小(字节)")
    last_modified: str = Field(..., description="最后修改时间")


class FileUploadResp(BaseModel):
    """文件上传响应"""
    data: FileInfo = Field(..., description="文件信息")


class BatchFileUploadResp(BaseModel):
    """批量文件上传响应"""
    data: List[FileInfo] = Field(..., description="文件信息列表")


class FileListResp(BaseModel):
    """文件列表响应"""
    data: List[OSSFileInfo] = Field(..., description="OSS文件信息列表")


class FileDeleteResp(BaseModel):
    """文件删除响应"""
    data: bool = Field(..., description="删除结果") 