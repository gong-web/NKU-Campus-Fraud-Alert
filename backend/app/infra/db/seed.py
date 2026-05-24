"""种子数据：5 院系 + 角色 + 权限矩阵 + 测试账号。

执行：``python -m app.infra.db.seed`` 或 ``make seed``。

幂等：每条 INSERT 都先 SELECT 查重；脚本可重复执行。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.core.snowflake import next_snowflake_id
from app.infra.cache.rbac_cache import RBACCache
from app.infra.db.models import (
    Department,
    FraudType,
    KnowledgeEntry,
    Permission,
    QuestionBank,
    Quiz,
    QuizQuestion,
    Role,
    RolePermission,
    User,
)
from app.infra.db.models.knowledge_entry import (
    KnowledgeEntrySourceType,
    KnowledgeEntryStatus,
)
from app.infra.db.models.quiz import QuizScopeType, QuizStatus, QuizType
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.services import permissions as perm

logger = get_logger(__name__)


# ── 数据 ────────────────────────────────────────────────────────────
DEPARTMENTS: list[dict[str, str | int]] = [
    {"dept_code": "UNKNOWN", "dept_name": "未指定"},
    {"dept_code": "CS", "dept_name": "计算机学院", "sort_order": 1},
    {"dept_code": "MATH", "dept_name": "数学科学学院", "sort_order": 2},
    {"dept_code": "BUSI", "dept_name": "商学院", "sort_order": 3},
    {"dept_code": "FOREIGN", "dept_name": "外国语学院", "sort_order": 4},
    {"dept_code": "PHYS", "dept_name": "物理科学学院", "sort_order": 5},
]

ROLES: list[dict[str, str | int]] = [
    {"role_code": Role.CODE_STUDENT, "role_name": "学生", "role_level": 1},
    {"role_code": Role.CODE_REVIEWER, "role_name": "审核管理员（院系级）", "role_level": 1},
    {"role_code": Role.CODE_REVIEWER, "role_name": "审核管理员（校级）", "role_level": 2},
    {"role_code": Role.CODE_SYS_ADMIN, "role_name": "系统管理员", "role_level": 1},
]

# PRD UC-01：8 类诈骗类型（写入 SystemConfig 暂存；FraudType 表由业务模块负责人建）
FRAUD_TYPES: list[dict[str, str]] = [
    {"type_code": "BRUSH_REWARD", "type_name": "刷单返利类"},
    {"type_code": "FAKE_POLICE", "type_name": "冒充公检法类"},
    {"type_code": "FAKE_JOB", "type_name": "虚假兼职招聘类"},
    {"type_code": "DATING_FRAUD", "type_name": "恋爱交友诈骗类"},
    {"type_code": "FAKE_REFUND", "type_name": "冒充客服退款类"},
    {"type_code": "FAKE_LOAN", "type_name": "虚假网络贷款类"},
    {"type_code": "GAME_TRADE", "type_name": "游戏账号交易诈骗类"},
    {"type_code": "OTHER", "type_name": "其他类型"},
]

TEST_USERS: list[dict[str, str]] = [
    # SysAdmin
    {
        "cas_account": "sysadmin001",
        "real_name": "测试系统管理员",
        "role_code": "SYS_ADMIN",
        "dept_code": "UNKNOWN",
    },
    # Reviewer · 院系级
    {
        "cas_account": "reviewer_dept001",
        "real_name": "计院辅导员-王老师",
        "role_code": "REVIEWER",
        "dept_code": "CS",
    },
    # Reviewer · 校级
    {
        "cas_account": "reviewer_school001",
        "real_name": "保卫处李主任",
        "role_code": "REVIEWER_SCHOOL",
        "dept_code": "UNKNOWN",
    },
    # 学生
    {"cas_account": "student001", "real_name": "张三", "role_code": "STUDENT", "dept_code": "CS"},
    {"cas_account": "student002", "real_name": "李四", "role_code": "STUDENT", "dept_code": "MATH"},
    {"cas_account": "student003", "real_name": "王五", "role_code": "STUDENT", "dept_code": "BUSI"},
    {
        "cas_account": "student004",
        "real_name": "赵六",
        "role_code": "STUDENT",
        "dept_code": "FOREIGN",
    },
    {"cas_account": "student005", "real_name": "钱七", "role_code": "STUDENT", "dept_code": "PHYS"},
]


async def seed_all() -> None:  # noqa: C901 - seed 脚本按步骤串行更容易审计
    async with uow() as session:
        # 0. 诈骗类型字典（迁移已 bulk_insert，这里做幂等补全）
        for ft_data in FRAUD_TYPES:
            existing_ft = (
                await session.execute(
                    select(FraudType).where(FraudType.type_code == ft_data["type_code"])
                )
            ).scalar_one_or_none()
            if existing_ft is None:
                session.add(FraudType(**ft_data, sort_order=FRAUD_TYPES.index(ft_data) + 1))
        await session.flush()
        logger.info("seed_fraud_types_done")

        # 1. 院系
        for dept_data in DEPARTMENTS:
            existing_dept = (
                await session.execute(
                    select(Department).where(Department.dept_code == dept_data["dept_code"])
                )
            ).scalar_one_or_none()
            if existing_dept is None:
                session.add(Department(**dept_data))
        await session.flush()

        # 2. 角色
        for role_data in ROLES:
            existing_role = (
                await session.execute(
                    select(Role).where(
                        Role.role_code == role_data["role_code"],
                        Role.role_level == role_data["role_level"],
                    )
                )
            ).scalar_one_or_none()
            if existing_role is None:
                session.add(Role(**role_data))
        await session.flush()

        # 3. 权限码
        for code in sorted(perm.all_permission_codes()):
            existing = (
                await session.execute(select(Permission).where(Permission.permission_code == code))
            ).scalar_one_or_none()
            if existing is None:
                resource, action = code.split(":", 1)
                session.add(
                    Permission(
                        permission_code=code,
                        permission_name=code,  # 中文 PR 由后续补
                        resource_type=resource.upper(),
                        action_type=action.upper(),
                    )
                )
        await session.flush()

        # 4. 角色权限矩阵
        roles_by_code: dict[str, list[Role]] = {}
        for role_obj in (await session.execute(select(Role))).scalars():
            roles_by_code.setdefault(role_obj.role_code, []).append(role_obj)
        perms_by_code = {
            p.permission_code: p for p in (await session.execute(select(Permission))).scalars()
        }
        existing_pairs = {
            (rp.role_id, rp.permission_id)
            for rp in (await session.execute(select(RolePermission))).scalars()
        }
        for (role_code, role_level), codes in perm.ROLE_PERMISSIONS_DEFAULT.items():
            target_role = next(
                (r for r in roles_by_code.get(role_code, []) if r.role_level == role_level),
                None,
            )
            if target_role is None:
                continue
            for code in codes:
                p = perms_by_code.get(code)
                if p is None:
                    continue
                if (target_role.role_id, p.permission_id) in existing_pairs:
                    continue
                session.add(
                    RolePermission(
                        role_id=target_role.role_id,
                        permission_id=p.permission_id,
                    )
                )
        await session.flush()

        # 5. 测试账号
        student_role = next(
            (r for r in roles_by_code.get("STUDENT", []) if r.role_level == 1), None
        )
        reviewer_dept_role = next(
            (r for r in roles_by_code.get("REVIEWER", []) if r.role_level == 1), None
        )
        reviewer_school_role = next(
            (r for r in roles_by_code.get("REVIEWER", []) if r.role_level == 2), None
        )
        sysadmin_role = roles_by_code.get("SYS_ADMIN", [None])[0]

        depts_by_code = {
            d.dept_code: d for d in (await session.execute(select(Department))).scalars()
        }

        def role_for(code: str) -> Role | None:
            return {
                "STUDENT": student_role,
                "REVIEWER": reviewer_dept_role,
                "REVIEWER_SCHOOL": reviewer_school_role,
                "SYS_ADMIN": sysadmin_role,
            }.get(code)

        for user_data in TEST_USERS:
            existing_user = (
                await session.execute(
                    select(User).where(User.cas_account == user_data["cas_account"])
                )
            ).scalar_one_or_none()
            if existing_user is not None:
                continue
            role = role_for(user_data["role_code"])
            dept = depts_by_code.get(user_data["dept_code"])
            if role is None or dept is None:
                continue
            session.add(
                User(
                    user_id=next_snowflake_id(),
                    cas_account=user_data["cas_account"],
                    real_name=user_data["real_name"],
                    department_id=dept.dept_id,
                    role_id=role.role_id,
                    status=UserStatus.ACTIVE.value,
                )
            )
        await session.flush()
        logger.info("seed_users_done")

        # 7. 题库 + 一场示例指定测验（UC-05 / UC-09）
        await _seed_quiz_data(session)

    # 6. RBAC 缓存预热
    async with uow() as session:
        from app.infra.repositories.role import RoleRepository

        roles_repo = RoleRepository(session)
        mapping = await roles_repo.list_role_permissions_full()
    await RBACCache().load(mapping)
    logger.info("seed_done", departments=len(DEPARTMENTS), users=len(TEST_USERS))


# ── 题库种子（UC-05 / UC-09）───────────────────────────────────────
# 每条：题干、4 个选项、正确答案、解析、所属诈骗类型 type_code、难度
QUIZ_QUESTIONS: list[dict[str, object]] = [
    {
        "content": "陌生 QQ 群发来「兼职刷单、佣金日结」的链接，要求先垫付货款再返利。最稳妥的做法是？",
        "option_a": "先垫付小额试一单看看回款情况",
        "option_b": "直接拒绝并向辅导员 / 国家反诈中心举报",
        "option_c": "把链接转给同学一起讨论是否靠谱",
        "option_d": "找客服核实公司资质后再决定",
        "correct_answer": "B",
        "explanation": "刷单返利本身违法。一切「先垫付、再返利」的兼职都是诈骗模板，不论金额大小都不要尝试。",
        "fraud_type_code": "BRUSH_REWARD",
        "difficulty": 1,
    },
    {
        "content": "下列哪一项是「冒充公检法」诈骗的典型话术？",
        "option_a": "「你的快递丢失了，需要双倍赔偿」",
        "option_b": "「你的账户涉嫌洗钱，请把钱转到安全账户接受调查」",
        "option_c": "「你被某公司选中参加抽奖」",
        "option_d": "「你的医保卡需要重新激活」",
        "correct_answer": "B",
        "explanation": "真正的公检法机关从不通过电话要求当事人「转账到安全账户」。一旦听到「安全账户」四字，几乎可确认为诈骗。",
        "fraud_type_code": "FAKE_POLICE",
        "difficulty": 1,
    },
    {
        "content": "招聘启事写明「无需经验、日入 500+、只需打字 / 点赞」，最可能是？",
        "option_a": "正规兼职，待遇优厚",
        "option_b": "虚假兼职诈骗，目的是骗取保证金或个人信息",
        "option_c": "需要先入职试一试再判断",
        "option_d": "可能是培训机构的体验岗",
        "correct_answer": "B",
        "explanation": "高薪轻松、零门槛的兼职几乎都是诈骗。常见套路：交押金、买软件、垫资刷单。",
        "fraud_type_code": "FAKE_JOB",
        "difficulty": 1,
    },
    {
        "content": "网恋对象一直不见面，反复推荐你下载某「内部投资 / 博彩 App」，刚开始还小赚，要不要继续投？",
        "option_a": "继续投，已经赚回成本了",
        "option_b": "投资有风险，量力而行",
        "option_c": "立刻停止并截图保留证据，向反诈中心举报",
        "option_d": "把账号告诉家人帮忙操作",
        "correct_answer": "C",
        "explanation": "这是典型「杀猪盘」流程：先取得信任 → 小利诱导 → 大额加注 → 后台清零。涉及陌生 App 投资务必立即止损。",
        "fraud_type_code": "DATING_FRAUD",
        "difficulty": 2,
    },
    {
        "content": "「客服」打电话称你购买的某商品有质量问题，需要在指定链接「退款 + 三倍赔偿」，正确做法是？",
        "option_a": "立刻点击链接按指引填写银行卡信息",
        "option_b": "回到购物 App 官方订单页核实，绝不点开链接",
        "option_c": "告诉对方支付密码以便快速到账",
        "option_d": "打开屏幕共享方便客服协助操作",
        "correct_answer": "B",
        "explanation": "凡是引导跳出官方平台「退款 / 理赔」、要求开启屏幕共享或读验证码的，都是冒充客服诈骗。",
        "fraud_type_code": "FAKE_REFUND",
        "difficulty": 1,
    },
    {
        "content": "某网贷 App 声称「秒下款、无抵押」，但要先转 1000 元「解冻金」才能放款。这是？",
        "option_a": "正规放贷流程，先交手续费正常",
        "option_b": "虚假贷款诈骗，「解冻金 / 保证金」都是骗局",
        "option_c": "可以先借小额试试",
        "option_d": "把身份证照片发过去确认下",
        "correct_answer": "B",
        "explanation": "正规金融机构放款前绝不会收取「解冻金、保证金、刷流水」等费用。任何放款前先收钱的都是诈骗。",
        "fraud_type_code": "FAKE_LOAN",
        "difficulty": 1,
    },
    {
        "content": "在游戏交易平台之外，陌生人加你微信要「私下高价收号」，并发来一个「担保网站」截图，怎么办？",
        "option_a": "对方愿意先付定金就可以信",
        "option_b": "用对方提供的网站走「担保交易」",
        "option_c": "拒绝场外交易，只走官方平台，截图并举报",
        "option_d": "把账号密码告诉对方让他自己看",
        "correct_answer": "C",
        "explanation": "所谓「担保网站」99% 是钓鱼站，会在「资金冻结、需缴解冻费」等环节套钱。游戏账号交易务必走官方平台。",
        "fraud_type_code": "GAME_TRADE",
        "difficulty": 2,
    },
    {
        "content": "下列哪一种情况最应该警惕？",
        "option_a": "辅导员在班级群通知开会",
        "option_b": "陌生人来电自称「公安」「检察官」并要求转账",
        "option_c": "京东客服在 App 内回复你的售后咨询",
        "option_d": "学校官网发布的奖学金公示",
        "correct_answer": "B",
        "explanation": "所有「执法人员」要求电话内转账的场景都是诈骗。请立即挂断并拨打 110 或 96110 核实。",
        "fraud_type_code": "FAKE_POLICE",
        "difficulty": 1,
    },
    {
        "content": "在校园里发现疑似诈骗信息，最有效的处置方式是？",
        "option_a": "在朋友圈转发提醒大家",
        "option_b": "直接和对方对线套话",
        "option_c": "通过校园反诈平台「一键上报」并截图留证",
        "option_d": "不予理睬，与己无关",
        "correct_answer": "C",
        "explanation": "及时上报既能保护自己也能预警他人。校园反诈平台支持匿名上报，反应越早处置越快。",
        "fraud_type_code": "OTHER",
        "difficulty": 1,
    },
    {
        "content": "下列说法中，哪一项最不可能是真的？",
        "option_a": "凡是要求开启屏幕共享 + 输入验证码的，几乎都是诈骗",
        "option_b": "凡是「内幕消息 + 稳赚不赔」的投资群，几乎都是骗局",
        "option_c": "凡是要求把钱转入「国家安全账户」的，都是诈骗",
        "option_d": "凡是说话好听的陌生人都值得信任",
        "correct_answer": "D",
        "explanation": "三个「凡是」是反诈口诀。「话术好听」反而是社工诈骗最常见的开场。",
        "fraud_type_code": "OTHER",
        "difficulty": 1,
    },
    {
        "content": "收到 95XXX 开头的「客服」短信，称你京东白条 / 助学贷款逾期，附带退订 / 处理链接，应当？",
        "option_a": "立即点击链接处理避免影响征信",
        "option_b": "回拨短信里的号码核实",
        "option_c": "登录官方 App 自查，不点短信内链接",
        "option_d": "把短信删除当作没看见",
        "correct_answer": "C",
        "explanation": "短信链接是钓鱼站的高发渠道；任何「征信、逾期、注销学生贷款」的提示都应回到官方 App 核对。",
        "fraud_type_code": "FAKE_LOAN",
        "difficulty": 2,
    },
    {
        "content": "下列哪一种「兼职」最有可能是洗钱通道？",
        "option_a": "饭堂帮厨小时工",
        "option_b": "图书馆助管",
        "option_c": "出借银行卡 / U 盾给「老板」走流水",
        "option_d": "校内家教",
        "correct_answer": "C",
        "explanation": "把自己的银行卡 / 微信 / 支付宝借给陌生人收转账，属于「帮信罪」高发行为，可能承担刑事责任。",
        "fraud_type_code": "BRUSH_REWARD",
        "difficulty": 2,
    },
    {
        "content": "接到自称「平台客服」来电，称你误开通某付费服务需立即取消，否则每月自动扣费。对方要求你提供短信验证码。应该？",
        "option_a": "按对方要求提供验证码尽快取消",
        "option_b": "回到官方 App/官网自行查询订阅并处理，不提供验证码",
        "option_c": "开启屏幕共享让对方远程帮你操作",
        "option_d": "把银行卡号发给对方核对身份",
        "correct_answer": "B",
        "explanation": "取消订阅只在官方渠道操作。验证码/屏幕共享一旦交出，就可能被用于盗刷或远程转账。",
        "fraud_type_code": "FAKE_REFUND",
        "difficulty": 1,
    },
    {
        "content": "陌生人以「助学金/奖学金发放」为由添加你好友，称需要你先缴纳手续费或保证金。最正确的做法是？",
        "option_a": "金额不大，先交了再说",
        "option_b": "让对方提供更多材料再决定",
        "option_c": "通过学校官方渠道核实并拒绝任何转账要求",
        "option_d": "把个人信息先发过去登记",
        "correct_answer": "C",
        "explanation": "奖助学金不会以个人名义让学生转账。凡是先交钱、要验证码、要银行卡信息的都高度可疑。",
        "fraud_type_code": "OTHER",
        "difficulty": 1,
    },
    {
        "content": "有人在群里分享「内部投资群」截图，号称老师带单稳赚，要求先下载 App 并充值。应当？",
        "option_a": "先小额充值试试",
        "option_b": "观望一段时间再加入",
        "option_c": "拒绝加入并提醒同学，必要时举报",
        "option_d": "把链接转发给家人一起研究",
        "correct_answer": "C",
        "explanation": "以群聊、老师带单、内幕渠道为噱头的投资几乎都是诈骗。不要下载陌生 App 或向个人账户转账。",
        "fraud_type_code": "OTHER",
        "difficulty": 2,
    },
]


# ── 知识库种子（UC-04 / UC-08）─────────────────────────────────────
# 每个诈骗类型至少一条 PUBLISHED 条目，用于题库 ``knowledge_entry_id`` 关联。
KB_ENTRIES: list[dict[str, str]] = [
    {
        "fraud_type_code": "BRUSH_REWARD",
        "title": "刷单返利类诈骗识别与防范",
        "desensitized_summary": (
            "诈骗分子在 QQ 群、微信群、招聘平台发布「日结高薪、足不出户、动动手指」的兼职信息，"
            "受害人完成首笔小额任务后会收到佣金返还（建立信任），随后被诱导垫付更大额「连环单」，"
            "平台以「任务未完成」「卡单」「需充值激活」等借口拒绝提现，最终卷款跑路。"
        ),
        "identification_points": (
            "1. 「先垫付货款、完成任务后返利」是核心诈骗模板；\n"
            "2. 任何要求在非官方网站 / App 充值、转账的「兼职」均高度可疑；\n"
            "3. 「连环单」「任务组」「卡单需追加」是诱导大额垫资的常见话术；\n"
            "4. 出借个人银行卡 / 微信账户走流水可能涉嫌「帮信罪」。"
        ),
        "prevention_advice": (
            "凡是「先垫付再返利」的兼职都是诈骗，不论金额大小都不要尝试；"
            "正规兼职不会要求转账或提供银行卡密码；"
            "发现可疑信息请截图保留证据并通过校园反诈平台一键上报，或拨打 96110 全国反诈专线。"
        ),
        "peak_periods": "开学季、节假日、寒暑假",
    },
    {
        "fraud_type_code": "FAKE_POLICE",
        "title": "冒充公检法类诈骗识别与防范",
        "desensitized_summary": (
            "受害人接到自称「公安」「检察院」「法院」「社保局」工作人员的电话，被告知其身份信息"
            "涉嫌洗钱 / 拐卖 / 偷渡 / 通缉案件，需配合调查并将资金转入「安全账户」自证清白。"
            "对方往往能准确报出受害人的姓名、身份证号等信息，加之录像 / 视频笔录的高压氛围，"
            "使受害人在惊慌失措中完成转账。"
        ),
        "identification_points": (
            "1. 真正的公检法机关从不通过电话办案，更不会要求转账到「安全账户」；\n"
            "2. 「安全账户」「资金清查」「保密办案」均为典型骗局话术；\n"
            "3. 要求下载特殊 App、开启屏幕共享、提供短信验证码的，几乎全是诈骗；\n"
            "4. 警官证、逮捕令通过网络发送的，100% 是伪造的。"
        ),
        "prevention_advice": (
            "立即挂断电话，拨打 110 或 96110 核实；"
            "公检法办案均为线下当面调查，绝不会通过电话 / 视频要求转账；"
            "若已转账，立即报警并保留对方电话、转账记录、聊天截图等证据。"
        ),
        "peak_periods": "全年高发，开学季尤甚",
    },
    {
        "fraud_type_code": "FAKE_JOB",
        "title": "虚假兼职招聘类诈骗识别与防范",
        "desensitized_summary": (
            "诈骗分子伪造企业资质、夸大薪资待遇，以「打字员」「点赞员」「快递理货」「线上客服」等"
            "低门槛岗位吸引学生应聘。一旦应聘者表达兴趣，便以「保证金」「服装费」「培训费」"
            "「软件激活费」等名目收取费用，或诱导其参与刷单 / 洗钱等违法活动。"
        ),
        "identification_points": (
            "1. 「无需经验、日入 500+、轻松点赞」的招聘几乎都是诈骗；\n"
            "2. 入职前要求缴纳保证金、培训费、押金的均为骗局（正规企业违法）；\n"
            "3. 要求提供身份证、银行卡照片或验证码的，是个人信息盗用前兆；\n"
            "4. 「兼职刷单」「拉人头返利」属于刑法规定的违法行为。"
        ),
        "prevention_advice": (
            "通过学校就业指导中心、官方招聘平台寻找正规兼职；"
            "应聘前在「企查查」「天眼查」核实企业资质；"
            "凡要求先付钱的兼职一律拒绝；遇到可疑信息及时上报并保留证据。"
        ),
        "peak_periods": "开学季、毕业季、暑期",
    },
    {
        "fraud_type_code": "DATING_FRAUD",
        "title": "恋爱交友诈骗类（杀猪盘）识别与防范",
        "desensitized_summary": (
            "诈骗分子通过社交软件 / 婚恋平台主动添加好友，长时间嘘寒问暖、塑造「高富帅 / 白富美」人设"
            "取得信任。建立「恋爱关系」后，引导受害人下载所谓「内部投资」「博彩」App，初期允许小额"
            "盈利提现，待受害人大额投入后即关闭后台、卷款跑路。该套路俗称「杀猪盘」。"
        ),
        "identification_points": (
            "1. 网恋对象始终不愿见面、不愿视频，或只发美颜过度的「自拍」；\n"
            "2. 对方反复推荐你下载「内部投资 / 博彩 / 数字货币」App；\n"
            "3. 初期小额投资能盈利提现（养鱼期），随后引导加大投入；\n"
            "4. 「特殊渠道」「内部漏洞」「稳赚不赔」是典型诱导话术。"
        ),
        "prevention_advice": (
            "网恋务必先视频确认对方身份，长期不见面的「恋人」高度可疑；"
            "凡是引导投资 / 博彩的「恋人」均为骗子，立刻拉黑止损并报警；"
            "切勿将存款、借款、家长积蓄投入陌生 App；及时向辅导员或反诈中心求助。"
        ),
        "peak_periods": "节假日、情人节、单身节",
    },
    {
        "fraud_type_code": "FAKE_REFUND",
        "title": "冒充客服退款类诈骗识别与防范",
        "desensitized_summary": (
            "诈骗分子冒充淘宝 / 京东 / 顺丰等平台客服，以「商品质量问题需退款赔偿」「快递丢失双倍赔付」"
            "「会员到期需注销」等借口联系受害人，诱导其点击钓鱼链接、开启屏幕共享或提供短信验证码，"
            "最终通过远程操作或诱导转账盗刷受害人账户资金。"
        ),
        "identification_points": (
            "1. 主动联系并提供「三倍赔偿」「自动注销」等剧情的几乎全是诈骗；\n"
            "2. 要求开启屏幕共享（钉钉 / 腾讯会议）的「客服」一定是骗子；\n"
            "3. 短信验证码、支付密码绝不能告知任何「客服」；\n"
            "4. 跳出官方 App、用陌生链接处理退款的均不可信。"
        ),
        "prevention_advice": (
            "退款 / 售后只在购物 App 官方订单页面操作；"
            "任何「客服」要求开启屏幕共享、读取验证码、转账到「核对账户」的都是骗子；"
            "怀疑被骗时立刻关闭屏幕共享、冻结银行卡并拨打 110。"
        ),
        "peak_periods": "618、双 11、年货节等购物节后",
    },
    {
        "fraud_type_code": "FAKE_LOAN",
        "title": "虚假网络贷款类诈骗识别与防范",
        "desensitized_summary": (
            "诈骗分子伪造网贷 App、电话推销「低息秒下款、无抵押无征信」的贷款产品，"
            "在受害人申请贷款后，以「解冻金」「保证金」「刷流水」「修改征信」等名义要求先转账，"
            "钱款到账后立即拉黑或继续以新名目骗取更多费用。"
        ),
        "identification_points": (
            "1. 正规金融机构放款前绝不会收取任何费用；\n"
            "2. 「解冻金、保证金、流水费、征信修复费」均为诈骗术语；\n"
            "3. 通过短信链接、QQ 群、陌生 App 推广的「贷款」高度可疑；\n"
            "4. 学生身份本就难以通过大额商业贷款，「秒下款」是明显异常。"
        ),
        "prevention_advice": (
            "通过银行官方网点 / App 办理贷款，拒绝陌生网贷推销；"
            "凡是放款前先收钱的都是诈骗；不要将身份证、银行卡照片发送给任何陌生人；"
            "保护好个人征信，遇到可疑放贷立刻挂断 / 删除 / 举报。"
        ),
        "peak_periods": "开学季、缴费季、双 11 前后",
    },
    {
        "fraud_type_code": "GAME_TRADE",
        "title": "游戏账号交易诈骗识别与防范",
        "desensitized_summary": (
            "诈骗分子在游戏内或社交平台联系玩家，以「高价收号」「线下交易」「担保网站」等噱头"
            "吸引玩家场外交易。常见套路包括：发送钓鱼链接窃取账号；伪造「担保网站」以「资金冻结」"
            "「需要解冻金」骗钱；先取得账号后申诉找回原账号；以「保证金」为名套取转账。"
        ),
        "identification_points": (
            "1. 任何场外交易（脱离游戏官方平台）都是高风险行为；\n"
            "2. 「担保网站」99% 是钓鱼站，会以各种理由要求转账解冻；\n"
            "3. 在 QQ / 微信加价收号的「土豪」绝大多数是骗子；\n"
            "4. 提前发账号密码、提前转账定金都是单方面信任。"
        ),
        "prevention_advice": (
            "游戏账号交易务必走官方平台（如腾讯藏宝阁、网易藏宝阁）；"
            "拒绝场外交易、拒绝陌生「担保网站」、拒绝先发账号 / 先转账；"
            "保留聊天截图与对方账号，遇可疑情况及时上报并联系游戏官方客服。"
        ),
        "peak_periods": "寒暑假、节假日",
    },
    {
        "fraud_type_code": "OTHER",
        "title": "校园反诈通用识别要点与处置流程",
        "desensitized_summary": (
            "除了已列举的常见类型，校园中还存在「冒充辅导员收费」「虚假奖学金 / 助学金」"
            "「校园贷套路」「火车票退改签」「快递异常理赔」等多种新型诈骗。"
            "其共同特征是：制造紧张焦虑情绪、引导脱离常规沟通渠道、要求快速转账。"
        ),
        "identification_points": (
            "1. 凡是要求开启屏幕共享 + 输入验证码的，几乎都是诈骗；\n"
            "2. 凡是「内幕消息 + 稳赚不赔」的投资群，几乎都是骗局；\n"
            "3. 凡是要求把钱转入「国家安全账户 / 安全账户」的，都是诈骗；\n"
            "4. 凡是制造时间压力（「不立刻处理就严重后果」）的，都要先冷静核实。"
        ),
        "prevention_advice": (
            "牢记反诈三句话：不轻信、不转账、不点链接；"
            "遇到可疑情况立即挂断 / 退群 / 截图，并拨打 96110 全国反诈专线核实；"
            "通过校园反诈平台一键上报，平台支持匿名上报，反应越早处置越快。"
        ),
        "peak_periods": "全年常态",
    },
]


async def _seed_knowledge_entries(  # type: ignore[no-untyped-def]
    session, *, sysadmin, fraud_types_by_code
) -> dict[str, KnowledgeEntry]:
    """灌入示例知识库条目（每类一条 PUBLISHED）。

    幂等：按 ``title`` 查重；返回 ``fraud_type_code → KnowledgeEntry`` 映射，
    供题库种子调用方设置 ``question_bank.knowledge_entry_id``。
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    out: dict[str, KnowledgeEntry] = {}
    inserted = 0
    for kb in KB_ENTRIES:
        ft = fraud_types_by_code.get(kb["fraud_type_code"])
        if ft is None:
            continue
        existing = (
            await session.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.title == kb["title"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            out[kb["fraud_type_code"]] = existing
            continue
        entry = KnowledgeEntry(
            entry_id=next_snowflake_id(),
            title=kb["title"],
            fraud_type_id=ft.type_id,
            desensitized_summary=kb["desensitized_summary"],
            identification_points=kb["identification_points"],
            prevention_advice=kb["prevention_advice"],
            peak_periods=kb.get("peak_periods"),
            source_type=KnowledgeEntrySourceType.SCHOOL,
            source_reference="校园反诈平台官方整理",
            status=KnowledgeEntryStatus.PUBLISHED,
            version=1,
            author_id=sysadmin.user_id,
            reviewer_id=sysadmin.user_id,
            published_at=now,
        )
        session.add(entry)
        out[kb["fraud_type_code"]] = entry
        inserted += 1
    await session.flush()
    logger.info("seed_knowledge_entries_done", inserted=inserted)
    return out


async def _seed_quiz_data(session) -> None:  # type: ignore[no-untyped-def]
    """灌入示例知识库 + 题库 + 一场面向全校的示例指定测验。

    幂等：知识库按 ``title`` 查重，题目按题干文本查重，指定测验按 ``title`` 查重。
    每道题按 ``fraud_type_code`` 关联到同类型的知识库条目（用于答错时跳转学习）。
    """
    sysadmin = (
        await session.execute(select(User).where(User.cas_account == "sysadmin001"))
    ).scalar_one_or_none()
    if sysadmin is None:
        logger.warning("seed_quiz_skip_no_sysadmin")
        return

    fraud_types_by_code = {
        ft.type_code: ft for ft in (await session.execute(select(FraudType))).scalars()
    }

    # 先灌入知识库条目（每个诈骗类型一条），用于题目错误推送
    kb_by_fraud_code = await _seed_knowledge_entries(
        session, sysadmin=sysadmin, fraud_types_by_code=fraud_types_by_code
    )

    inserted_questions = 0
    for q in QUIZ_QUESTIONS:
        existing = (
            await session.execute(
                select(QuestionBank).where(QuestionBank.content == q["content"])
            )
        ).scalar_one_or_none()
        ft_code = str(q["fraud_type_code"])
        ft = fraud_types_by_code.get(ft_code)
        kb_entry = kb_by_fraud_code.get(ft_code)
        if existing is not None:
            # 已有题目：补齐缺失的 knowledge_entry_id 关联（幂等回填）
            if existing.knowledge_entry_id is None and kb_entry is not None:
                existing.knowledge_entry_id = kb_entry.entry_id
            continue
        session.add(
            QuestionBank(
                question_id=next_snowflake_id(),
                content=q["content"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                fraud_type_id=ft.type_id if ft is not None else None,
                knowledge_entry_id=kb_entry.entry_id if kb_entry is not None else None,
                difficulty=q["difficulty"],
                is_active=1,
                created_by=sysadmin.user_id,
            )
        )
        inserted_questions += 1
    await session.flush()
    logger.info("seed_question_bank_done", inserted=inserted_questions)

    # 示例指定测验（全校 · 截止时间 +14 天）
    sample_title = "新生反诈意识基线测验"
    existing_quiz = (
        await session.execute(select(Quiz).where(Quiz.title == sample_title))
    ).scalar_one_or_none()
    if existing_quiz is None:
        all_questions = (
            (await session.execute(select(QuestionBank).where(QuestionBank.is_active == 1)))
            .scalars()
            .all()
        )
        if len(all_questions) >= 10:
            quiz = Quiz(
                quiz_id=next_snowflake_id(),
                quiz_type=QuizType.ASSIGNED,
                title=sample_title,
                question_count=10,
                pass_score=60,
                status=QuizStatus.ACTIVE,
                created_by=sysadmin.user_id,
                deadline_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=14),
                target_scope={"type": QuizScopeType.ALL},
            )
            session.add(quiz)
            await session.flush()
            for idx, q in enumerate(all_questions[:10], start=1):
                session.add(
                    QuizQuestion(
                        quiz_id=quiz.quiz_id,
                        question_id=q.question_id,
                        sort_order=idx,
                    )
                )
            await session.flush()
            logger.info("seed_sample_quiz_done", quiz_id=quiz.quiz_id)

    # 学校发布的期中测验（面向学院 ID 2、4）
    midterm_title = "学校期中反诈意识测验"
    existing_midterm = (
        await session.execute(select(Quiz).where(Quiz.title == midterm_title))
    ).scalar_one_or_none()
    if existing_midterm is None:
        all_questions = (
            (await session.execute(select(QuestionBank).where(QuestionBank.is_active == 1)))
            .scalars()
            .all()
        )
        if len(all_questions) >= 10:
            midterm_quiz = Quiz(
                quiz_id=next_snowflake_id(),
                quiz_type=QuizType.ASSIGNED,
                title=midterm_title,
                question_count=10,
                pass_score=60,
                status=QuizStatus.ACTIVE,
                created_by=sysadmin.user_id,
                deadline_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=30),
                target_scope={"type": QuizScopeType.DEPARTMENT, "department_ids": [2, 4]},
                publish_level=2,  # 学校级发布
            )
            session.add(midterm_quiz)
            await session.flush()
            for idx, q in enumerate(all_questions[:10], start=1):
                session.add(
                    QuizQuestion(
                        quiz_id=midterm_quiz.quiz_id,
                        question_id=q.question_id,
                        sort_order=idx,
                    )
                )
            await session.flush()
            logger.info("seed_midterm_quiz_done", quiz_id=midterm_quiz.quiz_id)

    # 计算机学院发布的期末测验（面向计算机学院）
    cs_final_title = "计算机学院期末反诈测验"
    existing_cs_final = (
        await session.execute(select(Quiz).where(Quiz.title == cs_final_title))
    ).scalar_one_or_none()
    if existing_cs_final is None:
        cs_reviewer = (
            await session.execute(
                select(User).where(User.cas_account == "reviewer_dept001")
            )
        ).scalar_one_or_none()
        cs_dept = (
            await session.execute(
                select(Department).where(Department.dept_code == "CS")
            )
        ).scalar_one_or_none()
        all_questions = (
            (await session.execute(select(QuestionBank).where(QuestionBank.is_active == 1)))
            .scalars()
            .all()
        )
        if cs_reviewer is not None and cs_dept is not None and len(all_questions) >= 10:
            cs_final_quiz = Quiz(
                quiz_id=next_snowflake_id(),
                quiz_type=QuizType.ASSIGNED,
                title=cs_final_title,
                question_count=10,
                pass_score=60,
                status=QuizStatus.ACTIVE,
                created_by=cs_reviewer.user_id,
                deadline_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=30),
                target_scope={"type": QuizScopeType.DEPARTMENT, "department_ids": [cs_dept.dept_id]},
                publish_level=1,  # 院级发布，学校级审核员不可见
            )
            session.add(cs_final_quiz)
            await session.flush()
            for idx, q in enumerate(all_questions[:10], start=1):
                session.add(
                    QuizQuestion(
                        quiz_id=cs_final_quiz.quiz_id,
                        question_id=q.question_id,
                        sort_order=idx,
                    )
                )
            await session.flush()
            logger.info("seed_cs_final_quiz_done", quiz_id=cs_final_quiz.quiz_id)


async def _main() -> None:
    configure_logging(level="INFO")
    await seed_all()


if __name__ == "__main__":
    asyncio.run(_main())