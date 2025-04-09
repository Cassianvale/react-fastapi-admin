from fastapi import APIRouter

from .categories import router as categories_router
from .products import router as products_router

products_main_router = APIRouter()
products_main_router.include_router(categories_router, prefix="/categories", tags=["商品分类"])
products_main_router.include_router(products_router, prefix="/products", tags=["商品管理"])

__all__ = ["products_main_router"] 