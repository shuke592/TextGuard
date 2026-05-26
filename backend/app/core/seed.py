"""
TextGuard 数据库种子数据
初始化角色、权限、超级管理员账号
"""
import asyncio
from sqlalchemy import select
from loguru import logger

from app.core.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.global_word import GlobalWord
from app.models.llm_config import LLMConfig
from app.core.config import settings


# 权限种子数据：(编码, 名称, 类型, 父编码, 路径, 图标, 排序)
PERMISSION_SEED = [
    # === 用户端菜单 ===
    ("proofread", "文本校对", "menu", None, "/proofread/text", "Edit", 1),
    ("proofread:text", "文本校对", "menu", "proofread", "/proofread/text", "Edit", 1),
    ("proofread:document", "文档校对", "menu", "proofread", "/proofread/document", "Document", 2),
    ("proofread:export", "导出校对结果", "button", "proofread", None, None, 3),
    ("dictionary", "个性化词库", "menu", None, "/dictionary", "Collection", 2),
    ("dictionary:create", "创建词库", "button", "dictionary", None, None, 1),
    ("dictionary:edit", "编辑词库", "button", "dictionary", None, None, 2),
    ("dictionary:delete", "删除词库", "button", "dictionary", None, None, 3),
    ("dictionary:import", "导入词条", "button", "dictionary", None, None, 4),
    ("whitelist", "放行词管理", "menu", None, "/whitelist", "CircleCheck", 3),
    ("whitelist:create", "添加放行词", "button", "whitelist", None, None, 1),
    ("whitelist:edit", "编辑放行词", "button", "whitelist", None, None, 2),
    ("whitelist:delete", "删除放行词", "button", "whitelist", None, None, 3),
    ("history", "校对历史", "menu", None, "/history", "Clock", 4),
    ("history:view", "查看历史详情", "button", "history", None, None, 1),
    ("history:export", "导出历史记录", "button", "history", None, None, 2),

    # === 管理后台菜单 ===
    ("admin:access", "管理后台访问", "menu", None, "/admin", "Setting", 10),
    ("admin:dashboard", "仪表盘", "menu", "admin:access", "/admin/dashboard", "DataAnalysis", 1),
    ("admin:users", "用户管理", "menu", "admin:access", "/admin/users", "User", 2),
    ("admin:users:view", "查看用户", "button", "admin:users", None, None, 1),
    ("admin:users:create", "创建用户", "button", "admin:users", None, None, 2),
    ("admin:users:edit", "编辑用户", "button", "admin:users", None, None, 3),
    ("admin:users:delete", "删除用户", "button", "admin:users", None, None, 4),
    ("admin:roles", "角色权限", "menu", "admin:access", "/admin/roles", "Lock", 3),
    ("admin:roles:view", "查看角色", "button", "admin:roles", None, None, 1),
    ("admin:roles:create", "创建角色", "button", "admin:roles", None, None, 2),
    ("admin:roles:edit", "编辑角色", "button", "admin:roles", None, None, 3),
    ("admin:roles:delete", "删除角色", "button", "admin:roles", None, None, 4),
    ("admin:policy", "策略管理", "menu", "admin:access", "/admin/policy", "Setting", 4),
    ("admin:policy:edit", "编辑策略", "button", "admin:policy", None, None, 1),
    ("admin:llm", "大模型配置", "menu", "admin:access", "/admin/llm", "Cpu", 5),
    ("admin:llm:view", "查看配置", "button", "admin:llm", None, None, 1),
    ("admin:llm:edit", "编辑配置", "button", "admin:llm", None, None, 2),
    ("admin:global_dict", "全局词库", "menu", "admin:access", "/admin/global-dict", "Notebook", 6),
    ("admin:global_dict:edit", "编辑全局词库", "button", "admin:global_dict", None, None, 1),
    ("admin:documents", "文档管理", "menu", "admin:access", "/admin/documents", "Folder", 7),
    ("admin:documents:view", "查看文档", "button", "admin:documents", None, None, 1),
    ("admin:documents:delete", "删除文档", "button", "admin:documents", None, None, 2),
    ("admin:settings", "系统设置", "menu", "admin:access", "/admin/settings", "Tools", 8),
    ("admin:settings:edit", "编辑设置", "button", "admin:settings", None, None, 1),
]


