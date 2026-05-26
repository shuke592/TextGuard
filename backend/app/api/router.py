"""
TextGuard API 路由聚合
将所有模块的路由注册到统一的 router 中
"""
from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.feishu import router as feishu_router
from app.api.v1.proofread import router as proofread_router
from app.api.v1.document import router as document_router
from app.api.v1.dictionary import router as dictionary_router
from app.api.v1.whitelist import router as whitelist_router
from app.api.v1.history import router as history_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.polish import router as polish_router
from app.api.v1.site_info import router as site_info_router
from app.api.v1.admin.dashboard import router as admin_dashboard_router
from app.api.v1.admin.roles import router as admin_roles_router
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.admin.global_dict import router as admin_global_dict_router
from app.api.v1.admin.llm_config import router as admin_llm_config_router
from app.api.v1.admin.settings import router as admin_settings_router
from app.api.v1.admin.audit import router as admin_audit_router
from app.api.v1.admin.documents import router as admin_documents_router
from app.api.v1.admin.policy import router as admin_policy_router
from app.api.v1.admin.system_config import router as admin_system_config_router

# 主路由
api_router = APIRouter()

# ---- 基础模块 ----
api_router.include_router(health_router)

# ---- 认证模块 ----
api_router.include_router(auth_router)
api_router.include_router(feishu_router)

# ---- 校对模块 ----
api_router.include_router(proofread_router)

# ---- AI润色模块 ----
api_router.include_router(polish_router)

# ---- 文档校对模块 ----
api_router.include_router(document_router)

# ---- 词库与放行词模块 ----
api_router.include_router(dictionary_router)
api_router.include_router(whitelist_router)

# ---- 校对历史模块 ----
api_router.include_router(history_router)

# ---- 异步任务模块 ----
api_router.include_router(tasks_router)

# ---- 管理后台模块 ----
api_router.include_router(admin_dashboard_router, prefix="/admin")
api_router.include_router(admin_roles_router, prefix="/admin")
api_router.include_router(admin_users_router, prefix="/admin")
api_router.include_router(admin_global_dict_router, prefix="/admin")
api_router.include_router(admin_llm_config_router, prefix="/admin")
api_router.include_router(admin_settings_router, prefix="/admin")
api_router.include_router(admin_audit_router, prefix="/admin")
api_router.include_router(admin_documents_router, prefix="/admin")
api_router.include_router(admin_policy_router, prefix="/admin")
api_router.include_router(admin_system_config_router, prefix="/admin")

# ---- 站点信息（公开） ----
api_router.include_router(site_info_router)
