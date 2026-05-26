"""
TextGuard 飞书OAuth2.0对接服务
实现飞书扫码登录、SSO登录、用户信息获取等功能
注意：使用标准库 urllib.request + asyncio.to_thread 替代 httpx AsyncClient，
解决Docker容器中httpx异步连接超时问题 (ConnectTimeout)
增加DNS预解析缓存+重试机制，解决服务器DNS解析超时挂起问题
"""
import asyncio
import http.client
import json
import socket
import ssl
import threading
import time
import traceback
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from loguru import logger

from app.core.config import settings

# 重试配置
MAX_RETRIES = 4          # 最大重试次数（含首次）
RETRY_DELAY_BASE = 0.3   # 重试间隔基数（秒），缩短以加速飞书登录

# DNS 缓存配置
_dns_cache: Dict[str, tuple] = {}  # hostname -> (ip, expire_time)
_dns_lock = threading.Lock()
_DNS_CACHE_TTL = 600       # 缓存有效期10分钟
_DNS_RESOLVE_TIMEOUT = 3   # DNS解析超时3秒


def _resolve_dns(hostname: str) -> Optional[str]:
    """
    带超时+缓存的DNS解析
    解决Python stdlib DNS解析(getaddrinfo)无法设置超时、可能挂起2分钟的问题
    """
    now = time.time()
    # 检查缓存
    with _dns_lock:
        if hostname in _dns_cache:
            ip, expire = _dns_cache[hostname]
            if now < expire:
                return ip
            # 缓存过期但保留作为兜底

    # 在子线程中执行DNS解析（严格超时控制）
    result = [None]
    error = [None]

    def do_resolve():
        try:
            infos = socket.getaddrinfo(hostname, 443, socket.AF_INET, socket.SOCK_STREAM)
            if infos:
                result[0] = infos[0][4][0]
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=do_resolve, daemon=True)
    t.start()
    t.join(timeout=_DNS_RESOLVE_TIMEOUT)

    if t.is_alive():
        # DNS解析超时，使用过期缓存兜底
        logger.warning(f"[飞书DNS] {hostname} 解析超时({_DNS_RESOLVE_TIMEOUT}s)")
        with _dns_lock:
            if hostname in _dns_cache:
                logger.info(f"[飞书DNS] 使用缓存IP: {_dns_cache[hostname][0]}")
                return _dns_cache[hostname][0]
        return None

    if error[0]:
        logger.warning(f"[飞书DNS] {hostname} 解析失败: {error[0]}")
        with _dns_lock:
            if hostname in _dns_cache:
                logger.info(f"[飞书DNS] 使用缓存IP兜底: {_dns_cache[hostname][0]}")
                return _dns_cache[hostname][0]
        return None

    if result[0]:
        with _dns_lock:
            _dns_cache[hostname] = (result[0], now + _DNS_CACHE_TTL)
        return result[0]

    return None


class _DNSCachedHTTPSConnection(http.client.HTTPSConnection):
    """自定义HTTPS连接：使用预解析的IP直连，保持SNI正确"""

    def __init__(self, host, **kwargs):
        self._real_host = host
        super().__init__(host, **kwargs)

    def connect(self):
        """重写connect：先尝试使用缓存IP直连，失败则走默认"""
        ip = _resolve_dns(self._real_host)
        if ip:
            # 使用IP建立TCP连接
            self.sock = socket.create_connection(
                (ip, self.port or 443),
                timeout=self.timeout
            )
            # SSL包装，server_hostname保持原始域名以通过证书校验
            ctx = self._context or ssl.create_default_context()
            self.sock = ctx.wrap_socket(self.sock, server_hostname=self._real_host)
        else:
            # 兜底：走默认连接（可能慢但至少尝试）
            super().connect()


class _DNSCachedHTTPSHandler(urllib.request.HTTPSHandler):
    """自定义HTTPS Handler：使用DNS缓存连接"""

    def https_open(self, req):
        return self.do_open(_DNSCachedHTTPSConnection, req, context=self._context)


def _build_opener():
    """构建使用DNS缓存的urllib opener"""
    ctx = ssl.create_default_context()
    handler = _DNSCachedHTTPSHandler(context=ctx)
    return urllib.request.build_opener(handler)


