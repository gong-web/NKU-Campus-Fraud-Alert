<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { auditApi } from "@/api/audit";
import { usersApi } from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import {
  AppActivityItem,
  AppButton,
  AppCard,
  AppIcon,
  AppPageHeader,
  AppStatCard,
} from "@/components";
import { formatRelative } from "@/utils/format";
import { auditOpLabel } from "@/utils/auditLabels";
import type { AuditLogOut, UserOut } from "@/types/api";

const router = useRouter();
const auth = useAuthStore();

const usersTotal = ref<number | null>(null);
const usersActive = ref<number>(0);
const usersDisabled = ref<number>(0);
const auditTotal = ref<number | null>(null);
interface FeedItem extends AuditLogOut {
  group_count?: number;
}
const auditRecent = ref<FeedItem[]>([]);

/**
 * 折叠连续相同 (operation_type + operator_id) 的审计记录，
 * 避免大量重复登录撑满"近期动态"列表。
 */
function dedupeFeed(items: AuditLogOut[], limit: number): FeedItem[] {
  const out: FeedItem[] = [];
  for (const it of items) {
    const last = out[out.length - 1];
    if (
      last &&
      last.operation_type === it.operation_type &&
      String(last.operator_id) === String(it.operator_id)
    ) {
      last.group_count = (last.group_count ?? 1) + 1;
      continue;
    }
    out.push({ ...it, group_count: 1 });
    if (out.length >= limit) break;
  }
  return out;
}
const judicialRecent = ref<AuditLogOut[]>([]);
const loading = ref<boolean>(true);
const errorMsg = ref<string>("");

