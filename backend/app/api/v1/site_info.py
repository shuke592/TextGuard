"""
TextGuard 站点信息公开接口
无需登录即可获取平台名称、图标等配置
"""
from fastapi import APIRouter
from app.services.site_config import get_site_config

router = APIRouter(prefix="/site", tags=["站点信息"])


@router.get("/info")
async def get_site_info():
    """获取站点公开配置（平台名称、副标题、图标）"""
    config = await get_site_config()
    return config
