"""Idempotent demo fixtures for the four-role presentation flow."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import encrypt_field
from app.core.snowflake import next_snowflake_id
from app.infra.db.models import (
    CaseAnonymousReporter,
    CaseStatusHistory,
    Department,
    FraudCase,
    FraudType,
    KnowledgeEntry,
    KnowledgeEntryHistory,
    Notification,
    QuestionBank,
    Quiz,
    QuizAttempt,
    QuizAttemptAnswer,
    QuizQuestion,
    ReportDraft,
    User,
    WarningNotice,
    WarningTarget,
)
from app.infra.db.models.fraud_case import CaseStatus
from app.infra.db.models.knowledge_entry import (
    KnowledgeEntrySourceType,
    KnowledgeEntryStatus,
)
from app.infra.db.models.knowledge_entry_history import KnowledgeEntryHistoryAction
from app.infra.db.models.quiz import QuizScopeType, QuizStatus, QuizType
from app.infra.db.models.quiz_attempt import QuizAttemptStatus
from app.infra.db.models.warning_notice import (
    WarningLevel,
    WarningPushScope,
    WarningStatus,
)

logger = get_logger(__name__)

DEMO_ID_BASE = 990_000_000_000_000_000


class DemoReportFixture(TypedDict):
    case_id: int
    case_no: str
    title: str
    description: str
    fraud_type_code: str
    incident_days_ago: int
    created_days_ago: int
    amount: Decimal | None
    fraud_method: str
    status: str
    reporter: User
    is_anonymous: bool


class DemoWarningFixture(TypedDict):
    title: str
    content: str
    level: int
    publisher: User
    scope: str
    status: str
    related_case_no: str
    appendix: str | None
    dept_codes: list[str]
    days_ago: int


class DemoKnowledgeFixture(TypedDict):
    title: str
    status: str
    fraud_type_code: str
    reviewer_id: int | None
    review_note: str | None


async def seed_demo_data(session: AsyncSession) -> None:
    """Seed presentation-ready records without duplicating them on rerun."""

    users = {
        user.cas_account: user
        for user in (
            await session.execute(
                select(User).where(
                    User.cas_account.in_(
                        [
                            "student001",
                            "student002",
                            "student003",
                            "reviewer_dept001",
                            "reviewer_school001",
                            "sysadmin001",
                        ]
                    )
                )
            )
        ).scalars()
    }
    fraud_types = {
        item.type_code: item for item in (await session.execute(select(FraudType))).scalars()
    }
    departments = {
        item.dept_code: item for item in (await session.execute(select(Department))).scalars()
    }

    required_users = {
        "student001",
        "student002",
        "reviewer_dept001",
        "reviewer_school001",
        "sysadmin001",
    }
    if not required_users.issubset(users):
        logger.warning("seed_demo_skip_missing_users")
        return

    _prefill_demo_profiles(users)
    await _seed_demo_reports(session, users=users, fraud_types=fraud_types)
    await _seed_demo_draft(session, users=users, fraud_types=fraud_types)
    await _seed_demo_warnings(
        session,
        users=users,
        departments=departments,
    )
    await _seed_demo_knowledge(session, users=users, fraud_types=fraud_types)
    await _seed_demo_quiz_history(session, users=users)
    await _seed_demo_notifications(session, users=users)
    await session.flush()
    logger.info("seed_demo_data_done")


def _prefill_demo_profiles(users: dict[str, User]) -> None:
    student = users["student001"]
    if student.phone_encrypted is None:
        student.phone_encrypted = "13800138000"
    if student.email_encrypted is None:
        student.email_encrypted = "student001@nankai.edu.cn"

    reviewer = users["reviewer_dept001"]
    if reviewer.phone_encrypted is None:
        reviewer.phone_encrypted = "13900139000"
    if reviewer.email_encrypted is None:
        reviewer.email_encrypted = "reviewer_dept001@nankai.edu.cn"


async def _seed_demo_reports(
    session: AsyncSession,
    *,
    users: dict[str, User],
    fraud_types: dict[str, FraudType],
) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    student = users["student001"]
    math_student = users["student002"]
    reviewer = users["reviewer_dept001"]

    fixtures: list[DemoReportFixture] = [
        {
            "case_id": DEMO_ID_BASE + 1,
            "case_no": "2026-CS-900001",
            "title": "【演示待审核】冒充客服退款诱导屏幕共享",
            "description": (
                "来电者自称电商客服，准确说出订单信息，以商品召回和三倍退款为由，"
                "要求下载会议软件并开启屏幕共享。本人发现验证码页面异常后立即退出。"
            ),
            "fraud_type_code": "FAKE_REFUND",
            "incident_days_ago": 0,
            "created_days_ago": 0,
            "amount": Decimal("3980.00"),
            "fraud_method": "冒充平台客服，诱导开启屏幕共享并索取验证码",
            "status": CaseStatus.PENDING,
            "reporter": student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 2,
            "case_no": "2026-MATH-900001",
            "title": "【演示校级待办】虚假助学金缴费通知",
            "description": (
                "陌生账号冒充学校资助中心工作人员，称助学金需要先缴纳认证费，"
                "并发送非学校域名的登记链接，要求填写身份证和银行卡信息。"
            ),
            "fraud_type_code": "OTHER",
            "incident_days_ago": 1,
            "created_days_ago": 1,
            "amount": Decimal("500.00"),
            "fraud_method": "冒充学校部门，以助学金认证为由收取费用",
            "status": CaseStatus.PENDING,
            "reporter": math_student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 3,
            "case_no": "2026-CS-900003",
            "title": "【演示待处理】刷单返利群诱导连续垫资",
            "description": (
                "在兼职群中看到刷单返利广告，首单小额返现后，对方以联单任务为由"
                "要求继续垫资，并称中途退出会导致本金冻结。目前已停止转账并保存聊天记录。"
            ),
            "fraud_type_code": "BRUSH_REWARD",
            "incident_days_ago": 2,
            "created_days_ago": 2,
            "amount": Decimal("6800.00"),
            "fraud_method": "小额返利建立信任，再以联单和解冻为由诱导追加转账",
            "status": CaseStatus.REVIEWING,
            "reporter": student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 4,
            "case_no": "2026-CS-900004",
            "title": "【演示可驳回】信息不完整的兼职招聘线索",
            "description": (
                "在社交平台看到高薪打字兼职，但发布者很快删除账号，当前只有一张"
                "模糊截图，缺少联系方式、链接和转账记录，可用于演示补充材料或驳回流程。"
            ),
            "fraud_type_code": "FAKE_JOB",
            "incident_days_ago": 3,
            "created_days_ago": 3,
            "amount": None,
            "fraud_method": "以低门槛高薪兼职吸引学生私聊",
            "status": CaseStatus.REVIEWING,
            "reporter": student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 5,
            "case_no": "2026-CS-900005",
            "title": "【演示匿名/转报警】冒充公安要求资金清查",
            "description": (
                "对方自称公安机关工作人员，称本人账户涉嫌洗钱，要求下载指定 App"
                "接受视频笔录，并将资金转入所谓安全账户。因担心身份暴露选择匿名上报。"
            ),
            "fraud_type_code": "FAKE_POLICE",
            "incident_days_ago": 1,
            "created_days_ago": 1,
            "amount": Decimal("32000.00"),
            "fraud_method": "冒充公检法制造恐慌，诱导转入安全账户",
            "status": CaseStatus.REVIEWING,
            "reporter": student,
            "is_anonymous": True,
        },
        {
            "case_id": DEMO_ID_BASE + 6,
            "case_no": "2026-CS-900006",
            "title": "【演示已处理】游戏账号场外交易钓鱼网站",
            "description": (
                "买家要求脱离官方平台交易，并发送仿冒担保网站。网站提示收款被冻结，"
                "需要支付解冻金。审核员已完成处置并整理为反诈案例。"
            ),
            "fraud_type_code": "GAME_TRADE",
            "incident_days_ago": 4,
            "created_days_ago": 4,
            "amount": Decimal("1200.00"),
            "fraud_method": "伪造担保网站，以资金冻结为由收取解冻金",
            "status": CaseStatus.HANDLED,
            "reporter": student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 7,
            "case_no": "2026-CS-900007",
            "title": "【演示已驳回】无法核实的中奖短信",
            "description": (
                "仅提供了一段口述信息，未提供短信号码、链接、截图或发生时间，"
                "审核员已反馈需要补充可核实材料。"
            ),
            "fraud_type_code": "OTHER",
            "incident_days_ago": 5,
            "created_days_ago": 5,
            "amount": None,
            "fraud_method": "中奖短信诱导点击链接",
            "status": CaseStatus.REJECTED,
            "reporter": student,
            "is_anonymous": False,
        },
        {
            "case_id": DEMO_ID_BASE + 8,
            "case_no": "2026-CS-900008",
            "title": "【演示已转报警】虚假贷款收取解冻金",
            "description": (
                "通过短信下载网贷 App 后，对方以银行卡号填写错误为由要求支付解冻金，"
                "累计损失较大，平台审核后已建议立即报警并联系银行止付。"
            ),
            "fraud_type_code": "FAKE_LOAN",
            "incident_days_ago": 6,
            "created_days_ago": 6,
            "amount": Decimal("18800.00"),
            "fraud_method": "虚假贷款 App 以账号冻结为由连续收取费用",
            "status": CaseStatus.REPORTED,
            "reporter": student,
            "is_anonymous": False,
        },
    ]

    for index, fixture in enumerate(fixtures):
        existing = (
            await session.execute(
                select(FraudCase).where(FraudCase.case_no == fixture["case_no"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        reporter = fixture["reporter"]
        status = fixture["status"]
        is_anonymous = fixture["is_anonymous"]
        created_at = now - timedelta(days=fixture["created_days_ago"])
        fraud_type = fraud_types[fixture["fraud_type_code"]]
        terminal = status in {
            CaseStatus.HANDLED,
            CaseStatus.REJECTED,
            CaseStatus.REPORTED,
        }
        case = FraudCase(
            case_id=fixture["case_id"],
            case_no=fixture["case_no"],
            title=fixture["title"],
            description=fixture["description"],
            fraud_type_id=fraud_type.type_id,
            incident_date=(now - timedelta(days=fixture["incident_days_ago"])).date(),
            amount=fixture["amount"],
            fraud_method=fixture["fraud_method"],
            status=status,
            reporter_id=None if is_anonymous else reporter.user_id,
            is_anonymous=is_anonymous,
            contact_way=None if is_anonymous else "13800138000",
            reviewer_id=reviewer.user_id if status != CaseStatus.PENDING else None,
            reviewed_at=(now - timedelta(minutes=15 + index)) if terminal else None,
            review_note="演示数据：已完成审核处置。" if terminal else None,
            dept_code="MATH" if reporter.cas_account == "student002" else "CS",
            created_at=created_at,
            updated_at=now - timedelta(minutes=index),
        )
        session.add(case)
        await session.flush()

        session.add(
            CaseStatusHistory(
                history_id=next_snowflake_id(),
                case_id=case.case_id,
                from_status=None,
                to_status=CaseStatus.PENDING,
                operator_id=reporter.user_id,
                note="学生提交演示上报",
                created_at=created_at,
            )
        )
        if status != CaseStatus.PENDING:
            session.add(
                CaseStatusHistory(
                    history_id=next_snowflake_id(),
                    case_id=case.case_id,
                    from_status=CaseStatus.PENDING,
                    to_status=CaseStatus.REVIEWING,
                    operator_id=reviewer.user_id,
                    note="审核员已打开详情并开始核查",
                    created_at=created_at + timedelta(hours=2),
                )
            )
        if terminal:
            terminal_note = {
                CaseStatus.HANDLED: "已完成处置并录入案例库",
                CaseStatus.REJECTED: "材料不足，已反馈补充要求",
                CaseStatus.REPORTED: "损失金额较大，已建议报警并联系银行止付",
            }[status]
            session.add(
                CaseStatusHistory(
                    history_id=next_snowflake_id(),
                    case_id=case.case_id,
                    from_status=CaseStatus.REVIEWING,
                    to_status=status,
                    operator_id=reviewer.user_id,
                    note=terminal_note,
                    created_at=now - timedelta(minutes=15 + index),
                )
            )

        if is_anonymous:
            encrypted = encrypt_field(str(reporter.user_id))
            session.add(
                CaseAnonymousReporter(
                    mapping_id=next_snowflake_id(),
                    case_id=case.case_id,
                    reporter_user_id_enc=encrypted.payload,
                    encryption_key_version=encrypted.version,
                )
            )
    await session.flush()


async def _seed_demo_draft(
    session: AsyncSession,
    *,
    users: dict[str, User],
    fraud_types: dict[str, FraudType],
) -> None:
    student = users["student001"]
    title = "【演示草稿】可疑兼职群聊天记录待补充"
    existing = (
        await session.execute(
            select(ReportDraft).where(
                ReportDraft.student_id == student.user_id,
                ReportDraft.title == title,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    now = datetime.now(UTC).replace(tzinfo=None)
    session.add(
        ReportDraft(
            draft_id=DEMO_ID_BASE + 20,
            student_id=student.user_id,
            title=title,
            description=(
                "已记录兼职群名称和对方昵称，准备补充聊天截图、收款二维码以及完整时间线后再提交。"
            ),
            fraud_type_id=fraud_types["FAKE_JOB"].type_id,
            incident_date=now.date(),
            amount=Decimal("300.00"),
            fraud_method="高薪兼职引流后要求缴纳培训费",
            is_anonymous=False,
            contact_way="student001@nankai.edu.cn",
            expires_at=now + timedelta(days=30),
            created_at=now - timedelta(hours=3),
            updated_at=now - timedelta(hours=1),
        )
    )


async def _seed_demo_warnings(
    session: AsyncSession,
    *,
    users: dict[str, User],
    departments: dict[str, Department],
) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    fixtures: list[DemoWarningFixture] = [
        {
            "title": "【紧急演示】近期冒充公安资金清查诈骗高发",
            "content": (
                "近期校内出现冒充公安机关、要求下载会议软件并将资金转入安全账户的诈骗。"
                "公检法不会通过电话办案，更不会要求转账。接到类似电话请立即挂断并拨打 96110。"
            ),
            "level": WarningLevel.URGENT,
            "publisher": users["reviewer_school001"],
            "scope": WarningPushScope.FULL_SCHOOL,
            "status": WarningStatus.ONLINE,
            "related_case_no": "2026-CS-900005",
            "appendix": "后续补充：请勿开启屏幕共享，验证码不得告知任何人。",
            "dept_codes": [],
            "days_ago": 0,
        },
        {
            "title": "【院系演示】计算机学院兼职刷单风险提示",
            "content": (
                "计算机学院近期收到多起兼职群刷单线索。凡是先垫付、后返利，"
                "并以联单、卡单、解冻为由要求继续转账的，均应立即停止操作并保留证据。"
            ),
            "level": WarningLevel.WARNING,
            "publisher": users["reviewer_dept001"],
            "scope": WarningPushScope.DEPARTMENT,
            "status": WarningStatus.ONLINE,
            "related_case_no": "2026-CS-900003",
            "appendix": None,
            "dept_codes": ["CS"],
            "days_ago": 1,
        },
        {
            "title": "【历史演示】购物节退款诈骗风险提示",
            "content": "历史预警样例，用于演示管理端已下线状态、下线原因和时间。",
            "level": WarningLevel.HINT,
            "publisher": users["reviewer_dept001"],
            "scope": WarningPushScope.FULL_SCHOOL,
            "status": WarningStatus.OFFLINE,
            "related_case_no": "2026-CS-900001",
            "appendix": None,
            "dept_codes": [],
            "days_ago": 10,
        },
    ]

    for offset, fixture in enumerate(fixtures):
        existing = (
            await session.execute(
                select(WarningNotice).where(WarningNotice.title == fixture["title"])
            )
        ).scalar_one_or_none()
        if existing is None:
            published_at = now - timedelta(days=fixture["days_ago"])
            existing = WarningNotice(
                warning_id=DEMO_ID_BASE + 30 + offset,
                title=fixture["title"],
                content=fixture["content"],
                warning_level=fixture["level"],
                related_case_no=fixture["related_case_no"],
                publisher_id=fixture["publisher"].user_id,
                push_scope=fixture["scope"],
                status=fixture["status"],
                appendix=fixture["appendix"],
                published_at=published_at,
                expires_at=now + timedelta(days=7)
                if fixture["status"] == WarningStatus.ONLINE
                else published_at + timedelta(days=3),
                offline_at=now - timedelta(days=6)
                if fixture["status"] == WarningStatus.OFFLINE
                else None,
                offline_reason="风险期已结束，转为历史记录"
                if fixture["status"] == WarningStatus.OFFLINE
                else None,
                created_at=published_at,
                updated_at=published_at,
            )
            session.add(existing)
            await session.flush()

        for dept_code in fixture["dept_codes"]:
            department = departments.get(dept_code)
            if department is None:
                continue
            target = await session.get(
                WarningTarget,
                {"warning_id": existing.warning_id, "dept_id": department.dept_id},
            )
            if target is None:
                session.add(
                    WarningTarget(
                        warning_id=existing.warning_id,
                        dept_id=department.dept_id,
                    )
                )
    await session.flush()


async def _seed_demo_knowledge(
    session: AsyncSession,
    *,
    users: dict[str, User],
    fraud_types: dict[str, FraudType],
) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    author = users["reviewer_dept001"]
    school_reviewer = users["reviewer_school001"]
    fixtures: list[DemoKnowledgeFixture] = [
        {
            "title": "【演示待审】屏幕共享退款诈骗识别要点",
            "status": KnowledgeEntryStatus.PENDING,
            "fraud_type_code": "FAKE_REFUND",
            "reviewer_id": None,
            "review_note": None,
        },
        {
            "title": "【演示草稿】校园群兼职引流案例整理",
            "status": KnowledgeEntryStatus.DRAFT,
            "fraud_type_code": "FAKE_JOB",
            "reviewer_id": None,
            "review_note": "待补充聊天截图脱敏说明",
        },
        {
            "title": "【演示已下线】旧版安全账户诈骗提示",
            "status": KnowledgeEntryStatus.OFFLINE,
            "fraud_type_code": "FAKE_POLICE",
            "reviewer_id": school_reviewer.user_id,
            "review_note": "内容已合并到新版公检法防骗指南",
        },
    ]

    for offset, fixture in enumerate(fixtures):
        existing = (
            await session.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.title == fixture["title"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        status = fixture["status"]
        entry = KnowledgeEntry(
            entry_id=DEMO_ID_BASE + 40 + offset,
            title=fixture["title"],
            fraud_type_id=fraud_types[fixture["fraud_type_code"]].type_id,
            desensitized_summary=(
                "学生接到自称平台客服的来电，对方以退款理赔为由要求打开会议软件。"
                "案例已去除姓名、账号、电话号码等个人信息。"
            ),
            identification_points=(
                "1. 主动来电并承诺高额赔偿；\n"
                "2. 要求脱离官方平台操作；\n"
                "3. 要求开启屏幕共享或提供验证码。"
            ),
            prevention_advice=(
                "只在购物平台官方订单页处理售后；拒绝屏幕共享；"
                "发现异常立即冻结银行卡并拨打 96110。"
            ),
            peak_periods="购物节、开学季",
            source_type=KnowledgeEntrySourceType.CASE,
            source_reference="演示案件 2026-CS-900001",
            status=status,
            version=2 if status == KnowledgeEntryStatus.PENDING else 1,
            author_id=author.user_id,
            reviewer_id=fixture["reviewer_id"],
            review_note=fixture["review_note"],
            published_at=None,
            offlined_at=now - timedelta(days=2)
            if status == KnowledgeEntryStatus.OFFLINE
            else None,
            created_at=now - timedelta(days=3 + offset),
            updated_at=now - timedelta(hours=offset + 1),
        )
        session.add(entry)
        await session.flush()

        snapshot = {
            "title": entry.title,
            "status": entry.status,
            "fraud_type_id": entry.fraud_type_id,
            "source_reference": entry.source_reference,
        }
        session.add(
            KnowledgeEntryHistory(
                history_id=next_snowflake_id(),
                entry_id=entry.entry_id,
                version=1,
                content_snapshot=snapshot | {"status": KnowledgeEntryStatus.DRAFT},
                modified_by=author.user_id,
                action=KnowledgeEntryHistoryAction.CREATE,
                modified_at=entry.created_at,
            )
        )
        if status == KnowledgeEntryStatus.PENDING:
            session.add(
                KnowledgeEntryHistory(
                    history_id=next_snowflake_id(),
                    entry_id=entry.entry_id,
                    version=2,
                    content_snapshot=snapshot,
                    modified_by=author.user_id,
                    action=KnowledgeEntryHistoryAction.SUBMIT,
                    modified_at=entry.updated_at,
                )
            )
    await session.flush()


async def _seed_demo_quiz_history(
    session: AsyncSession,
    *,
    users: dict[str, User],
) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    title = "【演示历史】校园反诈基础回顾测验"
    quiz = (
        await session.execute(select(Quiz).where(Quiz.title == title))
    ).scalar_one_or_none()
    questions = (
        (
            await session.execute(
                select(QuestionBank)
                .where(QuestionBank.is_active == 1)
                .order_by(QuestionBank.question_id)
                .limit(5)
            )
        )
        .scalars()
        .all()
    )
    if len(questions) < 5:
        return

    if quiz is None:
        quiz = Quiz(
            quiz_id=DEMO_ID_BASE + 50,
            quiz_type=QuizType.ASSIGNED,
            title=title,
            question_count=5,
            pass_score=60,
            status=QuizStatus.FINISHED,
            created_by=users["sysadmin001"].user_id,
            deadline_at=now - timedelta(days=1),
            target_scope={"type": QuizScopeType.ALL},
            publish_level=2,
            reminder_sent=1,
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=1),
        )
        session.add(quiz)
        await session.flush()

    link_count = (
        await session.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.quiz_id)
        )
    ).scalars().all()
    if not link_count:
        for sort_order, question in enumerate(questions, start=1):
            session.add(
                QuizQuestion(
                    quiz_id=quiz.quiz_id,
                    question_id=question.question_id,
                    sort_order=sort_order,
                )
            )
        await session.flush()

    participant_scores = [
        ("student001", 3),
        ("student002", 4),
        ("student003", 2),
    ]
    for offset, (account, correct_count) in enumerate(participant_scores):
        student = users.get(account)
        if student is None:
            continue
        existing_attempt = (
            await session.execute(
                select(QuizAttempt).where(
                    QuizAttempt.quiz_id == quiz.quiz_id,
                    QuizAttempt.student_id == student.user_id,
                )
            )
        ).scalar_one_or_none()
        if existing_attempt is not None:
            continue

        attempt = QuizAttempt(
            attempt_id=DEMO_ID_BASE + 60 + offset,
            quiz_id=quiz.quiz_id,
            student_id=student.user_id,
            status=QuizAttemptStatus.SUBMITTED,
            score=correct_count * 20,
            correct_count=correct_count,
            started_at=now - timedelta(days=2, minutes=25 + offset),
            submitted_at=now - timedelta(days=2, minutes=offset),
        )
        session.add(attempt)
        await session.flush()

        for question_index, question in enumerate(questions):
            is_correct = question_index < correct_count
            wrong_answer = "B" if question.correct_answer == "A" else "A"
            session.add(
                QuizAttemptAnswer(
                    answer_id=next_snowflake_id(),
                    attempt_id=attempt.attempt_id,
                    question_id=question.question_id,
                    chosen_answer=question.correct_answer if is_correct else wrong_answer,
                    is_correct=1 if is_correct else 0,
                )
            )
    await session.flush()


async def _seed_demo_notifications(
    session: AsyncSession,
    *,
    users: dict[str, User],
) -> None:
    student = users["student001"]
    fixtures = [
        (
            "WARNING_PUSH",
            "紧急预警：冒充公安资金清查诈骗高发",
            "请勿向所谓安全账户转账，接到类似电话立即拨打 96110 核实。",
            "warning",
            DEMO_ID_BASE + 30,
            0,
        ),
        (
            "REPORT_RESOLVED",
            "上报事件 2026-CS-900006 已处理",
            "审核员已完成处置并将脱敏内容整理为反诈案例。",
            "fraud_case",
            DEMO_ID_BASE + 6,
            0,
        ),
        (
            "REPORT_REJECTED",
            "上报事件 2026-CS-900007 需要补充材料",
            "请补充短信截图、发送号码、链接地址和大致发生时间。",
            "fraud_case",
            DEMO_ID_BASE + 7,
            1,
        ),
        (
            "QUIZ_ASSIGNED",
            "新的指定测验等待完成",
            "请在截止时间前完成新生反诈意识基线测验。",
            "quiz",
            None,
            0,
        ),
    ]

    now = datetime.now(UTC).replace(tzinfo=None)
    for offset, fixture in enumerate(fixtures):
        notif_type, title, content, object_type, object_id, is_read = fixture
        exists = (
            await session.execute(
                select(Notification).where(
                    Notification.recipient_id == student.user_id,
                    Notification.title == title,
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            continue
        created_at = now - timedelta(minutes=20 + offset * 5)
        session.add(
            Notification(
                notification_id=next_snowflake_id(),
                recipient_id=student.user_id,
                type=notif_type,
                title=title,
                content=content,
                related_object_type=object_type,
                related_object_id=object_id,
                is_read=is_read,
                created_at=created_at,
                read_at=created_at + timedelta(minutes=2) if is_read else None,
            )
        )