const greeting = computed<string>(() => {
  const hour = new Date().getHours();
  if (hour < 5) return "深夜好";
  if (hour < 12) return "早上好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

const today = computed<string>(() => {
  const d = new Date();
  const w = ["日", "一", "二", "三", "四", "五", "六"][d.getDay()];
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 · 星期${w}`;
});

interface QuickAction {
  to: string;
  title: string;
  desc: string;
  icon: string;
  tone: "brand" | "info" | "danger";
}

const QUICK_ACTIONS: readonly QuickAction[] = [
  {
    to: "/sys/users",
    title: "新建账号",
    desc: "开通访问并分配角色",
    icon: "user-cog",
    tone: "brand",
  },
  {
    to: "/sys/audit",
    title: "审计日志",
    desc: "按操作和时间查询记录",
    icon: "list-checks",
    tone: "info",
  },
  {
    to: "/sys/judicial-assist",
    title: "司法协助查询",
    desc: "提交协查申请并查看解密结果",
    icon: "scale",
    tone: "danger",
  },
];

interface SecurityCheck {
  title: string;
  status: "ok" | "warn";
  detail: string;
  icon: string;
}

const SECURITY_CHECKS: readonly SecurityCheck[] = [
  {
    title: "审计日志",
    status: "ok",
    detail: "重要操作有据可查",
    icon: "shield-check",
  },
  {
    title: "匿名上报",
    status: "ok",
    detail: "身份信息隔离保护",
    icon: "lock",
  },
  {
    title: "登录安全",
    status: "ok",
    detail: "登录会话安全保护",
    icon: "shield-alert",
  },
];

function shortId(v: unknown): string {
  const s = String(v ?? "");
  if (s.length <= 10) return s;
  return `${s.slice(0, 4)}…${s.slice(-4)}`;
}

function actionTitle(item: AuditLogOut): string {
  const op = item.operation_type;
  const id = shortId(item.object_id);
  const label = auditOpLabel(op);
  if (op === "USER_BATCH_IMPORT") return `${label} · ${item.object_id} 条`;
  if (op.startsWith("DECRYPT")) return `${label} · 事件 ${id}`;
  return `${label} · ${id}`;
}

function actionIcon(item: AuditLogOut): string {
  const op = item.operation_type;
  if (op.startsWith("LOGIN")) return "log-in";
  if (op === "LOGOUT") return "log-out";
  if (op.startsWith("USER")) return "user-cog";
  if (op.startsWith("DECRYPT")) return "scale";
  return "activity";
}

function actionTone(item: AuditLogOut): "brand" | "info" | "success" | "warning" | "danger" | "neutral" {
  const op = item.operation_type;
  if (op === "LOGIN_FAILED") return "warning";
  if (op.startsWith("DECRYPT")) return "danger";
  if (op.startsWith("USER")) return "info";
  if (op === "LOGIN") return "success";
  return "brand";
}

async function load(): Promise<void> {
  loading.value = true;
  errorMsg.value = "";
  try {
    const [users, audit, judicial] = await Promise.all([
      usersApi.list({ page: 1, size: 100 }),
      auditApi.list({ page: 1, size: 8 }),
      auditApi.list({ page: 1, size: 5, op_type: "DECRYPT_ANONYMOUS" }),
    ]);
    usersTotal.value = users.total;
    const items = (users.items as UserOut[]) ?? [];
    usersActive.value = items.filter((x) => x.status === 1).length;
    usersDisabled.value = items.filter((x) => x.status !== 1).length;
    auditTotal.value = audit.total;
    auditRecent.value = dedupeFeed(audit.items, 6);
    judicialRecent.value = judicial.items.slice(0, 4);
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : "加载概览失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function go(path: string): void {
  void router.push(path);
}
</script>

<template>
  <div class="sys-dash">
    <AppPageHeader
      :title="`${greeting}，${auth.me?.real_name ?? '管理员'}`"
    >
      <template #actions>
        <AppButton
          variant="secondary"
          size="sm"
          @click="load"
        >
          <AppIcon
            name="activity"
            :size="14"
          />
          刷新
        </AppButton>
      </template>
    </AppPageHeader>

    <p
      v-if="errorMsg"
      class="sys-dash__error"
    >
      <AppIcon
        name="alert-triangle"
        :size="16"
      />
      {{ errorMsg }}
    </p>

    <section class="sys-dash__hero">
      <AppCard
        tone="brand"
        padding="lg"
        class="sys-dash__hero-card"
      >
        <div class="sys-dash__hero-grid">
          <div class="sys-dash__hero-left">
            <h2 class="sys-dash__hero-title">
              平台管理
            </h2>
            <p class="sys-dash__hero-lead">
              管理账号、查看操作记录，处理司法协助申请。
            </p>
            <div class="sys-dash__hero-actions">
              <AppButton
                variant="secondary-on-brand"
                @click="go('/sys/audit')"
              >
                <AppIcon
                  name="list-checks"
                  :size="16"
                />
                查看审计
              </AppButton>
              <AppButton
                variant="ghost-on-brand"
                @click="go('/sys/users')"
              >
                <AppIcon
                  name="users"
                  :size="16"
                />
                账号管理
              </AppButton>
            </div>
          </div>
          <ul class="sys-dash__hero-checks">
            <li
              v-for="(c, i) in SECURITY_CHECKS"
              :key="c.title"
              :style="{ animationDelay: `${0.1 * i}s` }"
            >
              <span class="sys-dash__hero-check-icon">
                <AppIcon
                  :name="(c.icon as never)"
                  :size="16"
                />
              </span>
              <div class="sys-dash__hero-check-body">
                <strong>{{ c.title }}</strong>
                <small>{{ c.detail }}</small>
              </div>
              <span
                class="sys-dash__hero-check-status"
                :title="c.status === 'ok' ? '正常' : '需关注'"
                aria-label="状态"
              >
                <AppIcon
                  :name="(c.status === 'ok' ? 'circle-check' : 'alert-triangle' as never)"
                  :size="14"
                />
              </span>
            </li>
          </ul>
        </div>
      </AppCard>
    </section>

    <!-- 关键指标 -->
    <section class="sys-dash__stats">
      <AppStatCard
        label="账号总数"
        :value="usersTotal ?? '—'"
        icon="users"
        tone="brand"
        :loading="loading"
        :hint="`活跃 ${usersActive} · 停用 ${usersDisabled}`"
      />
      <AppStatCard
        label="审计日志总条数"
        :value="auditTotal ?? '—'"
        icon="list-checks"
        tone="info"
        :loading="loading"
        hint="自上线起累计"
      />
      <AppStatCard
        label="司法协助申请"
        :value="judicialRecent.length"
        icon="scale"
        tone="danger"
        :loading="loading"
        hint="近期解密事件"
      />
      <AppStatCard
        label="预警状态"
        value="正常"
        icon="shield-check"
        tone="success"
        :loading="loading"
        hint="各服务运行正常"
      />
    </section>

    <!-- 双栏：审计动态 + 快捷入口 -->
    <section class="sys-dash__grid">
      <AppCard
        padding="lg"
        :corner="true"
        class="sys-dash__feed"
      >
        <template #header>
          <div class="sys-dash__feed-head">
            <div>
              <h3>近期审计动态</h3>
              <small>仅展示最近 6 条；完整信息请进入审计日志。</small>
            </div>
            <AppButton
              variant="ghost"
              size="sm"
              @click="go('/sys/audit')"
            >
              查看全部
              <AppIcon
                name="arrow-right"
                :size="14"
              />
            </AppButton>
          </div>
        </template>
        <ul
          v-if="auditRecent.length"
          class="sys-dash__feed-list"
        >
          <AppActivityItem
            v-for="item in auditRecent"
            :key="item.log_id"
            :title="`${actionTitle(item)}${(item.group_count ?? 1) > 1 ? `  × ${item.group_count}` : ''}`"
            :meta="`操作人 #${shortId(item.operator_id)} · ${item.source_ip || '内部任务'}`"
            :time="formatRelative(item.operated_at)"
            :icon="actionIcon(item)"
            :tone="actionTone(item)"
          />
        </ul>
        <div
          v-else
          class="sys-dash__feed-empty"
        >
          <AppIcon
            name="info"
            :size="16"
          />
          暂无近期审计记录。
        </div>
      </AppCard>

      <AppCard
        padding="lg"
        class="sys-dash__quick"
      >
        <template #header>
          <div>
            <h3>快捷入口</h3>
          </div>
        </template>
        <ul class="sys-dash__actions">
          <li
            v-for="(a, i) in QUICK_ACTIONS"
            :key="a.to"
            :style="{ animationDelay: `${0.06 * i}s` }"
            class="sys-dash__action-item"
          >
            <button
              type="button"
              class="sys-dash__action"
              :class="`sys-dash__action--${a.tone}`"
              @click="go(a.to)"
            >
              <span class="sys-dash__action-icon">
                <AppIcon
                  :name="(a.icon as never)"
                  :size="20"
                />
              </span>
              <span class="sys-dash__action-text">
                <strong>{{ a.title }}</strong>
                <small>{{ a.desc }}</small>
              </span>
              <AppIcon
                name="arrow-right"
                :size="16"
                class="sys-dash__action-arrow"
              />
            </button>
          </li>
        </ul>

        <div class="sys-dash__health">
          <div class="sys-dash__health-head">
            <AppIcon
              name="shield-check"
              :size="14"
            />
            <span>系统健康</span>
            <span class="sys-dash__health-pill">全部正常</span>
          </div>
          <ul class="sys-dash__health-list">
            <li><span class="dot dot--ok" />数据库</li>
            <li><span class="dot dot--ok" />缓存服务</li>
            <li><span class="dot dot--ok" />文件存储</li>
            <li><span class="dot dot--ok" />审计服务</li>
          </ul>
        </div>
      </AppCard>
    </section>
  </div>
</template>

<style scoped>
.sys-dash {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.sys-dash__error {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(198 40 40 / 6%);
  color: var(--color-danger);
  border: 1px solid rgb(198 40 40 / 22%);
  font-size: var(--font-size-sm);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

/* ── 英雄卡片 ─────────────────────────────────────────────────── */
.sys-dash__hero-card {
  position: relative;
  overflow: hidden;
}

.sys-dash__hero-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--space-6);
  color: #fff;
}

@media (width <= 1024px) {
  .sys-dash__hero-grid {
    grid-template-columns: 1fr;
  }
}

.sys-dash__hero-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sys-dash__hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  background: rgb(255 255 255 / 12%);
  border: 1px solid rgb(255 255 255 / 16%);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: var(--font-weight-medium);
  width: fit-content;
}

.sys-dash__hero-eyebrow .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-gold-300);
  box-shadow: 0 0 8px rgb(230 179 73 / 80%);
}

.sys-dash__hero-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: clamp(24px, 2.6vw, 36px);
  line-height: 1.2;
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.01em;
}

