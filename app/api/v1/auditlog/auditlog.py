from fastapi import APIRouter, Query, Body, Path as FastAPIPath, HTTPException, Depends, BackgroundTasks
from tortoise.expressions import Q
from typing import List, Optional, Dict, Any, Union
import csv
import os
import datetime
from pathlib import Path
from fastapi.responses import FileResponse

from app.models.admin import AuditLog
from app.schemas import SuccessExtra, Success
from app.schemas.apis import *
from app.core.dependency import AuthControl

router = APIRouter()


def build_query_filter(
    username: str = "",
    module: str = "",
    method: str = "",
    summary: str = "",
    status: Optional[int] = None,
    ip_address: str = "",
    operation_type: str = "",
    log_level: str = "",
    start_time: str = "",
    end_time: str = ""
) -> Q:
    """构建统一的查询条件过滤器
    
    将所有查询条件统一处理为一个Q对象，方便重复使用
    """
    # 基础条件：未删除的记录
    q = Q(is_deleted=False)
    
    # 添加文本匹配条件
    if username:
        q &= Q(username__icontains=username)
    if module:
        q &= Q(module__icontains=module)
    if method:
        q &= Q(method__icontains=method)
    if summary:
        q &= Q(summary__icontains=summary)
    if ip_address:
        q &= Q(ip_address__icontains=ip_address)
    if operation_type:
        q &= Q(operation_type__icontains=operation_type)
    if log_level:
        q &= Q(log_level__icontains=log_level)
    
    # 添加数值匹配条件
    if status is not None:
        q &= Q(status=status)
    
    # 添加时间范围条件
    if start_time and end_time:
        q &= Q(created_at__range=[start_time, end_time])
    elif start_time:
        q &= Q(created_at__gte=start_time)
    elif end_time:
        q &= Q(created_at__lte=end_time)
    
    return q


