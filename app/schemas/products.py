from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class ProductCategoryBase(BaseModel):
    name: str = Field(..., title="分类名称", max_length=50)
    description: Optional[str] = Field(None, title="分类描述", max_length=500)
    order: int = Field(default=0, title="排序")

    class Config:
        from_attributes = True


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(ProductCategoryBase):
    name: Optional[str] = Field(None, title="分类名称", max_length=50)
    description: Optional[str] = Field(None, title="分类描述", max_length=500)
    order: Optional[int] = Field(None, title="排序")
    is_deleted: Optional[bool] = Field(None, title="是否删除")


class ProductCategoryOut(ProductCategoryBase):
    id: int
    is_deleted: bool = False


class ProductBase(BaseModel):
    name: str = Field(..., title="商品名称", max_length=100)
    category_id: int = Field(..., title="商品分类ID")
    image: Optional[str] = Field(None, title="商品图片", max_length=255)
    cost_price: Decimal = Field(..., title="成本价")
    sale_price: Decimal = Field(..., title="销售价")
    specifications: Optional[Dict[str, Any]] = Field(None, title="商品规格")
    description: Optional[str] = Field(None, title="商品描述")
    status: bool = Field(default=True, title="商品状态")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)  # 将Decimal转换为字符串
        }


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = Field(None, title="商品名称", max_length=100)
    category_id: Optional[int] = Field(None, title="商品分类ID")
    image: Optional[str] = Field(None, title="商品图片", max_length=255)
    cost_price: Optional[Decimal] = Field(None, title="成本价")
    sale_price: Optional[Decimal] = Field(None, title="销售价")
    specifications: Optional[Dict[str, Any]] = Field(None, title="商品规格")
    description: Optional[str] = Field(None, title="商品描述")
    status: Optional[bool] = Field(None, title="商品状态")
    is_deleted: Optional[bool] = Field(None, title="是否删除")


class ProductOut(ProductBase):
    id: int
    category_name: str
    is_deleted: bool = False


class ProductFilter(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[bool] = None 