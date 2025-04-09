from tortoise import fields

from .base import BaseModel, TimestampMixin


class ProductCategory(BaseModel, TimestampMixin):
    """商品分类模型"""
    name = fields.CharField(max_length=50, unique=True, description="分类名称", index=True)
    description = fields.CharField(max_length=500, null=True, description="分类描述")
    order = fields.IntField(default=0, description="排序", index=True)
    is_deleted = fields.BooleanField(default=False, description="是否删除", index=True)

    class Meta:
        table = "product_category"


class Product(BaseModel, TimestampMixin):
    """商品模型"""
    name = fields.CharField(max_length=100, description="商品名称", index=True)
    category = fields.ForeignKeyField("models.ProductCategory", related_name="products", description="商品分类")
    image = fields.CharField(max_length=255, null=True, description="商品图片")
    cost_price = fields.DecimalField(max_digits=10, decimal_places=2, description="成本价")
    sale_price = fields.DecimalField(max_digits=10, decimal_places=2, description="销售价")
    specifications = fields.JSONField(null=True, description="商品规格")
    description = fields.TextField(null=True, description="商品描述")
    status = fields.BooleanField(default=True, description="商品状态", index=True)
    is_deleted = fields.BooleanField(default=False, description="是否删除", index=True)

    class Meta:
        table = "product" 