@router.get("/list", summary="查看操作日志")
async def get_audit_log_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="操作人名称"),
    module: str = Query("", description="功能模块"),
    method: str = Query("", description="请求方法"),
    summary: str = Query("", description="接口描述"),
    status: int = Query(None, description="状态码"),
    ip_address: str = Query("", description="IP地址"),
    operation_type: str = Query("", description="操作类型"),
    log_level: str = Query("", description="日志级别"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """
    获取审计日志列表，支持多种过滤条件
    """
    # 构建查询条件
    q = build_query_filter(
        username, module, method, summary, status,
        ip_address, operation_type, log_level,
        start_time, end_time
    )
    
    # 获取总记录数（提前使用count优化查询）
    total = await AuditLog.filter(q).count()
    
    # 分页查询数据并按创建时间倒序排序
    audit_log_objs = await AuditLog.filter(q).order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    
    # 转换为字典格式
    data = [await audit_log.to_dict() for audit_log in audit_log_objs]
    
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.delete("/delete/{log_id}", summary="删除操作日志")
async def delete_audit_log(
    log_id: int = FastAPIPath(..., description="日志ID"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    删除指定的审计日志（软删除）
    """
    # 权限检查
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以删除日志")
    
    # 检查日志是否存在
    log = await AuditLog.get_or_none(id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    # 执行软删除
    await AuditLog.filter(id=log_id).update(is_deleted=True)
    return Success(msg="删除成功")


@router.delete("/batch_delete", summary="批量删除操作日志")
async def batch_delete_audit_logs(
    log_ids: List[int] = Body(..., description="日志ID列表"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    批量删除指定的审计日志（软删除）
    """
    # 权限检查
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以删除日志")
    
    # 检查参数
    if not log_ids:
        raise HTTPException(status_code=400, detail="请提供要删除的日志ID")
    
    # 执行批量软删除
    count = await AuditLog.batch_delete(log_ids)
    return Success(msg=f"成功删除{count}条日志")


@router.delete("/clear", summary="清空操作日志")
async def clear_audit_logs(
    days: Optional[int] = Query(None, description="清除多少天前的日志，不提供则清除所有"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    清空所有或指定天数前的审计日志（软删除）
    """
    # 权限检查
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以清空日志")
    
    # 构建查询条件
    q = Q(is_deleted=False)
    if days:
        clear_date = datetime.datetime.now() - datetime.timedelta(days=days)
        clear_date_str = clear_date.strftime("%Y-%m-%d")
        q &= Q(created_at__lt=clear_date_str)
    
    # 执行批量软删除
    count = await AuditLog.filter(q).update(is_deleted=True)
    return Success(msg=f"成功清除{count}条日志")


async def _export_logs_to_csv(
    start_time: str, 
    end_time: str, 
    filters: Dict[str, Any],
    export_path: str
):
    """
    将日志导出到CSV文件（后台任务）
    """
    # 构建查询条件
    filter_params = {
        'username': filters.get('username', ''),
        'module': filters.get('module', ''),
        'method': filters.get('method', ''),
        'summary': filters.get('summary', ''),
        'status': filters.get('status'),
        'ip_address': filters.get('ip_address', ''),
        'operation_type': filters.get('operation_type', ''),
        'log_level': filters.get('log_level', '')
    }
    q = build_query_filter(**filter_params, start_time=start_time, end_time=end_time)
    
    # 查询符合条件的日志
    logs = await AuditLog.filter(q).order_by("-created_at")
    
    # 确保导出目录存在
    export_dir = os.path.dirname(export_path)
    os.makedirs(export_dir, exist_ok=True)
    
    # 字段名称映射
    field_names_map = {
        'ID': 'id',
        '用户ID': 'user_id',
        '用户名': 'username',
        '功能模块': 'module',
        '请求描述': 'summary',
        '请求方法': 'method',
        '请求路径': 'path',
        '状态码': 'status',
        '响应时间(ms)': 'response_time',
        'IP地址': 'ip_address',
        '操作类型': 'operation_type',
        '日志级别': 'log_level',
        '创建时间': 'created_at',
        '更新时间': 'updated_at'
    }
    
    # 写入CSV文件
    try:
        with open(export_path, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = list(field_names_map.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                # 创建行数据
                row_data = {}
                for display_name, field_name in field_names_map.items():
                    value = getattr(log, field_name)
                    # 处理时间格式
                    if field_name in ('created_at', 'updated_at') and value:
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    row_data[display_name] = value
                
                writer.writerow(row_data)
    except Exception as e:
        # 记录导出错误但不中断程序
        import logging
        logging.error(f"导出日志到CSV文件失败: {str(e)}")


@router.post("/export", summary="导出操作日志")
async def export_audit_logs(
    background_tasks: BackgroundTasks,
    username: str = Body("", description="操作人名称"),
    module: str = Body("", description="功能模块"),
    method: str = Body("", description="请求方法"),
    summary: str = Body("", description="接口描述"),
    status: Optional[int] = Body(None, description="状态码"),
    ip_address: str = Body("", description="IP地址"),
    operation_type: str = Body("", description="操作类型"),
    log_level: str = Body("", description="日志级别"),
    start_time: str = Body("", description="开始时间"),
    end_time: str = Body("", description="结束时间"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    导出审计日志到CSV文件
    """
    # 生成导出文件名和路径
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    export_dir = Path("./exports/auditlogs")
    export_dir.mkdir(parents=True, exist_ok=True)
    export_file = f"auditlog_export_{timestamp}.csv"
    export_path = export_dir / export_file
    
    # 准备过滤条件
    filters = {
        'username': username,
        'module': module,
        'method': method,
        'summary': summary,
        'status': status,
        'ip_address': ip_address,
        'operation_type': operation_type,
        'log_level': log_level
    }
    
    # 启动后台任务导出日志
    background_tasks.add_task(
        _export_logs_to_csv, 
        start_time, 
        end_time, 
        filters,
        str(export_path)
    )
    
    return Success(msg=f"正在导出日志，文件将保存为 {export_file}")


@router.get("/download/{filename}", summary="下载导出的日志文件")
async def download_export_file(
    filename: str = FastAPIPath(..., description="导出文件名"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    下载已导出的审计日志文件
    """
    # 验证文件名，防止目录遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    file_path = Path(f"./exports/auditlogs/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在或已被删除")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/csv"
    )


@router.get("/statistics", summary="获取操作日志统计信息")
async def get_audit_log_statistics(
    days: int = Query(7, description="统计最近几天的数据", ge=1, le=30),
    current_user = Depends(AuthControl.is_authed)
):
    """
    获取最近N天的审计日志统计信息
    """
    # 添加参数验证
    if days < 1:
        days = 1
    elif days > 30:
        days = 30
        
    statistics = await AuditLog.get_logs_statistics(days)
    return Success(data=statistics)