async def seed_permissions(session):
    """初始化权限数据"""
    # 检查是否已有权限数据
    result = await session.execute(select(Permission).limit(1))
    if result.scalar_one_or_none():
        logger.info("权限数据已存在，跳过初始化")
        return

    # 第一遍：创建所有权限（不设父级）
    perm_map = {}
    for code, name, ptype, parent_code, path, icon, sort in PERMISSION_SEED:
        perm = Permission(
            name=name,
            code=code,
            type=ptype,
            path=path,
            icon=icon,
            sort_order=sort,
        )
        session.add(perm)
        await session.flush()
        perm_map[code] = perm.id

    # 第二遍：设置父级关系
    for code, _, _, parent_code, _, _, _ in PERMISSION_SEED:
        if parent_code and parent_code in perm_map:
            result = await session.execute(
                select(Permission).where(Permission.code == code)
            )
            perm = result.scalar_one()
            perm.parent_id = perm_map[parent_code]

    await session.flush()
    logger.info(f"权限数据初始化完成，共 {len(PERMISSION_SEED)} 条")
    return perm_map


async def seed_roles(session, perm_map):
    """初始化角色数据"""
    # 检查是否已有角色数据
    result = await session.execute(select(Role).limit(1))
    if result.scalar_one_or_none():
        logger.info("角色数据已存在，跳过初始化")
        # 返回已有的角色
        result = await session.execute(select(Role).where(Role.code == "super_admin"))
        admin_role = result.scalar_one_or_none()
        result2 = await session.execute(select(Role).where(Role.code == "user"))
        user_role = result2.scalar_one_or_none()
        return admin_role, user_role

    # 创建超级管理员角色
    admin_role = Role(
        name="超级管理员",
        code="super_admin",
        description="系统最高权限管理员，拥有所有权限",
        is_system=True,
        is_active=True,
        sort_order=0,
    )
    session.add(admin_role)

    # 创建普通用户角色
    user_role = Role(
        name="普通用户",
        code="user",
        description="普通用户，可使用校对功能",
        is_system=True,
        is_active=True,
        sort_order=10,
    )
    session.add(user_role)
    await session.flush()

    # 为普通用户角色分配基础权限
    user_perms = [
        "proofread", "proofread:text", "proofread:document", "proofread:export",
        "dictionary", "dictionary:create", "dictionary:edit", "dictionary:delete", "dictionary:import",
        "whitelist", "whitelist:create", "whitelist:edit", "whitelist:delete",
        "history", "history:view", "history:export",
    ]
    if perm_map:
        for perm_code in user_perms:
            if perm_code in perm_map:
                session.add(RolePermission(
                    role_id=user_role.id,
                    permission_id=perm_map[perm_code],
                ))

    await session.flush()
    logger.info("角色数据初始化完成: super_admin, user")
    return admin_role, user_role


async def seed_admin_user(session, admin_role):
    """初始化超级管理员账号"""
    result = await session.execute(
        select(User).where(User.employee_id == "admin")
    )
    if result.scalar_one_or_none():
        logger.info("管理员账号已存在，跳过初始化")
        return

    admin_user = User(
        employee_id="admin",
        username="系统管理员",
        password_hash=hash_password("admin123"),
        role_id=admin_role.id,
        is_active=True,
    )
    session.add(admin_user)
    await session.flush()
    logger.info("超级管理员账号创建完成: admin / admin123")


# ======================================================================
# 全局词库种子数据
# ======================================================================

