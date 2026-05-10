<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppPageHeader,
  AppStatCard,
} from "@/components";

const auth = useAuthStore();

const greeting = computed<string>(() => {
  const hour = new Date().getHours();
  if (hour < 5) return "凌晨好";
  if (hour < 12) return "早上好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

interface PendingTrack {
  title: string;
  desc: string;
  count: number | string;
  icon: string;
  tone: "brand" | "info" | "warning" | "danger";
}

const TRACKS: readonly PendingTrack[] = [
  {
    title: "待初审",
    desc: "学生新提交的事件，需 24h 内分流",
    count: "—",
    icon: "clipboard-list",
    tone: "brand",
  },
  {
    title: "待复核",
    desc: "院系级处理后需校级二审",
    count: "—",
    icon: "list-checks",
    tone: "info",
  },
  {
    title: "需补充材料",
    desc: "证据不足，已请上报人补交",
    count: "—",
    icon: "file-text",
    tone: "warning",
  },
  {
    title: "高风险预警",
    desc: "金额或类型触发紧急策略",
    count: "—",
    icon: "siren",
    tone: "danger",
  },
];

interface FlowStep {
  label: string;
  desc: string;
  state: "done" | "active" | "wait";
}

const FLOW: readonly FlowStep[] = [
  { label: "提交", desc: "学生上报", state: "done" },
  { label: "初审", desc: "24h 内", state: "done" },
  { label: "复核", desc: "院系/校级", state: "active" },
  { label: "处置", desc: "止损归档", state: "wait" },
];
</script>

<template>
  <div class="admin-dash">
    <AppPageHeader
      badge="审核工作台"
      :title="`${greeting}，${auth.me?.real_name ?? '审核员'}`"
      subtitle="事件上报 · 初审 · 复核 · 处置全流程工作台。状态机由 service 层守护，所有变更同事务写审计。"
    >
      <template #actions>
        <AppButton
          variant="secondary"
          size="sm"
          :disabled="true"
          title="部门过滤即将上线"
        >
          <AppIcon
            name="filter"
            :size="14"
          />
          按部门过滤
        </AppButton>
      </template>
    </AppPageHeader>

    <!-- 英雄卡：流程展示 -->
    <AppCard
      tone="brand"
      padding="lg"
      class="admin-dash__hero"
    >
      <div class="admin-dash__hero-grid">
        <div>
          <span class="admin-dash__hero-eyebrow">
            <span class="dot" />
            审核工作流 · 闭环
          </span>
            <h2 class="admin-dash__hero-title">
              事件全程可追溯，<br>
              <span class="admin-dash__hero-em">守住校园安全防线</span>
            </h2>
          <p class="admin-dash__hero-lead">
            状态机由地基组的 service 层守护：所有状态变更必须在<strong>同一事务</strong>内完成，
            并自动写审计；任何角色都不能绕过流程或删改记录。
          </p>
          <div class="admin-dash__hero-actions">
            <AppButton
              variant="secondary-on-brand"
              :disabled="true"
              title="操作手册即将上线"
            >
              <AppIcon
                name="book-open"
                :size="16"
              />
              审核操作手册
            </AppButton>
            <AppButton
              variant="ghost-on-brand"
              :disabled="true"
              title="状态分流即将上线"
            >
              <AppIcon
                name="filter"
                :size="16"
              />
              按状态分流
            </AppButton>
          </div>
        </div>

        <div
          class="admin-dash__hero-flow"
          aria-hidden="true"
        >
          <ol class="admin-dash__flow">
            <li
              v-for="(step, i) in FLOW"
              :key="step.label"
              :class="`admin-dash__flow-step admin-dash__flow-step--${step.state}`"
            >
              <span class="admin-dash__flow-num">{{ String(i + 1).padStart(2, "0") }}</span>
              <strong>{{ step.label }}</strong>
              <small>{{ step.desc }}</small>
              <span
                v-if="i < FLOW.length - 1"
                class="admin-dash__flow-arrow"
                aria-hidden="true"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <path
                    d="M3 8h10m-3-3 3 3-3 3"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </span>
            </li>
          </ol>
        </div>
      </div>
    </AppCard>

    <!-- 待办计数 -->
    <section class="admin-dash__tracks">
      <AppStatCard
        v-for="t in TRACKS"
        :key="t.title"
        :label="t.title"
        :value="t.count"
        :hint="t.desc"
        :icon="t.icon"
        :tone="t.tone"
        placeholder="待接入"
      />
    </section>

    <!-- 双栏占位 -->
    <section class="admin-dash__grid">
      <AppCard
        padding="md"
        :corner="true"
      >
        <template #header>
          <div>
            <h3>分配给我</h3>
            <small>事件上报模块接入后自动加载</small>
          </div>
          <span class="admin-dash__chip">即将开放</span>
        </template>
        <div class="admin-dash__placeholder">
          <span class="admin-dash__placeholder-icon">
            <AppIcon
              name="clipboard-list"
              :size="20"
            />
          </span>
          <div class="admin-dash__placeholder-text">
            <p>分配给当前审核员的事件队列</p>
            <small>支持初审、复核、处置流程；按状态、风险等级、时效自动排序</small>
          </div>
        </div>
      </AppCard>

      <AppCard padding="md">
        <template #header>
          <div>
            <h3>本周指标</h3>
            <small>数据分析模块接入后自动加载</small>
          </div>
          <span class="admin-dash__chip">即将开放</span>
        </template>
        <div class="admin-dash__placeholder">
          <span
            class="admin-dash__placeholder-icon"
            data-tone="info"
          >
            <AppIcon
              name="activity"
              :size="20"
            />
          </span>
          <div class="admin-dash__placeholder-text">
            <p>处置时长 · 复核率 · 误判率等审核 KPI</p>
            <small>含同期对比、部门排名、首响时长热力图</small>
          </div>
        </div>
      </AppCard>
    </section>
  </div>
</template>

<style scoped>
.admin-dash {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── 英雄卡 ───────────────────────────────────────────────────── */
.admin-dash__hero {
  position: relative;
  overflow: hidden;
}

.admin-dash__hero-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-6);
  color: #fff;
  align-items: center;
}

@media (width <= 1024px) {
  .admin-dash__hero-grid {
    grid-template-columns: 1fr;
  }
}

.admin-dash__hero-eyebrow {
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

.admin-dash__hero-eyebrow .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-gold-300);
  box-shadow: 0 0 8px rgb(230 179 73 / 80%);
}

