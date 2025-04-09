from fastapi import APIRouter, Depends, Query, HTTPException, Body
from typing import List, Optional

from app.schemas.base import Success, SuccessExtra
from app.schemas.products import ProductCreate, ProductUpdate, ProductOut, ProductFilter
from app.models.product import Product, ProductCategory
from app.core.dependency import get_page_params

router = APIRouter()


@router.post("/", response_model=None, summary="创建商品")
async def create_product(product: ProductCreate):
    # 检查分类是否存在
    category = await ProductCategory.filter(id=product.category_id, is_deleted=False).first()
    if not category:
        raise HTTPException(status_code=400, detail="商品分类不存在")
    
    # 创建商品
    product_data = product.dict()
    product_obj = await Product.create(**product_data)
    
    # 获取详情数据
    product_dict = await product_obj.to_dict()
    product_dict["category_name"] = category.name
    
    return Success(data=product_dict)


@router.get("/", response_model=None, summary="获取商品列表")
async def get_products(
    filter_data: ProductFilter = Depends(),
    page_depend: dict = Depends(get_page_params)
):
    # 构建查询条件
    query = Product.filter(is_deleted=False)
    if filter_data.name:
        query = query.filter(name__icontains=filter_data.name)
    if filter_data.category_id:
        query = query.filter(category_id=filter_data.category_id)
    if filter_data.status is not None:
        query = query.filter(status=filter_data.status)
    
    # 获取分页数据
    page = page_depend.get("page")
    page_size = page_depend.get("page_size")
    total = await query.count()
    products = await query.order_by("-id").offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为字典列表
    product_list = []
    for product in products:
        product_dict = await product.to_dict()
        category = await ProductCategory.filter(id=product.category_id).first()
        product_dict["category_name"] = category.name if category else ""
        product_list.append(product_dict)
    
    return SuccessExtra(data=product_list, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=None, summary="获取商品详情")
async def get_product(product_id: int):
    # 查询商品
    product = await Product.filter(id=product_id, is_deleted=False).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 获取详情数据
    product_dict = await product.to_dict()
    category = await ProductCategory.filter(id=product.category_id).first()
    product_dict["category_name"] = category.name if category else ""
    
    return Success(data=product_dict)


@router.put("/{product_id}", response_model=None, summary="更新商品")
async def update_product(product_id: int, product: ProductUpdate):
    # 查询商品
    product_obj = await Product.filter(id=product_id, is_deleted=False).first()
    if not product_obj:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查分类是否存在
    if product.category_id:
        category_exists = await ProductCategory.filter(id=product.category_id, is_deleted=False).exists()
        if not category_exists:
            raise HTTPException(status_code=400, detail="商品分类不存在")
    
    # 更新商品
    update_data = {k: v for k, v in product.dict().items() if v is not None}
    await product_obj.update_from_dict(update_data)
    await product_obj.save()
    
    # 获取详情数据
    product_dict = await product_obj.to_dict()
    category = await ProductCategory.filter(id=product_obj.category_id).first()
    product_dict["category_name"] = category.name if category else ""
    
    return Success(data=product_dict)


@router.delete("/{product_id}", response_model=None, summary="删除商品")
async def delete_product(product_id: int):
    # 查询商品
    product = await Product.filter(id=product_id, is_deleted=False).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 软删除商品
    product.is_deleted = True
    await product.save()
    
    return Success(msg="删除成功")


@router.put("/{product_id}/status", response_model=None, summary="更新商品状态")
async def update_product_status(product_id: int, status: bool = Body(..., embed=True)):
    # 查询商品
    product = await Product.filter(id=product_id, is_deleted=False).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 更新商品状态
    product.status = status
    await product.save()
    
    return Success(msg="状态更新成功") 