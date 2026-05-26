"""
TextGuard 数据库初始化脚本
用途：创建初始管理员账号、角色权限、测试数据
运行方式：python init_database.py
"""
import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_engine, AsyncSessionLocal
from app.models.base import BaseModel
from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.llm_config import LLMConfig
from app.core.security import hash_password


async def init_database():
    """初始化数据库：创建表 + 插入初始数据"""
    
    print("=" * 60)
    print("TextGuard 数据库初始化")
    print("=" * 60)
    
    # 1. 创建所有表
    print("\n[1/5] 创建数据库表...")
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    print("✅ 数据库表创建完成")
    
    # 2. 创建角色
    print("\n[2/5] 创建角色...")
    async with AsyncSessionLocal() as session:
        await create_roles(session)
    print("✅ 角色创建完成")
    
    # 3. 创建权限
    print("\n[3/5] 创建权限...")
    async with AsyncSessionLocal() as session:
        await create_permissions(session)
    print("✅ 权限创建完成")
    
    # 4. 创建初始用户
    print("\n[4/5] 创建初始用户...")
    async with AsyncSessionLocal() as session:
        await create_users(session)
    print("✅ 初始用户创建完成")
    
    # 5. 创建大模型配置示例
    print("\n[5/5] 创建大模型配置示例...")
    async with AsyncSessionLocal() as session:
        await create_llm_configs(session)
    print("✅ 大模型配置示例创建完成")
    
    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n默认账号信息：")
    print("  管理员: admin / admin123")
    print("  普通用户: user001 / user123")
    print("  游客: guest / guest123")
    print("\n访问地址: http://localhost:3022")
    print("API 文档: http://localhost:3020/docs")
    print("=" * 60)