.sys-dash__hero-em {
  background: linear-gradient(120deg, var(--color-gold-200) 0%, var(--color-gold-400) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.sys-dash__hero-lead {
  margin: 0;
  color: rgb(255 255 255 / 80%);
  line-height: 1.75;
  max-width: 580px;
  font-size: var(--font-size-sm);
}

.sys-dash__hero-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-2);
}

.sys-dash__hero-checks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sys-dash__hero-checks li {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgb(255 255 255 / 9%), rgb(255 255 255 / 4%));
  border: 1px solid rgb(255 255 255 / 12%);
  animation: feature-in 600ms var(--easing-out) both;
}

@keyframes feature-in {
  from {
    opacity: 0;
    transform: translateX(8px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.sys-dash__hero-check-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: rgb(46 125 50 / 32%);
  color: #b9f2bd;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.sys-dash__hero-check-body strong {
  display: block;
  font-size: 12.5px;
  font-weight: var(--font-weight-semibold);
}

.sys-dash__hero-check-body small {
  font-size: 11px;
  color: rgb(255 255 255 / 64%);
  line-height: 1.45;
}

.sys-dash__hero-check-status {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgb(74 222 128 / 16%);
  border: 1px solid rgb(74 222 128 / 38%);
  color: #4ade80;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 0 0 rgb(74 222 128 / 50%);
  animation: pulse-dot 2.4s ease-in-out infinite;
}

.sys-dash__hero-check-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px rgb(74 222 128 / 80%);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.sys-dash__hero-watermark {
  position: absolute;
  bottom: -12px;
  right: 12px;
  font-family: var(--font-family-serif);
  font-size: 110px;
  font-weight: 700;
  color: rgb(230 179 73 / 6%);
  letter-spacing: 0.04em;
  pointer-events: none;
  user-select: none;
  z-index: 1;
}

/* ── 统计卡区 ─────────────────────────────────────────────────── */
.sys-dash__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(228px, 1fr));
  gap: var(--space-4);
}