def _sync_http_post(url: str, payload: Dict, headers: Optional[Dict] = None, timeout: int = 4) -> Dict[str, Any]:
    """
    同步HTTP POST请求（在线程池中执行）
    使用DNS缓存解决DNS解析超时问题
    :param url: 请求URL
    :param payload: JSON请求体
    :param headers: 自定义请求头
    :param timeout: socket超时秒数
    :return: {"http_status": int, "data": dict} 或 {"error": str}
    """
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        opener = _build_opener()
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return {"http_status": resp.status, "data": json.loads(body)}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw_body": body}
        return {"http_status": e.code, "data": data}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _sync_http_get(url: str, headers: Optional[Dict] = None, timeout: int = 4) -> Dict[str, Any]:
    """同步HTTP GET请求（使用DNS缓存）"""
    try:
        req = urllib.request.Request(url, method="GET")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        opener = _build_opener()
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return {"http_status": resp.status, "data": json.loads(body)}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw_body": body}
        return {"http_status": e.code, "data": data}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _is_dns_error(error_msg: str) -> bool:
    """判断是否为DNS/网络相关的可重试错误"""
    dns_keywords = [
        "name resolution",
        "Name or service not known",
        "Temporary failure",
        "timed out",
        "TimeoutError",
        "ConnectionRefused",
        "Network is unreachable",
        "URLError",
    ]
    return any(kw.lower() in error_msg.lower() for kw in dns_keywords)


def _sync_http_post_with_retry(url: str, payload: Dict, headers: Optional[Dict] = None, timeout: int = 4) -> Dict[str, Any]:
    """
    带重试的同步HTTP POST请求
    遇到DNS/网络错误时自动重试（配合DNS缓存，通常首次即成功）
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        result = _sync_http_post(url, payload, headers, timeout)
        # 成功或业务层错误（非网络错误）直接返回
        if "error" not in result:
            if attempt > 0:
                logger.info(f"[飞书] POST {url} 第{attempt+1}次尝试成功")
            return result
        # 网络错误判断是否可重试
        error_msg = result["error"]
        if not _is_dns_error(error_msg):
            return result  # 非DNS错误不重试
        last_error = error_msg
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAY_BASE * (attempt + 1)
            logger.warning(f"[飞书] POST {url} 第{attempt+1}次失败({error_msg})，{delay}秒后重试...")
            time.sleep(delay)
    return {"error": last_error}


def _sync_http_get_with_retry(url: str, headers: Optional[Dict] = None, timeout: int = 4) -> Dict[str, Any]:
    """
    带重试的同步HTTP GET请求
    遇到DNS/网络错误时自动重试（配合DNS缓存，通常首次即成功）
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        result = _sync_http_get(url, headers, timeout)
        if "error" not in result:
            if attempt > 0:
                logger.info(f"[飞书] GET {url} 第{attempt+1}次尝试成功")
            return result
        error_msg = result["error"]
        if not _is_dns_error(error_msg):
            return result
        last_error = error_msg
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAY_BASE * (attempt + 1)
            logger.warning(f"[飞书] GET {url} 第{attempt+1}次失败({error_msg})，{delay}秒后重试...")
            time.sleep(delay)
    return {"error": last_error}