async def create_roles(session: AsyncSession):
    """创建角色"""
    roles_data = [
        {
            "name": "超级管理员",
            "code": "admin",
            "description": "系统最高权限，可管理所有功能",
            "is_system": True,
            "sort_order": 1
        },
        {
            "name": "普通用户",
            "code": "user",
            "description": "标准用户，可使用文档校对、润色等核心功能",
            "is_system": True,
            "sort_order": 2
        },
        {
            "name": "游客",
            "code": "guest",
            "description": "访客用户，功能受限，有每日配额限制",
            "is_system": True,
            "sort_order": 3
        }
    ]
    
    for role_data in roles_data:
        # 检查是否已存在
        result = await session.execute(
            select(Role).where(Role.code == role_data["code"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(**role_data)
            session.add(role)
            print(f"  - 创建角色: {role_data['name']} ({role_data['code']})")
        else:
            print(f"  - 角色已存在: {role_data['name']}")
    
    await session.commit()


async def create_permissions(session: AsyncSession):
    """创建权限树"""
    permissions_data = [
        # 一级菜单：文档校对
        {"name": "文档校对", "code": "proofread", "type": "menu", "parent_id": None, "path": "/proofread", "icon": "Document", "sort_order": 1},
        {"name": "文本校对", "code": "proofread:text", "type": "menu", "parent_id": 1, "path": "/proofread/text", "icon": "Edit", "sort_order": 1},
        {"name": "文档上传校对", "code": "proofread:upload", "type": "menu", "parent_id": 1, "path": "/proofread/upload", "icon": "Upload", "sort_order": 2},
        
        # 一级菜单：AI 润色
        {"name": "AI润色", "code": "polish", "type": "menu", "parent_id": None, "path": "/polish", "icon": "MagicStick", "sort_order": 2},
        
        # 一级菜单：个人中心
        {"name": "个人中心", "code": "profile", "type": "menu", "parent_id": None, "path": "/profile", "icon": "User", "sort_order": 3},
        {"name": "我的词库", "code": "profile:dictionary", "type": "menu", "parent_id": 6, "path": "/profile/dictionary", "icon": "Collection", "sort_order": 1},
        {"name": "放行词管理", "code": "profile:whitelist", "type": "menu", "parent_id": 6, "path": "/profile/whitelist", "icon": "Check", "sort_order": 2},
        
        # 一级菜单：管理后台
        {"name": "管理后台", "code": "admin", "type": "menu", "parent_id": None, "path": "/admin", "icon": "Setting", "sort_order": 10},
        {"name": "用户管理", "code": "admin:users", "type": "menu", "parent_id": 9, "path": "/admin/users", "icon": "User", "sort_order": 1},
        {"name": "角色权限", "code": "admin:roles", "type": "menu", "parent_id": 9, "path": "/admin/roles", "icon": "Lock", "sort_order": 2},
        {"name": "大模型配置", "code": "admin:llm", "type": "menu", "parent_id": 9, "path": "/admin/llm", "icon": "Connection", "sort_order": 3},
        {"name": "全局词库", "code": "admin:global-words", "type": "menu", "parent_id": 9, "path": "/admin/global-words", "icon": "Collection", "sort_order": 4},
        {"name": "审计日志", "code": "admin:audit", "type": "menu", "parent_id": 9, "path": "/admin/audit", "icon": "Document", "sort_order": 5},
        {"name": "系统设置", "code": "admin:settings", "type": "menu", "parent_id": 9, "path": "/admin/settings", "icon": "Tools", "sort_order": 6},
        
        # 按钮级权限
        {"name": "编辑用户", "code": "admin:users:edit", "type": "button", "parent_id": 10, "sort_order": 1},
        {"name": "删除用户", "code": "admin:users:delete", "type": "button", "parent_id": 10, "sort_order": 2},
        {"name": "重置密码", "code": "admin:users:reset-pwd", "type": "button", "parent_id": 10, "sort_order": 3},
        {"name": "编辑角色", "code": "admin:roles:edit", "type": "button", "parent_id": 11, "sort_order": 1},
        {"name": "删除角色", "code": "admin:roles:delete", "type": "button", "parent_id": 11, "sort_order": 2},
        {"name": "编辑大模型", "code": "admin:llm:edit", "type": "button", "parent_id": 12, "sort_order": 1},
        {"name": "删除大模型", "code": "admin:llm:delete", "type": "button", "parent_id": 12, "sort_order": 2},
        {"name": "切换活跃模型", "code": "admin:llm:activate", "type": "button", "parent_id": 12, "sort_order": 3},
        {"name": "编辑系统设置", "code": "admin:settings:edit", "type": "button", "parent_id": 14, "sort_order": 1},
    ]
    
    # 先创建所有权限（不设置 parent）
    permission_map = {}
    for perm_data in permissions_data:
        result = await session.execute(
            select(Permission).where(Permission.code == perm_data["code"])
        )
        existing_perm = result.scalar_one_or_none()
        
        if not existing_perm:
            # 暂时不设置 parent_id
            data = {k: v for k, v in perm_data.items() if k != "parent_id"}
            perm = Permission(**data)
            session.add(perm)
            await session.flush()  # 立即获取 ID
            permission_map[perm_data["code"]] = perm.id
            print(f"  - 创建权限: {perm_data['name']} ({perm_data['code']})")
        else:
            permission_map[perm_data["code"]] = existing_perm.id
            print(f"  - 权限已存在: {perm_data['name']}")
    
    await session.commit()
    
    # 分配权限给角色
    await assign_permissions_to_roles(session, permission_map)


async def assign_permissions_to_roles(session: AsyncSession, permission_map: dict):
    """分配权限给角色"""
    # 获取角色
    result = await session.execute(select(Role))
    roles = {role.code: role for role in result.scalars().all()}
    
    # 管理员拥有所有权限
    admin_role = roles.get("admin")
    if admin_role:
        for perm_id in permission_map.values():
            result = await session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == admin_role.id,
                    RolePermission.permission_id == perm_id
                )
            )
            if not result.scalar_one_or_none():
                session.add(RolePermission(role_id=admin_role.id, permission_id=perm_id))
        print("  - 管理员角色已分配所有权限")
    
    # 普通用户权限（核心功能）
    user_role = roles.get("user")
    if user_role:
        user_permissions = [
            "proofread", "proofread:text", "proofread:upload",
            "polish", "profile", "profile:dictionary", "profile:whitelist"
        ]
        for perm_code in user_permissions:
            perm_id = permission_map.get(perm_code)
            if perm_id:
                result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == user_role.id,
                        RolePermission.permission_id == perm_id
                    )
                )
                if not result.scalar_one_or_none():
                    session.add(RolePermission(role_id=user_role.id, permission_id=perm_id))
        print("  - 普通用户角色已分配核心功能权限")
    
    # 游客权限（仅基础功能）
    guest_role = roles.get("guest")
    if guest_role:
        guest_permissions = ["proofread", "proofread:text", "polish"]
        for perm_code in guest_permissions:
            perm_id = permission_map.get(perm_code)
            if perm_id:
                result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == guest_role.id,
                        RolePermission.permission_id == perm_id
                    )
                )
                if not result.scalar_one_or_none():
                    session.add(RolePermission(role_id=guest_role.id, permission_id=perm_id))
        print("  - 游客角色已分配基础功能权限")
    
    await session.commit()