# 全局敏感词（涉政/涉暴/涉恐/违法类，生产环境适用）
GLOBAL_SENSITIVE_WORDS = [
    # 涉政敏感
    ("颠覆国家政权", "sensitive", "政治", "error", "涉政敏感表述"),
    ("分裂国家", "sensitive", "政治", "error", "涉政敏感表述"),
    ("煽动叛乱", "sensitive", "政治", "error", "涉政敏感表述"),
    ("反党反社会", "sensitive", "政治", "error", "涉政敏感表述"),
    ("推翻政府", "sensitive", "政治", "error", "涉政敏感表述"),
    # 涉暴涉恐
    ("恐怖袭击", "sensitive", "暴恐", "error", "涉暴涉恐敏感表述"),
    ("制造爆炸", "sensitive", "暴恐", "error", "涉暴涉恐敏感表述"),
    ("暴力革命", "sensitive", "暴恐", "error", "涉暴涉恐敏感表述"),
    # 违法类
    ("贩卖毒品", "sensitive", "违法", "error", "违法犯罪敏感表述"),
    ("赌博网站", "sensitive", "违法", "error", "违法犯罪敏感表述"),
    ("洗钱", "sensitive", "违法", "error", "违法犯罪敏感表述"),
    ("非法集资", "sensitive", "违法", "error", "违法犯罪敏感表述"),
    ("传销", "sensitive", "违法", "error", "违法犯罪敏感表述"),
    # 涉黄
    ("色情服务", "sensitive", "涉黄", "error", "涉黄敏感表述"),
    ("淫秽物品", "sensitive", "涉黄", "error", "涉黄敏感表述"),
    # 歧视侮辱
    ("种族歧视", "sensitive", "歧视", "warning", "歧视性表述"),
    ("性别歧视", "sensitive", "歧视", "warning", "歧视性表述"),
    ("残疾歧视", "sensitive", "歧视", "warning", "歧视性表述"),
]

