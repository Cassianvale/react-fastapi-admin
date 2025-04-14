from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from fastapi import APIRouter, Header, Depends, HTTPException

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth, AuthControl
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword
from app.settings import settings
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    
    # 获取当前时间
    now = datetime.now(timezone.utc)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + access_token_expires
    access_token = create_access_token(
        data=JWTPayload(
            user_id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            exp=expire,
        )
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(user_id=user.id)
    
    data = JWTOut(
        access_token=access_token,
        refresh_token=refresh_token,
        username=user.username,
    )
    return Success(data=data.model_dump())


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh_token", summary="刷新访问令牌")
async def refresh_token(request: RefreshTokenRequest):
    """
    使用刷新令牌获取新的访问令牌
    """
    try:
        # 验证刷新令牌
        decoded = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True}
        )
        
        # 验证令牌类型
        if decoded.get("sub") != "refresh":
            raise HTTPException(status_code=400, detail="无效的刷新令牌类型")
        
        # 获取用户ID
        user_id = decoded.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="刷新令牌中缺少用户标识")
        
        # 查询用户
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="用户不存在或已被删除")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires
        
        access_token = create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        )
        
        return Success(data={"access_token": access_token})
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="刷新令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="无效的刷新令牌")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新令牌出错: {str(e)}")


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")


@router.post("/logout", summary="用户注销", dependencies=[DependAuth])
async def logout(token: str = Header(..., description="token验证")):
    """
    用户注销接口，将当前token加入黑名单
    """
    # 获取用户ID
    user_id = CTX_USER_ID.get()
    
    # 调用AuthControl的logout方法注销用户
    await AuthControl.logout(token, user_id)
    
    return Success(msg="注销成功")