async def create_users(session: AsyncSession):
    """创建初始用户"""
    # 获取角色
    result = await session.execute(select(Role))
    roles = {role.code: role for role in result.scalars().all()}
    
    users_data = [
        {
            "employee_id": "admin",
            "username": "系统管理员",
            "password": "admin123",
            "role_code": "admin",
            "phone": "13800138000",
            "gender": "male",
            "department": "技术部",
            "is_active": True,
            "daily_quota": None,  # 不限配额
            "remark": "系统默认管理员账号"
        },
        {
            "employee_id": "user001",
            "username": "张三",
            "password": "user123",
            "role_code": "user",
            "phone": "13800138001",
            "gender": "male",
            "department": "产品部",
            "is_active": True,
            "daily_quota": 100,
            "remark": "测试用户账号"
        },
        {
            "employee_id": "guest",
            "username": "游客",
            "password": "guest123",
            "role_code": "guest",
            "is_active": True,
            "daily_quota": 20,
            "remark": "游客体验账号"
        }
    ]
    
    for user_data in users_data:
        # 检查是否已存在
        result = await session.execute(
            select(User).where(User.employee_id == user_data["employee_id"])
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            role = roles.get(user_data.pop("role_code"))
            password = user_data.pop("password")
            
            user = User(
                **user_data,
                role_id=role.id,
                password_hash=hash_password(password),
                last_login_at=datetime.now()
            )
            session.add(user)
            print(f"  - 创建用户: {user.username} ({user.employee_id})")
        else:
            print(f"  - 用户已存在: {user_data['username']}")
    
    await session.commit()


async def create_llm_configs(session: AsyncSession):
    """创建大模型配置示例"""
    llm_configs_data = [
        {
            "name": "DeepSeek 示例",
            "provider": "deepseek",
            "api_base": "https://api.deepseek.com",
            "api_key": "请填写你的 DeepSeek API Key",
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 4000,
            "timeout": 60,
            "max_retries": 3,
            "is_active": False,  # 默认不激活，需用户配置后手动激活
            "is_enabled": True,
            "remark": "DeepSeek 模型配置示例，请在管理后台修改 API Key 后激活"
        },
        {
            "name": "OpenAI GPT-4 示例",
            "provider": "openai",
            "api_base": "https://api.openai.com/v1",
            "api_key": "请填写你的 OpenAI API Key",
            "model": "gpt-4o",
            "temperature": 0.3,
            "max_tokens": 4000,
            "timeout": 60,
            "max_retries": 3,
            "is_active": False,
            "is_enabled": True,
            "remark": "OpenAI GPT-4 配置示例，请在管理后台修改 API Key 后激活"
        },
        {
            "name": "Kimi 示例",
            "provider": "moonshot",
            "api_base": "https://api.moonshot.cn/v1",
            "api_key": "请填写你的 Kimi API Key",
            "model": "moonshot-v1-8k",
            "temperature": 0.3,
            "max_tokens": 4000,
            "timeout": 60,
            "max_retries": 3,
            "is_active": False,
            "is_enabled": True,
            "remark": "Kimi (月之暗面) 配置示例，请在管理后台修改 API Key 后激活"
        }
    ]
    
    for config_data in llm_configs_data:
        # 检查是否已存在
        result = await session.execute(
            select(LLMConfig).where(LLMConfig.name == config_data["name"])
        )
        existing_config = result.scalar_one_or_none()
        
        if not existing_config:
            config = LLMConfig(**config_data)
            session.add(config)
            print(f"  - 创建大模型配置: {config_data['name']}")
        else:
            print(f"  - 大模型配置已存在: {config_data['name']}")
    
    await session.commit()


if __name__ == "__main__":
    asyncio.run(init_database())
