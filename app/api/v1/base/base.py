import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from fastapi import APIRouter, Header, Depends, HTTPException

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth, AuthControl
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword, ProfileUpdate
from app.settings import settings
from app.utils.jwt_utils import create_access_token, create_refresh_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    """
    用户登录接口

    Args:
        credentials: 登录凭证（用户名和密码）

    Returns:
        登录成功返回访问令牌和刷新令牌

    Raises:
        ValidationError: 当认证失败时抛出
    """
    try:
        user = await user_controller.authenticate(credentials)
        if not user:
            raise ValidationError("用户认证失败")

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

    except HTTPException as e:
        raise ValidationError(e.detail)
    except Exception as e:
        raise ValidationError(f"登录失败: {str(e)}")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh_token", summary="刷新访问令牌")
async def refresh_token(request: RefreshTokenRequest):
    """
    使用刷新令牌获取新的访问令牌

    Args:
        request: 包含刷新令牌的请求

    Returns:
        新的访问令牌

    Raises:
        AuthenticationError: 当刷新令牌无效或过期时抛出
    """
    try:
        # 验证刷新令牌
        decoded = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True},
        )

        # 验证令牌类型
        if decoded.get("sub") != "refresh":
            raise AuthenticationError("无效的刷新令牌类型")

        # 获取用户ID
        user_id = decoded.get("user_id")
        if not user_id:
            raise AuthenticationError("刷新令牌中缺少用户标识")

        # 查询用户
        user = await User.filter(id=user_id).first()
        if not user:
            raise AuthenticationError("用户不存在或已被删除")

        if not user.is_active:
            raise AuthenticationError("用户已被禁用")

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
        raise AuthenticationError("刷新令牌已过期")
    except jwt.InvalidTokenError:
        raise AuthenticationError("无效的刷新令牌")
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"刷新令牌出错: {str(e)}")


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    """
    获取当前用户信息

    Returns:
        用户信息（不包含密码）

    Raises:
        AuthenticationError: 当用户不存在时抛出
    """
    user_id = CTX_USER_ID.get()
    if not user_id:
        raise AuthenticationError("用户ID不存在")

    user_obj = await user_controller.get(id=user_id)
    if not user_obj:
        raise AuthenticationError("用户不存在")

    data = await user_obj.to_dict(exclude_fields=["password"])
    data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    """
    获取当前用户的菜单权限

    Returns:
        用户有权限的菜单树结构（不包含隐藏菜单）

    Raises:
        AuthenticationError: 当用户不存在时抛出
    """
    user_id = CTX_USER_ID.get()
    if not user_id:
        raise AuthenticationError("用户ID不存在")

    user_obj = await User.filter(id=user_id).first()
    if not user_obj:
        raise AuthenticationError("用户不存在")

    menus: list[Menu] = []

    # 超级用户获取所有非隐藏菜单
    if user_obj.is_superuser:
        menus = await Menu.filter(is_hidden=False).all()
    else:
        # 普通用户根据角色获取非隐藏菜单
        role_objs: list[Role] = await user_obj.roles
        if role_objs:
            for role_obj in role_objs:
                menu_list = await role_obj.menus.filter(is_hidden=False)
                if menu_list:
                    menus.extend(menu_list)
            # 去重
            menus = list(set(menus))

    # 获取父级菜单（只包含非隐藏菜单）
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)

    # 构建菜单树
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []

        # 添加子菜单（只包含非隐藏菜单）
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())

        res.append(parent_menu_dict)

    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    """
    获取当前用户的API权限

    Returns:
        用户有权限的API列表

    Raises:
        AuthenticationError: 当用户不存在时抛出
    """
    user_id = CTX_USER_ID.get()
    if not user_id:
        raise AuthenticationError("用户ID不存在")

    user_obj = await User.filter(id=user_id).first()
    if not user_obj:
        raise AuthenticationError("用户不存在")

    apis = []

    # 超级用户获取所有API
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
    else:
        # 普通用户根据角色获取API
        role_objs: list[Role] = await user_obj.roles
        if role_objs:
            for role_obj in role_objs:
                api_list: list[Api] = await role_obj.apis
                if api_list:
                    apis.extend([api.method.lower() + api.path for api in api_list])
            # 去重
            apis = list(set(apis))

    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    """
    更新用户密码

    Args:
        req_in: 包含旧密码和新密码的请求

    Returns:
        操作结果

    Raises:
        AuthenticationError: 当用户不存在时抛出
        ValidationError: 当密码验证失败时抛出
    """
    user_id = CTX_USER_ID.get()
    if not user_id:
        raise AuthenticationError("用户ID不存在")

    user = await user_controller.get(user_id)
    if not user:
        raise AuthenticationError("用户不存在")

    # 验证旧密码
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        raise ValidationError("旧密码验证错误")

    # 更新密码
    user.password = get_password_hash(req_in.new_password)
    await user.save()

    return Success(msg="修改成功")


@router.post("/update_profile", summary="更新个人信息", dependencies=[DependAuth])
async def update_user_profile(req_in: ProfileUpdate):
    """
    更新当前用户的个人信息

    Args:
        req_in: 包含要更新的个人信息

    Returns:
        操作结果

    Raises:
        AuthenticationError: 当用户不存在时抛出
        ValidationError: 当邮箱已被使用时抛出
    """
    user_id = CTX_USER_ID.get()
    if not user_id:
        raise AuthenticationError("用户ID不存在")

    user = await user_controller.get(user_id)
    if not user:
        raise AuthenticationError("用户不存在")

    # 检查邮箱是否已被其他用户使用
    if req_in.email and req_in.email != user.email:
        existing_user = await user_controller.get_by_email(req_in.email)
        if existing_user and existing_user.id != user_id:
            raise ValidationError("该邮箱地址已被其他用户使用")

    # 更新用户信息
    update_data = req_in.update_dict()
    if update_data:
        for key, value in update_data.items():
            if hasattr(user, key):
                # 检查字段是否允许null值
                field = user._meta.fields_map.get(key)
                if field and value is None and not field.null:
                    # 如果字段不允许null且值为None，则跳过更新该字段
                    continue
                setattr(user, key, value)
        await user.save()

    return Success(msg="个人信息更新成功")


@router.post("/logout", summary="用户注销", dependencies=[DependAuth])
async def logout(token: str = Header(..., description="token验证")):
    """
    用户注销接口，将当前token加入黑名单

    Args:
        token: 用户的访问令牌

    Returns:
        注销结果
    """
    try:
        # 获取用户ID
        user_id = CTX_USER_ID.get()

        # 调用AuthControl的logout方法注销用户
        await AuthControl.logout(token, user_id)

        return Success(msg="注销成功")

    except Exception as e:
        raise AuthenticationError(f"注销失败: {str(e)}")
