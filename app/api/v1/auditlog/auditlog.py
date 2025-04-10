from fastapi import APIRouter, Query, Body, Path as FastAPIPath, HTTPException, Depends, BackgroundTasks
from tortoise.expressions import Q
from typing import List, Optional
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
    q = Q(is_deleted=False)
    if username:
        q &= Q(username__icontains=username)
    if module:
        q &= Q(module__icontains=module)
    if method:
        q &= Q(method__icontains=method)
    if summary:
        q &= Q(summary__icontains=summary)
    if status is not None:
        q &= Q(status=status)
    if ip_address:
        q &= Q(ip_address__icontains=ip_address)
    if operation_type:
        q &= Q(operation_type__icontains=operation_type)
    if log_level:
        q &= Q(log_level__icontains=log_level)
    if start_time and end_time:
        q &= Q(created_at__range=[start_time, end_time])
    elif start_time:
        q &= Q(created_at__gte=start_time)
    elif end_time:
        q &= Q(created_at__lte=end_time)

    # 使用预加载和优化查询
    total = await AuditLog.filter(q).count()
    
    # 添加排序条件并优化查询
    audit_log_objs = await AuditLog.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    
    # 使用to_dict方法转换数据
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
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以删除日志")
    
    log = await AuditLog.get_or_none(id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
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
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以删除日志")
    
    if not log_ids:
        raise HTTPException(status_code=400, detail="请提供要删除的日志ID")
    
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
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，只有超级管理员可以清空日志")
    
    q = Q(is_deleted=False)
    if days:
        clear_date = datetime.datetime.now() - datetime.timedelta(days=days)
        clear_date_str = clear_date.strftime("%Y-%m-%d")
        q &= Q(created_at__lt=clear_date_str)
    
    count = await AuditLog.filter(q).update(is_deleted=True)
    return Success(msg=f"成功清除{count}条日志")


async def _export_logs_to_csv(
    start_time: str, 
    end_time: str, 
    filters: dict,
    export_path: str
):
    """
    将日志导出到CSV文件（后台任务）
    """
    # 查询符合条件的日志
    q = Q(is_deleted=False)
    for key, value in filters.items():
        if value:
            if key == 'status' and value is not None:
                q &= Q(status=value)
            elif isinstance(value, str):
                q &= Q(**{f"{key}__icontains": value})
    
    if start_time and end_time:
        q &= Q(created_at__range=[start_time, end_time])
    elif start_time:
        q &= Q(created_at__gte=start_time)
    elif end_time:
        q &= Q(created_at__lte=end_time)
    
    logs = await AuditLog.filter(q).order_by("-created_at")
    
    # 确保导出目录存在
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    
    # 写入CSV文件
    with open(export_path, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = [
            'ID', '用户ID', '用户名', '功能模块', '请求描述', '请求方法', 
            '请求路径', '状态码', '响应时间(ms)', 'IP地址', '操作类型', 
            '日志级别', '创建时间', '更新时间'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in logs:
            writer.writerow({
                'ID': log.id,
                '用户ID': log.user_id,
                '用户名': log.username,
                '功能模块': log.module,
                '请求描述': log.summary,
                '请求方法': log.method,
                '请求路径': log.path,
                '状态码': log.status,
                '响应时间(ms)': log.response_time,
                'IP地址': log.ip_address,
                '操作类型': log.operation_type,
                '日志级别': log.log_level,
                '创建时间': log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
                '更新时间': log.updated_at.strftime("%Y-%m-%d %H:%M:%S") if log.updated_at else None
            })


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
    # 生成导出文件名
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
    days: int = Query(7, description="统计最近几天的数据"),
    current_user = Depends(AuthControl.is_authed)
):
    """
    获取最近N天的审计日志统计信息
    """
    statistics = await AuditLog.get_logs_statistics(days)
    return Success(data=statistics)
