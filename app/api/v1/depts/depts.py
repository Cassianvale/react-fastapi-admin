from fastapi import APIRouter, Query

from app.controllers.dept import dept_controller
from app.schemas import Success
from app.schemas.depts import *

router = APIRouter()


@router.get("/list", summary="查看部门列表")
async def list_dept(
    name: str = Query(None, description="部门名称"),
):
    dept_tree = await dept_controller.get_dept_tree(name)
    return Success(data=dept_tree)


@router.get("/get", summary="查看部门")
async def get_dept(
    id: int = Query(..., description="部门ID"),
):
    dept_obj = await dept_controller.get(id=id)
    data = await dept_obj.to_dict()
    return Success(data=data)


@router.post("/create", summary="创建部门")
async def create_dept(
    dept_in: DeptCreate,
):
    dept_obj = await dept_controller.create_dept(obj_in=dept_in)
    return Success(msg="Created Successfully", data={"id": dept_obj.id})


@router.post("/update", summary="更新部门")
async def update_dept(
    dept_in: DeptUpdate,
):
    dept_obj = await dept_controller.update_dept(obj_in=dept_in)
    return Success(msg="Update Successfully", data={"id": dept_obj.id})


@router.delete("/delete", summary="删除部门")
async def delete_dept(
    dept_id: int = Query(..., description="部门ID"),
    cascade: bool = Query(True, description="是否级联删除子部门"),
):
    await dept_controller.delete_dept(dept_id=dept_id, cascade=cascade)
    return Success(msg="Deleted Success")