.admin-dash__hero-title {
  margin: var(--space-3) 0 var(--space-2);
  font-family: var(--font-family-serif);
  font-size: clamp(22px, 2.4vw, 30px);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.04em;
  line-height: 1.3;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: baseline;
}

.admin-dash__hero-step {
  white-space: nowrap;
}

.admin-dash__hero-sep {
  color: var(--color-gold-300);
  opacity: 0.6;
  font-weight: var(--font-weight-regular);
}

.admin-dash__hero-em {
  background: linear-gradient(120deg, var(--color-gold-200) 0%, var(--color-gold-400) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.admin-dash__hero-lead {
  margin: 0 0 var(--space-4);
  color: rgb(255 255 255 / 80%);
  max-width: 560px;
  line-height: 1.7;
  font-size: var(--font-size-sm);
}

.admin-dash__hero-lead strong {
  color: rgb(255 233 196 / 92%);
  font-weight: var(--font-weight-semibold);
}

.admin-dash__hero-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.admin-dash__hero-flow {
  display: flex;
  align-items: center;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgb(255 255 255 / 9%), rgb(255 255 255 / 4%));
  border: 1px solid rgb(255 255 255 / 16%);
  backdrop-filter: blur(var(--glass-blur));
}

.admin-dash__flow {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: stretch;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.admin-dash__flow-step {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  column-gap: var(--space-2);
  align-items: center;
  padding: var(--space-3) var(--space-4) var(--space-3) var(--space-3);
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 4%);
  border: 1px solid rgb(255 255 255 / 14%);
  min-width: 104px;
  transition: all var(--duration-base) var(--easing-out);
}

.admin-dash__flow-step:hover {
  border-color: rgb(230 179 73 / 36%);
  background: rgb(255 255 255 / 7%);
}

.admin-dash__flow-num {
  grid-row: 1 / 3;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  background: rgb(255 255 255 / 12%);
  font-family: var(--font-family-mono);
  font-size: 11px;
  font-weight: var(--font-weight-bold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.04em;
}

.admin-dash__flow-step strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-dash__flow-step small {
  font-size: 11px;
  opacity: 0.66;
}

.admin-dash__flow-step--done {
  background: rgb(46 125 50 / 28%);
  border-color: rgb(46 125 50 / 50%);
}

.admin-dash__flow-step--done .admin-dash__flow-num {
  background: rgb(46 125 50 / 56%);
  color: #b9f2bd;
}

.admin-dash__flow-step--active {
  background: rgb(230 179 73 / 28%);
  border-color: rgb(230 179 73 / 56%);
  box-shadow: 0 0 0 3px rgb(230 179 73 / 18%);
}

.admin-dash__flow-step--active .admin-dash__flow-num {
  background: rgb(230 179 73 / 50%);
  color: #fff8e7;
}

.admin-dash__flow-step--wait {
  opacity: 0.6;
}

.admin-dash__flow-arrow {
  position: absolute;
  right: -18px;
  top: 50%;
  transform: translateY(-50%);
  color: rgb(230 179 73 / 64%);
  z-index: 1;
}

@media (width <= 768px) {
  .admin-dash__flow-arrow { display: none; }
}

.admin-dash__hero-watermark {
  position: absolute;
  bottom: -8px;
  right: 16px;
  font-family: var(--font-family-serif);
  font-size: 96px;
  font-weight: 700;
  color: rgb(230 179 73 / 6%);
  letter-spacing: 0.04em;
  pointer-events: none;
  user-select: none;
  z-index: 1;
}

/* ── 待办计数 ─────────────────────────────────────────────────── */
.admin-dash__tracks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

/* ── 双栏 ─────────────────────────────────────────────────────── */
.admin-dash__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

@media (width <= 1024px) {
  .admin-dash__grid {
    grid-template-columns: 1fr;
  }
}

.admin-dash__grid h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.admin-dash__grid small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.admin-dash__chip {
  font-family: var(--font-family-mono);
  font-size: 10.5px;
  letter-spacing: 0.18em;
  padding: 3px 10px;
  background: var(--color-gold-50);
  color: var(--color-gold-700);
  border: 1px solid rgb(230 179 73 / 28%);
  border-radius: var(--radius-pill);
  text-transform: uppercase;
}

.admin-dash__placeholder {
  display: grid;
  grid-template-columns: 40px 1fr;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3) var(--space-2);
  color: var(--color-text-secondary);
}

.admin-dash__placeholder-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.admin-dash__placeholder p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}

.admin-dash__placeholder small {
  font-size: var(--font-size-xs);
  opacity: 0.85;
  line-height: 1.55;
}

.admin-dash__placeholder-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-brand-50);
  color: var(--color-brand-600);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(134 38 51 / 12%);
  box-shadow: var(--shadow-low);
  flex-shrink: 0;
}

.admin-dash__placeholder-icon[data-tone="info"] {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}
</style>