# 全局禁词（公文/正式文档中禁止出现的不规范用语）
GLOBAL_BANNED_WORDS = [
    ("他妈的", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("我靠", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("卧槽", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("牛逼", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("装逼", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("傻逼", "banned", "粗俗用语", "error", "粗俗用语，正式文档禁止使用"),
    ("脑残", "banned", "侮辱用语", "error", "侮辱性用语，正式文档禁止使用"),
    ("白痴", "banned", "侮辱用语", "warning", "侮辱性用语，正式文档慎用"),
    ("废物", "banned", "侮辱用语", "warning", "侮辱性用语，正式文档慎用"),
]

# 全局纠错词条（常见错别字/易混用词，word → replacement）
GLOBAL_CORRECTIONS = [
    # 常见错别字
    ("帐号", "账号", "correction", "常见错别字", "warning", "'帐'用于帐篷，'账'用于账户"),
    ("帐户", "账户", "correction", "常见错别字", "warning", "'帐'用于帐篷，'账'用于账户"),
    ("象样", "像样", "correction", "常见错别字", "warning", "表示'如同、好似'用'像'"),
    ("权力机关", "权力机关", "correction", "易混用", "info", "注意：'权力'指政治力量，'权利'指法律赋予的利益"),
    ("其它", "其他", "correction", "常见错别字", "info", "规范用法为'其他'，'其它'仅用于事物"),
    ("按装", "安装", "correction", "常见错别字", "warning", "正确用字为'安装'"),
    ("人材", "人才", "correction", "常见错别字", "warning", "正确用字为'人才'"),
    ("一但", "一旦", "correction", "常见错别字", "warning", "正确用字为'一旦'"),
    ("凑和", "凑合", "correction", "常见错别字", "warning", "正确用字为'凑合'"),
    ("决窍", "诀窍", "correction", "常见错别字", "warning", "正确用字为'诀窍'"),
    ("松驰", "松弛", "correction", "常见错别字", "warning", "正确用字为'松弛'"),
    ("好象", "好像", "correction", "常见错别字", "warning", "正确用字为'好像'"),
    ("侯车室", "候车室", "correction", "常见错别字", "warning", "'候'表示等候"),
    ("针贬", "针砭", "correction", "常见错别字", "warning", "正确用字为'针砭'"),
    ("蜡烛", "蜡烛", "correction", "易混用", "info", "注意：'腊'用于腊月、腊肉；'蜡'用于蜡烛"),
    ("反应意见", "反映意见", "correction", "易混用", "warning", "'反映'表示把情况告知，'反应'表示回应"),
    ("象征", "象征", "correction", "易混用", "info", "注意区分：'象征'正确，但'好象'应为'好像'"),
    ("急待", "亟待", "correction", "常见错别字", "warning", "表示'急迫需要'应用'亟待'"),
    ("挖墙角", "挖墙脚", "correction", "常见错别字", "warning", "正确用法为'挖墙脚'"),
    ("渡假", "度假", "correction", "常见错别字", "warning", "正确用字为'度假'"),
    ("竟然", "竟然", "correction", "易混用", "info", "注意：'竟然'表出乎意料，'竟'不可写作'竞'"),
    ("再接再励", "再接再厉", "correction", "常见错别字", "warning", "正确用字为'再接再厉'"),
    ("走头无路", "走投无路", "correction", "常见错别字", "warning", "正确成语为'走投无路'"),
    ("一愁莫展", "一筹莫展", "correction", "常见错别字", "warning", "正确成语为'一筹莫展'"),
    ("按步就班", "按部就班", "correction", "常见错别字", "warning", "正确成语为'按部就班'"),
    ("名符其实", "名副其实", "correction", "常见错别字", "warning", "正确成语为'名副其实'"),
    ("迫不急待", "迫不及待", "correction", "常见错别字", "warning", "正确成语为'迫不及待'"),
    ("委曲求全", "委曲求全", "correction", "易混用", "info", "'委曲'与'委屈'不同，此成语正确"),
    ("山青水秀", "山清水秀", "correction", "常见错别字", "warning", "正确成语为'山清水秀'"),
    ("金壁辉煌", "金碧辉煌", "correction", "常见错别字", "warning", "正确成语为'金碧辉煌'"),
    ("世外桃园", "世外桃源", "correction", "常见错别字", "warning", "正确成语为'世外桃源'"),
    ("脉膊", "脉搏", "correction", "常见错别字", "warning", "正确用字为'脉搏'"),
    ("做月子", "坐月子", "correction", "常见错别字", "warning", "正确用字为'坐月子'"),
    ("九州", "九州", "correction", "易混用", "info", "地名用'九州'，'洲'指大陆（如亚洲）"),
    # 公文常见错误
    ("制定规划", "制定规划", "correction", "公文用语", "info", "注意：'制订'侧重创制拟定，'制定'侧重决定不变"),
    ("其他地区", "其他地区", "correction", "公文用语", "info", "公文中统一使用'其他'，不用'其它'"),
    ("做出决定", "作出决定", "correction", "公文用语", "warning", "公文规范用法为'作出决定'"),
    ("做出贡献", "作出贡献", "correction", "公文用语", "warning", "公文规范用法为'作出贡献'"),
    ("做为", "作为", "correction", "公文用语", "warning", "规范用法为'作为'"),
    # 电力行业常见错别字
    ("变压气", "变压器", "correction", "电力术语", "warning", "电力行业术语纠错"),
    ("断路气", "断路器", "correction", "电力术语", "warning", "电力行业术语纠错"),
    ("互感气", "互感器", "correction", "电力术语", "warning", "电力行业术语纠错"),
    ("发电厂", "发电厂", "correction", "电力术语", "info", "注意区分：发电厂≠变电站≠配电站"),
    ("接地保护", "接地保护", "correction", "电力术语", "info", "注意区分：接地保护≠接零保护"),
]

# 全局放行词（不应被校对标记的专有名词、技术术语等）
GLOBAL_WHITELIST_WORDS = [
    # 技术术语
    ("API", "whitelist", "技术术语", "技术接口缩写，无需校对"),
    ("SDK", "whitelist", "技术术语", "软件开发工具包缩写"),
    ("SaaS", "whitelist", "技术术语", "软件即服务"),
    ("IoT", "whitelist", "技术术语", "物联网缩写"),
    ("AI", "whitelist", "技术术语", "人工智能缩写"),
    # 电力/新能源行业术语
    ("千瓦时", "whitelist", "电力术语", "电能计量单位"),
    ("kWh", "whitelist", "电力术语", "千瓦时缩写"),
    ("光伏", "whitelist", "新能源术语", "光伏发电"),
    ("风电", "whitelist", "新能源术语", "风力发电"),
    ("储能", "whitelist", "新能源术语", "能量存储"),
    ("电能表", "whitelist", "电力术语", "电能计量设备"),
    ("智能电表", "whitelist", "电力术语", "智能电能表"),
    ("互感器", "whitelist", "电力术语", "电力计量设备"),
    ("变压器", "whitelist", "电力术语", "电力输变电设备"),
    ("断路器", "whitelist", "电力术语", "电力保护设备"),
    ("继电器", "whitelist", "电力术语", "电力自动化设备"),
    ("配电网", "whitelist", "电力术语", "配电网络"),
    ("高压线", "whitelist", "电力术语", "高压输电线路"),
    ("低压线", "whitelist", "电力术语", "低压配电线路"),
    ("SCADA", "whitelist", "电力术语", "数据采集与监控系统"),
    ("DCS", "whitelist", "电力术语", "分布式控制系统"),
    # 公文常用术语
    ("人民政府", "whitelist", "公文术语", "政府机构名称"),
    ("国务院", "whitelist", "公文术语", "国家行政机关"),
    ("中共中央", "whitelist", "公文术语", "党中央"),
    ("政协", "whitelist", "公文术语", "政治协商会议缩写"),
    ("人大", "whitelist", "公文术语", "人民代表大会缩写"),
    # 法律常用术语
    ("民事诉讼", "whitelist", "法律术语", "法律程序术语"),
    ("刑事诉讼", "whitelist", "法律术语", "法律程序术语"),
    ("行政诉讼", "whitelist", "法律术语", "法律程序术语"),
    ("仲裁", "whitelist", "法律术语", "纠纷解决方式"),
    ("公证", "whitelist", "法律术语", "法律证明"),
    # 度量单位
    ("MW", "whitelist", "度量单位", "兆瓦"),
    ("GW", "whitelist", "度量单位", "吉瓦"),
    ("kV", "whitelist", "度量单位", "千伏"),
    ("kA", "whitelist", "度量单位", "千安"),
    ("MVA", "whitelist", "度量单位", "兆伏安"),
]


async def seed_global_words(session):
    """初始化全局词库数据"""
    result = await session.execute(select(GlobalWord).limit(1))
    if result.scalar_one_or_none():
        logger.info("全局词库数据已存在，跳过初始化")
        return

    count = 0

    # 敏感词
    for word, wtype, category, severity, remark in GLOBAL_SENSITIVE_WORDS:
        session.add(GlobalWord(
            word=word, type=wtype, category=category,
            severity=severity, remark=remark, is_active=True,
        ))
        count += 1

    # 禁词
    for word, wtype, category, severity, remark in GLOBAL_BANNED_WORDS:
        session.add(GlobalWord(
            word=word, type=wtype, category=category,
            severity=severity, remark=remark, is_active=True,
        ))
        count += 1

    # 纠错词条（word, replacement, type, category, severity, remark）
    for word, replacement, wtype, category, severity, remark in GLOBAL_CORRECTIONS:
        session.add(GlobalWord(
            word=word, type=wtype, replacement=replacement,
            category=category, severity=severity, remark=remark, is_active=True,
        ))
        count += 1

    # 放行词（word, type, category, remark）
    for word, wtype, category, remark in GLOBAL_WHITELIST_WORDS:
        session.add(GlobalWord(
            word=word, type=wtype, category=category,
            severity="info", remark=remark, is_active=True,
        ))
        count += 1

    await session.flush()
    logger.info(f"全局词库初始化完成，共 {count} 条")


async def seed_llm_configs(session):
    """初始化默认大模型配置"""
    result = await session.execute(select(LLMConfig).limit(1))
    if result.scalar_one_or_none():
        logger.info("大模型配置已存在，跳过初始化")
        return

    # 从 .env 读取 DeepSeek 配置作为默认
    deepseek_key = settings.DEEPSEEK_API_KEY
    if not deepseek_key or deepseek_key == "your-deepseek-api-key-here" or deepseek_key == "":
        deepseek_key = "请在管理后台配置你的API密钥"

    configs = [
        LLMConfig(
            name="DeepSeek",
            provider="deepseek",
            api_base=settings.DEEPSEEK_API_BASE or "https://api.deepseek.com",
            api_key=deepseek_key,
            model=settings.DEEPSEEK_MODEL or "deepseek-chat",
            temperature=0.3,
            timeout=60,
            max_retries=3,
            is_active=True,
            is_enabled=True,
            remark="默认配置，从 .env 导入",
        ),
    ]
    session.add_all(configs)
    await session.flush()
    logger.info(f"大模型配置初始化完成，共 {len(configs)} 条")


async def run_seed():
    """执行所有种子数据初始化"""
    logger.info("开始初始化种子数据...")
    await init_db()

    async with async_session_factory() as session:
        try:
            perm_map = await seed_permissions(session)
            admin_role, user_role = await seed_roles(session, perm_map)
            if admin_role:
                await seed_admin_user(session, admin_role)
            await seed_global_words(session)
            await seed_llm_configs(session)
            await session.commit()
            logger.info("种子数据初始化全部完成！")
        except Exception as e:
            await session.rollback()
            logger.error(f"种子数据初始化失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
