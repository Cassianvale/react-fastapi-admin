import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import oss2
from fastapi import HTTPException, UploadFile, status

from app.settings.config import settings


class UploadController:
    """文件上传控制器"""
    
    def get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(filename)[1] if "." in filename else ""
    
    def generate_oss_file_name(self, original_filename: str) -> str:
        """生成OSS中的文件名，基于时间和UUID"""
        ext = self.get_file_extension(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_uuid = str(uuid.uuid4()).replace("-", "")[:8]
        return f"{timestamp}_{random_uuid}{ext}"
    
    def generate_oss_path(self, file_type: str = "common") -> str:
        """
        根据文件类型和当前日期生成OSS存储路径
        
        Args:
            file_type: 文件类型，用于分类存储，如image、document等
            
        Returns:
            str: OSS存储路径
        """
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")  # 使用连续的年月日格式
        
        # 使用os.path.join正确处理路径连接，防止双斜杠问题
        # 注意：OSS使用正斜杠，Windows下os.path.join使用反斜杠，需要转换
        path = os.path.join(settings.OSS_UPLOAD_DIR, file_type, date_str)
        # 转换为OSS路径格式（使用正斜杠）
        return path.replace('\\', '/')
    
    def generate_local_path(self, file_type: str = "common") -> str:
        """
        根据文件类型和当前日期生成本地存储路径
        
        Args:
            file_type: 文件类型，用于分类存储，如image、document等
            
        Returns:
            tuple: (本地文件系统路径, URL路径)
        """
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")  # 使用连续的年月日格式
        
        # 本地文件系统路径
        fs_path = os.path.join(settings.LOCAL_STORAGE_PATH, file_type, date_str)
        # URL路径
        url_path = os.path.join(settings.LOCAL_STORAGE_URL_PREFIX, file_type, date_str).replace('\\', '/')
        
        # 确保目录存在
        os.makedirs(fs_path, exist_ok=True)
        
        return fs_path, url_path
    
    async def check_image_file(self, file: UploadFile) -> bytes:
        """
        检查图片文件是否符合要求
        
        Args:
            file: 上传的文件
            
        Returns:
            bytes: 文件内容
            
        Raises:
            HTTPException: 文件不符合要求时抛出异常
        """
        # 检查文件类型
        file_extension = self.get_file_extension(file.filename).lower()
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的图片格式，仅支持: {', '.join(allowed_extensions)}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 检查文件大小（限制为10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超出限制，最大允许10MB"
            )
            
        return file_content
    
    async def check_file(self, file: UploadFile) -> bytes:
        """
        检查普通文件是否符合要求
        
        Args:
            file: 上传的文件
            
        Returns:
            bytes: 文件内容
            
        Raises:
            HTTPException: 文件不符合要求时抛出异常
        """
        # 读取文件内容
        file_content = await file.read()
        
        # 检查文件大小（限制为10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超出限制，最大允许10MB"
            )
            
        return file_content
    
    async def upload_to_local(self, file_content: bytes, filename: str, file_type: str = "common") -> str:
        """
        上传文件到本地存储
        
        Args:
            file_content: 文件内容
            filename: 文件名
            file_type: 文件类型，如image、document等
        
        Returns:
            str: 文件的URL
        
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        try:
            # 获取本地存储路径
            fs_path, url_path = self.generate_local_path(file_type)
            
            # 文件完整路径
            file_path = os.path.join(fs_path, filename)
            
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 返回文件URL
            if settings.LOCAL_STORAGE_FULL_URL:
                # 如果配置了完整URL，使用完整URL (去掉前导的/static/uploads)
                if url_path.startswith(settings.LOCAL_STORAGE_URL_PREFIX):
                    rel_path = url_path[len(settings.LOCAL_STORAGE_URL_PREFIX):].lstrip('/')
                    file_url = f"{settings.LOCAL_STORAGE_FULL_URL.rstrip('/')}/{rel_path}/{filename}"
                else:
                    file_url = f"{settings.LOCAL_STORAGE_FULL_URL.rstrip('/')}/{url_path.lstrip('/')}/{filename}"
            else:
                # 否则使用相对路径
                file_url = f"{url_path}/{filename}"
            
            return file_url
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上传到本地存储失败: {str(e)}"
            )
    
    async def upload_to_oss(self, file_content: bytes, oss_file_name: str, file_type: str = "common") -> str:
        """
        上传文件到阿里云OSS
        
        Args:
            file_content: 文件内容
            oss_file_name: OSS中的文件名
            file_type: 文件类型，如image、document等
        
        Returns:
            str: 文件的URL
        
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        # 如果OSS未启用，使用本地存储
        if not settings.OSS_ENABLED:
            return await self.upload_to_local(file_content, oss_file_name, file_type)
            
        # 初始化OSS客户端
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
        
        # 构建完整的OSS文件路径，增加按日期分类的目录结构
        oss_path = self.generate_oss_path(file_type)
        # 使用os.path.join连接路径，然后转换为OSS格式
        oss_file_path = os.path.join(oss_path, oss_file_name).replace('\\', '/')
        
        # 上传文件
        try:
            # 上传文件并设置ACL为公共读，确保文件可以被公开访问
            headers = {'x-oss-object-acl': 'public-read'}
            bucket.put_object(oss_file_path, file_content, headers=headers)
            
            # 获取文件URL
            if settings.OSS_BUCKET_DOMAIN:
                # 如果有自定义域名
                file_url = f"https://{settings.OSS_BUCKET_DOMAIN}/{oss_file_path}"
            else:
                # 使用OSS默认域名
                file_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{oss_file_path}"
            
            return file_url
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上传到OSS失败: {str(e)}"
            )
    
    async def upload_image(self, file: UploadFile) -> Dict:
        """
        上传单个图片到OSS或本地存储
        
        Args:
            file: 上传的图片文件
            
        Returns:
            Dict: 包含上传结果的字典
        """
        # 检查文件
        file_content = await self.check_image_file(file)
        
        # 生成文件名
        file_name = self.generate_oss_file_name(file.filename)
        
        # 上传文件，根据配置选择OSS或本地存储
        file_url = await self.upload_to_oss(file_content, file_name, file_type="image")
        
        # 返回结果
        return {
            "url": file_url,
            "name": file.filename,
            "size": len(file_content)
        }
    
    async def upload_files(self, files: List[UploadFile]) -> List[Dict]:
        """
        批量上传文件到OSS或本地存储
        
        Args:
            files: 上传的文件列表
            
        Returns:
            List[Dict]: 包含上传结果的字典列表
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要上传的文件"
            )
        
        # 限制最大上传数量
        max_files = 10
        if len(files) > max_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"一次最多上传{max_files}个文件"
            )
        
        result = []
        
        for file in files:
            # 检查文件
            file_content = await self.check_file(file)
            
            # 生成文件名
            file_name = self.generate_oss_file_name(file.filename)
            
            # 根据文件扩展名决定文件类型
            file_extension = self.get_file_extension(file.filename).lower()
            file_type = "common"
            
            # 根据扩展名确定文件类型
            if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                file_type = "image"
            elif file_extension in [".doc", ".docx", ".pdf", ".txt", ".xls", ".xlsx"]:
                file_type = "document"
            elif file_extension in [".mp4", ".avi", ".mov", ".wmv"]:
                file_type = "video"
            
            # 上传文件，根据配置选择OSS或本地存储
            file_url = await self.upload_to_oss(file_content, file_name, file_type=file_type)
            
            result.append({
                "url": file_url,
                "name": file.filename,
                "size": len(file_content)
            })
        
        return result
    
    async def list_files(self, prefix: str = None, max_keys: int = 100) -> List[Dict]:
        """
        获取OSS中的文件列表
        
        Args:
            prefix: 路径前缀，例如 "image/"
            max_keys: 最大返回数量，默认100
        
        Returns:
            List[Dict]: 文件信息列表
        """
        try:
            # 初始化OSS客户端
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            
            # 构建完整的前缀，使用os.path.join处理路径
            if prefix:
                full_prefix = os.path.join(settings.OSS_UPLOAD_DIR, prefix).replace('\\', '/')
            else:
                full_prefix = settings.OSS_UPLOAD_DIR
            
            # 列举文件
            result = []
            for obj in oss2.ObjectIterator(bucket, prefix=full_prefix, max_keys=max_keys):
                if not obj.key.endswith('/'):  # 排除目录
                    file_name = os.path.basename(obj.key)
                    
                    # 构建URL
                    if settings.OSS_BUCKET_DOMAIN:
                        file_url = f"https://{settings.OSS_BUCKET_DOMAIN}/{obj.key}"
                    else:
                        file_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{obj.key}"
                    
                    result.append({
                        "name": file_name,
                        "url": file_url,
                        "key": obj.key,
                        "size": obj.size,
                        "last_modified": obj.last_modified.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            return result
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文件列表失败: {str(e)}"
            )
    
    async def delete_local_file(self, file_path: str) -> bool:
        """
        删除本地存储中的文件
        
        Args:
            file_path: 文件的相对路径或完整URL
            
        Returns:
            bool: 是否删除成功
        """
        try:
            print(f"尝试删除本地文件: {file_path}")
            
            # 处理以 'static/uploads/' 开头的路径 (前端传递的格式)
            if file_path.startswith("static/uploads/"):
                # 直接构建到本地存储路径，不要再添加"uploads"
                relative_path = file_path.replace("static/uploads/", "")
                full_path = os.path.join(settings.LOCAL_STORAGE_PATH, relative_path)
                
            # 如果是完整URL，提取相对路径
            elif settings.LOCAL_STORAGE_FULL_URL and file_path.startswith(settings.LOCAL_STORAGE_FULL_URL):
                # 从完整URL中提取相对路径
                relative_path = file_path[len(settings.LOCAL_STORAGE_FULL_URL):].lstrip('/')
                full_path = os.path.join(settings.LOCAL_STORAGE_PATH, relative_path)
                
            # 如果是以URL前缀开头
            elif file_path.startswith(settings.LOCAL_STORAGE_URL_PREFIX):
                # 移除URL前缀
                relative_path = file_path[len(settings.LOCAL_STORAGE_URL_PREFIX):].lstrip('/')
                # 构建完整路径
                full_path = os.path.join(settings.LOCAL_STORAGE_PATH, relative_path)
                
            else:
                # 如果路径不以URL前缀开头，假设它是相对于存储根目录的路径
                full_path = os.path.join(settings.LOCAL_STORAGE_PATH, file_path.lstrip('/'))
                
            print(f"解析后的完整路径: {full_path}")
                
            # 检查文件是否存在
            if os.path.isfile(full_path):
                os.remove(full_path)
                print(f"文件删除成功: {full_path}")
                return True
            
            # 如果文件不存在，记录错误信息但不抛出异常
            print(f"文件不存在: {full_path}")
            return False
            
        except Exception as e:
            print(f"删除本地文件失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除本地文件失败: {str(e)}"
            )
    
    async def delete_file(self, file_key: str) -> bool:
        """
        删除OSS或本地存储中的文件
        
        Args:
            file_key: 文件的OSS键值或本地存储路径
            
        Returns:
            bool: 是否删除成功
        """
        # 检查是否为本地存储路径
        if not settings.OSS_ENABLED or file_key.startswith(settings.LOCAL_STORAGE_URL_PREFIX):
            return await self.delete_local_file(file_key)
            
        try:
            # 初始化OSS客户端
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            
            # 删除文件
            bucket.delete_object(file_key)
            return True
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除文件失败: {str(e)}"
            )
    
    async def set_public_acl(self, prefix: str = None) -> Dict:
        """
        批量设置指定前缀下的文件ACL为公共读
        
        Args:
            prefix: 路径前缀，例如 "image/"
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 初始化OSS客户端
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            
            # 构建完整的前缀
            if prefix:
                full_prefix = os.path.join(settings.OSS_UPLOAD_DIR, prefix).replace('\\', '/')
            else:
                full_prefix = settings.OSS_UPLOAD_DIR
            
            # 处理计数
            count = 0
            error_count = 0
            
            # 列举文件并设置ACL
            for obj in oss2.ObjectIterator(bucket, prefix=full_prefix):
                if not obj.key.endswith('/'):  # 排除目录
                    try:
                        # 设置文件ACL为公共读
                        bucket.put_object_acl(obj.key, oss2.OBJECT_ACL_PUBLIC_READ)
                        count += 1
                    except Exception:
                        error_count += 1
            
            return {
                "success": True,
                "message": f"成功设置 {count} 个文件的ACL为公共读，失败 {error_count} 个",
                "count": count,
                "error_count": error_count
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"设置文件ACL失败: {str(e)}"
            )


upload_controller = UploadController() 