/* ── 双栏 ─────────────────────────────────────────────────────── */
.sys-dash__grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: var(--space-4);
}

@media (width <= 1024px) {
  .sys-dash__grid {
    grid-template-columns: 1fr;
  }
}

.sys-dash__feed-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
}

.sys-dash__feed-head h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.sys-dash__feed-head small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.sys-dash__feed-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.sys-dash__feed-empty {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  padding: var(--space-5) 0;
}

/* ── 快捷入口 ─────────────────────────────────────────────────── */
.sys-dash__quick h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.sys-dash__quick small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.sys-dash__actions {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sys-dash__action-item {
  animation: feature-in 500ms var(--easing-out) both;
}

.sys-dash__action {
  width: 100%;
  display: grid;
  grid-template-columns: 40px 1fr auto auto;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  color: inherit;
  transition: all var(--duration-base) var(--easing-out);
  position: relative;
  overflow: hidden;
}

.sys-dash__action::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  transition: background var(--duration-base) var(--easing-out);
}

.sys-dash__action:hover {
  border-color: var(--color-brand-300);
  transform: translateX(2px);
  box-shadow: var(--shadow-low);
  background: var(--color-bg);
}

.sys-dash__action--brand:hover::before { background: var(--color-brand-500); }
.sys-dash__action--info:hover::before { background: var(--color-info); }
.sys-dash__action--danger:hover::before { background: var(--color-danger); }

.sys-dash__action-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
}

.sys-dash__action--brand .sys-dash__action-icon {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border-color: rgb(134 38 51 / 12%);
}

.sys-dash__action--info .sys-dash__action-icon {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}

.sys-dash__action--danger .sys-dash__action-icon {
  background: rgb(198 40 40 / 10%);
  color: var(--color-danger);
  border-color: rgb(198 40 40 / 18%);
}

.sys-dash__action-text {
  min-width: 0;
}

.sys-dash__action-text strong {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.sys-dash__action-text small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 1px;
  display: block;
}

.sys-dash__action-kbd {
  font-family: var(--font-family-mono);
  font-size: 10.5px;
  letter-spacing: 0.08em;
  padding: 2px 6px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.sys-dash__action-arrow {
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--easing-out);
}

.sys-dash__action:hover .sys-dash__action-arrow {
  transform: translateX(2px);
  color: var(--color-brand-600);
}

@media (width <= 640px) {
  .sys-dash__action {
    grid-template-columns: 40px 1fr auto;
  }

  .sys-dash__action-kbd {
    display: none;
  }
}

.sys-dash__health {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, rgb(46 125 50 / 5%), rgb(46 125 50 / 1%));
  border: 1px solid rgb(46 125 50 / 22%);
}

.sys-dash__health-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  font-weight: var(--font-weight-semibold);
  color: var(--color-success);
  text-transform: uppercase;
  margin-bottom: var(--space-2);
}

.sys-dash__health-pill {
  margin-left: auto;
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.16em;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: rgb(46 125 50 / 12%);
  border: 1px solid rgb(46 125 50 / 28%);
  color: var(--color-success);
  text-transform: none;
}

.sys-dash__health-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.sys-dash__health-list li {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.02em;
}

.sys-dash__health-list .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-neutral-400);
}

.sys-dash__health-list .dot--ok {
  background: var(--color-success);
  box-shadow: 0 0 0 2px rgb(46 125 50 / 12%);
}
</style>
