from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.api import api_controller
from app.core.exceptions import RecordNotFoundError
from app.schemas import Success, SuccessExtra
from app.schemas.apis import *

router = APIRouter()


@router.get("/list", summary="查看API列表")
async def list_api(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    path: str = Query(None, description="API路径"),
    summary: str = Query(None, description="API简介"),
    tags: str = Query(None, description="API模块"),
):
    q = Q()
    if path:
        q &= Q(path__contains=path)
    if summary:
        q &= Q(summary__contains=summary)
    if tags:
        # 支持多标签筛选：tags参数可能是逗号分隔的字符串
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        if tag_list:
            # 使用OR条件匹配任一标签
            tag_q = Q()
            for tag in tag_list:
                tag_q |= Q(tags__contains=tag)
            q &= tag_q
    total, api_objs = await api_controller.list(page=page, page_size=page_size, search=q, order=["tags", "id"])
    data = [await obj.to_dict() for obj in api_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看Api")
async def get_api(
    id: int = Query(..., description="Api"),
):
    api_obj = await api_controller.get(id=id)
    if not api_obj:
        raise RecordNotFoundError("API不存在")
    data = await api_obj.to_dict()
    return Success(data=data)


@router.post("/update", summary="更新Api")
async def update_api(
    api_in: ApiUpdate,
):
    api_obj = await api_controller.get(id=api_in.id)
    if not api_obj:
        raise RecordNotFoundError("API不存在")
    await api_controller.update(id=api_in.id, obj_in=api_in)
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除Api")
async def delete_api(
    api_id: int = Query(..., description="ApiID"),
):
    api_obj = await api_controller.get(id=api_id)
    if not api_obj:
        raise RecordNotFoundError("API不存在")

    # 删除对应的权限
    await api_controller._delete_api_permission(api_obj)

    # 删除API
    await api_controller.remove(id=api_id)
    return Success(msg="删除成功，已同步删除对应权限")


@router.post("/refresh", summary="刷新API列表")
async def refresh_api():
    await api_controller.refresh_api()
    return Success(msg="刷新成功")


@router.get("/tags", summary="获取所有API标签")
async def get_api_tags():
    """获取系统中所有的API标签"""
    tags = await api_controller.get_all_tags()
    return Success(data=tags)
