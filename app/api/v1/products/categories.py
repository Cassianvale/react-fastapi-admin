from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from app.schemas.base import Success, SuccessExtra
from app.schemas.products import ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryOut
from app.models.product import ProductCategory
from app.core.dependency import get_page_params

router = APIRouter()


@router.post("", response_model=None, summary="创建商品分类")
async def create_category(category: ProductCategoryCreate):
    # 检查分类名称是否已存在
    exists = await ProductCategory.filter(name=category.name, is_deleted=False).exists()
    if exists:
        raise HTTPException(status_code=400, detail="商品分类名称已存在")
    
    # 创建商品分类
    category_obj = await ProductCategory.create(**category.dict())
    return Success(data=await category_obj.to_dict())


@router.get("", response_model=None, summary="获取商品分类列表")
async def get_categories(
    name: Optional[str] = Query(None, description="分类名称"),
    page_depend: dict = Depends(get_page_params)
):
    # 构建查询条件
    query = ProductCategory.filter(is_deleted=False)
    if name:
        query = query.filter(name__icontains=name)
    
    # 获取分页数据
    page = page_depend.get("page")
    page_size = page_depend.get("page_size")
    total = await query.count()
    categories = await query.order_by("order").offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为字典列表
    category_list = []
    for category in categories:
        category_list.append(await category.to_dict())
    
    return SuccessExtra(data=category_list, total=total, page=page, page_size=page_size)


@router.get("/{category_id}", response_model=None, summary="获取商品分类详情")
async def get_category(category_id: int):
    # 查询商品分类
    category = await ProductCategory.filter(id=category_id, is_deleted=False).first()
    if not category:
        raise HTTPException(status_code=404, detail="商品分类不存在")
    
    return Success(data=await category.to_dict())


@router.put("/{category_id}", response_model=None, summary="更新商品分类")
async def update_category(category_id: int, category: ProductCategoryUpdate):
    # 查询商品分类
    category_obj = await ProductCategory.filter(id=category_id, is_deleted=False).first()
    if not category_obj:
        raise HTTPException(status_code=404, detail="商品分类不存在")
    
    # 更新商品分类
    update_data = {k: v for k, v in category.dict().items() if v is not None}
    await category_obj.update_from_dict(update_data)
    await category_obj.save()
    
    return Success(data=await category_obj.to_dict())


@router.delete("/{category_id}", response_model=None, summary="删除商品分类")
async def delete_category(category_id: int):
    # 查询商品分类
    category = await ProductCategory.filter(id=category_id, is_deleted=False).first()
    if not category:
        raise HTTPException(status_code=404, detail="商品分类不存在")
    
    # 软删除商品分类
    category.is_deleted = True
    await category.save()
    
    return Success(msg="删除成功") 