class FeishuService:
    """飞书开放平台API服务（使用同步HTTP + 线程池 + DNS缓存，解决Docker网络问题）"""

    BASE_URL = "https://open.feishu.cn/open-apis"
    # 需要预解析的飞书域名
    _FEISHU_HOSTS = ["open.feishu.cn", "accounts.feishu.cn"]

    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        self.redirect_uri = settings.FEISHU_REDIRECT_URI
        # 启动时预热DNS缓存（后台线程，不阻塞启动）
        if settings.FEISHU_ENABLED:
            threading.Thread(target=self._warmup_dns, daemon=True).start()

    def _warmup_dns(self):
        """预热飞书域名DNS缓存"""
        for host in self._FEISHU_HOSTS:
            ip = _resolve_dns(host)
            if ip:
                logger.info(f"[飞书DNS] 预热成功: {host} -> {ip}")
            else:
                logger.warning(f"[飞书DNS] 预热失败: {host}")

    async def get_user_access_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取user_access_token（多策略fallback）
        策略1: V2 OAuth + JSON
        策略2: V1 OIDC（需app_access_token）
        """
        # 策略1: V2 OAuth接口
        result = await self._try_v2_token(code)
        if result.get("success"):
            return result
        logger.warning(f"[飞书] 策略1(V2)失败: {result.get('error_detail')}")

        # 策略2: V1 OIDC接口
        result = await self._try_v1_oidc(code)
        if result.get("success"):
            return result
        logger.error(f"[飞书] 所有策略均失败: {result.get('error_detail')}")
        return result

    async def _try_v2_token(self, code: str) -> Dict[str, Any]:
        """V2 OAuth token交换（在线程池中同步执行，带重试）"""
        url = f"{self.BASE_URL}/authen/v2/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        logger.info(f"[飞书] V2 token交换: client_id={self.app_id}, code长度={len(code)}")
        try:
            resp = await asyncio.to_thread(_sync_http_post_with_retry, url, payload, None, 4)
            if "error" in resp:
                logger.error(f"[飞书] V2网络异常(重试{MAX_RETRIES}次均失败): {resp['error']}")
                return {"success": False, "error_detail": f"V2网络异常: {resp['error']}"}

            data = resp["data"]
            logger.info(f"[飞书] V2响应: HTTP {resp['http_status']}, code={data.get('code')}")

            if data.get("code") == 0 and "access_token" in data:
                logger.info("[飞书] V2换取user_access_token成功")
                return {"success": True, **data}
            else:
                detail = f"V2: feishu_code={data.get('code')}, error={data.get('error')}, desc={data.get('error_description', data.get('msg', ''))}"
                return {"success": False, "error_detail": detail}
        except Exception as e:
            logger.error(f"[飞书] V2异常: {traceback.format_exc()}")
            return {"success": False, "error_detail": f"V2异常: {type(e).__name__}: {e}"}

    async def _try_v1_oidc(self, code: str) -> Dict[str, Any]:
        """V1 OIDC token交换（需先获取app_access_token，带重试）"""
        # 获取app_access_token
        try:
            token_url = f"{self.BASE_URL}/auth/v3/app_access_token/internal"
            token_payload = {"app_id": self.app_id, "app_secret": self.app_secret}
            resp = await asyncio.to_thread(_sync_http_post_with_retry, token_url, token_payload, None, 4)
            if "error" in resp:
                return {"success": False, "error_detail": f"V1获取app_token网络异常: {resp['error']}"}
            token_data = resp["data"]
            if token_data.get("code") != 0:
                return {"success": False, "error_detail": f"V1获取app_token失败: {token_data.get('msg')}"}
            app_token = token_data.get("app_access_token")
            logger.info("[飞书] V1获取app_access_token成功")
        except Exception as e:
            return {"success": False, "error_detail": f"V1 app_token异常: {type(e).__name__}: {e}"}

        # 用code换取user_access_token
        url = f"{self.BASE_URL}/authen/v1/oidc/access_token"
        headers = {"Authorization": f"Bearer {app_token}"}
        payload = {"grant_type": "authorization_code", "code": code}
        logger.info(f"[飞书] V1 OIDC请求: url={url}")
        try:
            resp = await asyncio.to_thread(_sync_http_post_with_retry, url, payload, headers, 4)
            if "error" in resp:
                return {"success": False, "error_detail": f"V1 OIDC网络异常: {resp['error']}"}
            data = resp["data"]
            logger.info(f"[飞书] V1 OIDC响应: HTTP {resp['http_status']}, code={data.get('code')}")
            if data.get("code") == 0:
                token_info = data.get("data", {})
                if "access_token" in token_info:
                    return {"success": True, **token_info}
                return {"success": False, "error_detail": f"V1 OIDC无access_token: {data}"}
            else:
                return {"success": False, "error_detail": f"V1oidc: code={data.get('code')}, msg={data.get('msg')}"}
        except Exception as e:
            logger.error(f"[飞书] V1 OIDC异常: {traceback.format_exc()}")
            return {"success": False, "error_detail": f"V1oidc异常: {type(e).__name__}: {e}"}

    async def get_user_info(self, user_access_token: str) -> Optional[Dict[str, Any]]:
        """
        获取飞书登录用户信息（/authen/v1/user_info）
        注意：employee_no 字段需要应用具有 contact:user.employee_id:readonly 权限才会返回
        """
        url = f"{self.BASE_URL}/authen/v1/user_info"
        headers = {"Authorization": f"Bearer {user_access_token}"}
        try:
            resp = await asyncio.to_thread(_sync_http_get_with_retry, url, headers, 4)
            if "error" in resp:
                logger.error(f"[飞书] 获取用户信息网络异常: {resp['error']}")
                return None
            data = resp["data"]
            if data.get("code") == 0:
                user_info = data.get("data", {})
                logger.info(
                    f"[飞书] 获取用户信息成功: name={user_info.get('name')}, "
                    f"employee_no='{user_info.get('employee_no', '')}', "
                    f"mobile={user_info.get('mobile')}, "
                    f"open_id={user_info.get('open_id')}"
                )
                return user_info
            else:
                logger.error(f"[飞书] 获取用户信息失败: code={data.get('code')}, msg={data.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"[飞书] 获取用户信息异常: {e}")
            return None

    async def get_app_access_token(self) -> Optional[str]:
        """
        获取 app_access_token（tenant_access_token），用于调用通讯录等需要应用凭证的API
        """
        url = f"{self.BASE_URL}/auth/v3/app_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        try:
            resp = await asyncio.to_thread(_sync_http_post_with_retry, url, payload, None, 8)
            if "error" in resp:
                logger.error(f"[飞书] 获取app_access_token网络异常: {resp['error']}")
                return None
            data = resp["data"]
            if data.get("code") == 0:
                token = data.get("app_access_token") or data.get("tenant_access_token")
                logger.info("[飞书] 获取app_access_token成功")
                return token
            else:
                logger.error(f"[飞书] 获取app_access_token失败: code={data.get('code')}, msg={data.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"[飞书] 获取app_access_token异常: {e}")
            return None

    async def get_employee_no_by_contact_api(self, open_id: str, user_id: str = "") -> Optional[str]:
        """
        通过通讯录API（/contact/v3/users/{id}）获取用户工号
        当 /authen/v1/user_info 未返回 employee_no 时的备用方案
        需要应用具有 contact:user.employee_number:read 或 contact:user.employee:readonly 权限

        优先使用 user_id 查询（更精确），其次使用 open_id
        """
        app_token = await self.get_app_access_token()
        if not app_token:
            logger.warning("[飞书] 无法获取app_access_token，跳过通讯录API查询工号")
            return None

        # 优先用 user_id，其次 open_id
        if user_id:
            query_id = user_id
            id_type = "user_id"
        elif open_id:
            query_id = open_id
            id_type = "open_id"
        else:
            logger.warning("[飞书] 无可用ID，跳过通讯录API查询工号")
            return None

        url = f"{self.BASE_URL}/contact/v3/users/{query_id}?user_id_type={id_type}"
        headers = {"Authorization": f"Bearer {app_token}"}
        try:
            resp = await asyncio.to_thread(_sync_http_get_with_retry, url, headers, 4)
            if "error" in resp:
                logger.error(f"[飞书] 通讯录API获取用户信息网络异常: {resp['error']}")
                return None
            data = resp["data"]
            logger.info(
                f"[飞书] /contact/v3/users/{query_id} 响应: "
                f"code={data.get('code')}, msg={data.get('msg')}"
            )
            if data.get("code") == 0:
                contact_user = data.get("data", {}).get("user", {})
                employee_no = contact_user.get("employee_no", "")
                logger.info(
                    f"[飞书] 通讯录API返回: name={contact_user.get('name')}, "
                    f"employee_no='{employee_no}'"
                )
                return employee_no if employee_no else None
            else:
                logger.warning(
                    f"[飞书] 通讯录API查询失败: code={data.get('code')}, msg={data.get('msg')}，"
                    f"可能需要在飞书管理后台为应用添加 contact:user.employee:readonly 权限"
                )
                return None
        except Exception as e:
            logger.error(f"[飞书] 通讯录API异常: {e}")
            return None

    async def login_with_code(self, code: str) -> Dict[str, Any]:
        """
        完整飞书登录流程：code → user_access_token → 用户信息
        如果 user_info 中 employee_no 为空，尝试通过通讯录API获取
        """
        # Step 1: 换取token
        token_result = await self.get_user_access_token(code)
        if not token_result.get("success"):
            return token_result

        user_access_token = token_result.get("access_token")
        if not user_access_token:
            return {"success": False, "error_detail": "响应中无access_token字段"}

        # Step 2: 获取用户信息（/authen/v1/user_info）
        user_info = await self.get_user_info(user_access_token)
        if not user_info:
            return {"success": False, "error_detail": "获取飞书用户信息失败"}

        # Step 3: 如果 employee_no 为空，尝试通过通讯录API补充获取
        employee_no = user_info.get("employee_no", "")
        if not employee_no:
            logger.info("[飞书] user_info 未返回 employee_no，尝试通过通讯录API获取...")
            open_id = user_info.get("open_id", "")
            feishu_user_id = user_info.get("user_id", "")
            contact_employee_no = await self.get_employee_no_by_contact_api(open_id, feishu_user_id)
            if contact_employee_no:
                user_info["employee_no"] = contact_employee_no
                logger.info(f"[飞书] 通讯录API成功补充获取 employee_no='{contact_employee_no}'")
            else:
                logger.warning(
                    "[飞书] 通讯录API也未获取到 employee_no，将使用手机号作为工号。"
                    "请检查飞书管理后台是否已为应用开启以下任一权限："
                    "contact:user.employee_id:readonly / contact:user.employee:readonly / "
                    "contact:user.employee_number:read"
                )

        return {"success": True, **user_info}

    def get_login_config(self) -> Dict[str, Any]:
        """获取前端飞书登录配置"""
        return {
            "app_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "enabled": settings.FEISHU_ENABLED,
        }


# 全局飞书服务实例
feishu_service = FeishuService()
