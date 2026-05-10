<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import {
  AppButton,
  AppCard,
  AppIcon,
  AppPageHeader,
} from "@/components";

const auth = useAuthStore();

const greeting = computed<string>(() => {
  const hour = new Date().getHours();
  if (hour < 5) return "凌晨好";
  if (hour < 12) return "上午好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

interface FraudType {
  code: string;
  name: string;
  desc: string;
  icon: string;
  tone: "brand" | "info" | "warning" | "danger";
  trend: string;
}

const FRAUD_TYPES: readonly FraudType[] = [
  {
    code: "BRUSH_REWARD",
    name: "刷单返利",
    desc: "高佣金兼职、垫付返现",
    icon: "alert-triangle",
    tone: "warning",
    trend: "高发",
  },
  {
    code: "FAKE_POLICE",
    name: "冒充公检法",
    desc: "称账户涉案、恐吓转账",
    icon: "siren",
    tone: "danger",
    trend: "紧急",
  },
  {
    code: "FAKE_JOB",
    name: "虚假兼职",
    desc: "刷信誉、打字员、模特经纪",
    icon: "user-cog",
    tone: "warning",
    trend: "高发",
  },
  {
    code: "FAKE_REFUND",
    name: "冒充客服退款",
    desc: "购物 / 快递异常诱导退款",
    icon: "alert-triangle",
    tone: "warning",
    trend: "常见",
  },
  {
    code: "DATING_FRAUD",
    name: "恋爱交友",
    desc: "杀猪盘 / 投资盘",
    icon: "shield-alert",
    tone: "danger",
    trend: "紧急",
  },
  {
    code: "FAKE_LOAN",
    name: "虚假贷款",
    desc: "无门槛低息，先交手续费",
    icon: "info",
    tone: "info",
    trend: "常见",
  },
];

interface QuickEntry {
  title: string;
  desc: string;
  icon: string;
  tone: "brand" | "info" | "warning";
  cta: string;
  anchor?: string;
}

interface QuickEntryX extends QuickEntry {
  pending?: boolean;
}

const QUICK_ENTRIES: readonly QuickEntryX[] = [
  {
    title: "我要上报疑似诈骗",
    desc: "30 秒内完成快速上报，可匿名",
    icon: "siren",
    tone: "brand",
    cta: "即将上线",
    pending: true,
  },
  {
    title: "我的上报记录",
    desc: "跟踪事件状态、补充材料",
    icon: "clipboard-list",
    tone: "info",
    cta: "即将上线",
    pending: true,
  },
  {
    title: "常见诈骗手法",
    desc: "六大类典型套路与识别要点",
    icon: "book-open",
    tone: "warning",
    cta: "查看图谱",
    anchor: "fraud-types",
  },
];

function scrollToAnchor(id?: string): void {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

interface Hotline {
  number: string;
  numberDisplay: string;
  label: string;
  desc: string;
  icon: string;
  tone: "danger" | "warning" | "brand";
}

const HOTLINES: readonly Hotline[] = [
  {
    number: "tel:96110",
    numberDisplay: "96110",
    label: "国家反诈中心专线",
    desc: "全国统一 · 24h 接警",
    icon: "siren",
    tone: "danger",
  },
  {
    number: "tel:110",
    numberDisplay: "110",
    label: "公安报警",
    desc: "紧急情况首选",
    icon: "shield-alert",
    tone: "warning",
  },
  {
    number: "tel:022-23508110",
    numberDisplay: "022-2350 8110",
    label: "南开大学保卫处",
    desc: "校内事件协助 · 工作时间",
    icon: "info",
    tone: "brand",
  },
];
</script>

<template>
  <div class="student-home">
    <AppPageHeader
      badge="校园反诈 · 学生首页"
      :title="`${greeting}，${auth.me?.real_name ?? '同学'}`"
      subtitle="保持警惕，发现疑似诈骗及时上报，让校园更安全。一键报、有人审、有反馈。"
    />

    <!-- 英雄卡：30 秒上报 -->
    <AppCard
      tone="brand"
      padding="lg"
      class="student-home__hero"
    >
      <div class="student-home__hero-grid">
        <div class="student-home__hero-left">
          <span class="student-home__hero-eyebrow">
            <span class="dot" />
            30 秒上报 · 全程匿名可选
          </span>
          <h2 class="student-home__hero-title">
            一键上报，<br>
            快速联通<span class="student-home__hero-em">保卫处</span>与<span class="student-home__hero-em">辅导员</span>
          </h2>
          <p class="student-home__hero-lead">
            匿名上报选项可启用。上报后会进入审核流程，状态变更将通过站内信第一时间通知你；
            高风险上报自动加急。
          </p>
          <div class="student-home__hero-actions">
            <AppButton
              variant="secondary-on-brand"
              size="lg"
              :disabled="true"
              title="上报模块即将上线（业务模块组员负责）"
            >
              <AppIcon
                name="siren"
                :size="18"
              />
              立即上报
              <span class="student-home__hero-soon">即将上线</span>
            </AppButton>
            <AppButton
              variant="ghost-on-brand"
              size="lg"
              @click="scrollToAnchor('fraud-types')"
            >
              <AppIcon
                name="info"
                :size="18"
              />
              我可以匿名吗？
            </AppButton>
          </div>
          <ul class="student-home__hero-bullets">
            <li>
              <AppIcon
                name="shield-check"
                :size="14"
              />
              个人信息全程加密，仅司法授权可解
            </li>
            <li>
              <AppIcon
                name="activity"
                :size="14"
              />
              上报后 24 小时内必有人审核
            </li>
          </ul>
        </div>
        <div
          class="student-home__hero-illustration"
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 240 240"
            width="220"
            height="220"
          >
            <defs>
              <radialGradient
                id="home-orb"
                cx="50%"
                cy="50%"
                r="50%"
              >
                <stop
                  offset="0%"
                  stop-color="#ffffff"
                  stop-opacity="0.6"
                />
                <stop
                  offset="100%"
                  stop-color="#ffffff"
                  stop-opacity="0"
                />
              </radialGradient>
              <linearGradient
                id="home-shield"
                x1="0"
                y1="0"
                x2="0.6"
                y2="1"
              >
                <stop
                  offset="0%"
                  stop-color="#ffffff"
                />
                <stop
                  offset="100%"
                  stop-color="#f4d4dc"
                />
              </linearGradient>
            </defs>
            <circle
              cx="120"
              cy="120"
              r="110"
              fill="url(#home-orb)"
            />
            <circle
              cx="120"
              cy="120"
              r="92"
              fill="none"
              stroke="rgba(255,255,255,0.32)"
              stroke-dasharray="2 5"
            />
            <circle
              cx="120"
              cy="120"
              r="72"
              fill="none"
              stroke="rgba(230,179,73,0.35)"
              stroke-width="0.8"
              stroke-dasharray="0.8 2"
            />
            <!-- 八瓣莲花 -->
            <g
              transform="translate(120 120)"
              opacity="0.5"
            >
              <g
                v-for="i in 8"
                :key="i"
                :transform="`rotate(${(i - 1) * 45})`"
              >
                <path
                  d="M0 -56 C8 -42 8 -22 0 -10 C-8 -22 -8 -42 0 -56 Z"
                  fill="rgba(255,233,196,0.18)"
                  stroke="rgba(230,179,73,0.32)"
                  stroke-width="0.5"
                />
              </g>
            </g>
            <!-- 中央盾 -->
            <path
              d="M120 60 L156 76 V124 C156 154 138 174 120 184 C102 174 84 154 84 124 V76 Z"
              fill="url(#home-shield)"
            />
            <path
              d="M120 60 L156 76 V124 C156 154 138 174 120 184 C102 174 84 154 84 124 V76 Z"
              fill="none"
              stroke="rgba(134,38,51,0.36)"
              stroke-width="0.8"
            />
            <path
              d="M102 122 L116 136 L142 108"
              fill="none"
              stroke="#862633"
              stroke-width="6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>
    </AppCard>

    <!-- 快捷入口三连卡 -->
    <section class="student-home__quick">
      <article
        v-for="(q, i) in QUICK_ENTRIES"
        :key="q.title"
        class="student-home__quick-card"
        :class="`student-home__quick-card--${q.tone}`"
        :style="{ animationDelay: `${0.06 * i}s` }"
      >
        <span class="student-home__quick-icon">
          <AppIcon
            :name="(q.icon as never)"
            :size="22"
          />
        </span>
        <div class="student-home__quick-body">
          <h3>{{ q.title }}</h3>
          <p>{{ q.desc }}</p>
        </div>
        <AppButton
          variant="ghost"
          size="sm"
          :disabled="!!q.pending"
          @click="scrollToAnchor(q.anchor)"
        >
          {{ q.cta }}
          <AppIcon
            v-if="!q.pending"
            name="arrow-right"
            :size="14"
          />
        </AppButton>
      </article>
    </section>

    <!-- 双栏：诈骗类型 + 紧急联系 -->
    <section
      id="fraud-types"
      class="student-home__grid"
    >
      <AppCard
        padding="lg"
        :corner="true"
      >
        <template #header>
          <div>
            <h3>常见诈骗类型</h3>
            <small>遇到下列特征时请第一时间核实并上报。</small>
          </div>
        </template>
        <ul class="student-home__fraud">
          <li
            v-for="(f, i) in FRAUD_TYPES"
            :key="f.code"
            :class="[`student-home__fraud-item--${f.tone}`]"
            :style="{ animationDelay: `${0.04 * i}s` }"
          >
            <span class="student-home__fraud-icon">
              <AppIcon
                :name="(f.icon as never)"
                :size="18"
              />
            </span>
            <div class="student-home__fraud-body">
              <strong>{{ f.name }}</strong>
              <small>{{ f.desc }}</small>
            </div>
            <span
              class="student-home__fraud-tag"
              :class="`student-home__fraud-tag--${f.tone}`"
            >{{ f.trend }}</span>
          </li>
        </ul>
      </AppCard>

      <AppCard padding="lg">
        <template #header>
          <div>
            <h3>遇到紧急情况</h3>
            <small>电话直拨，越早处置越能止损。</small>
          </div>
        </template>
        <div class="student-home__emergency">
          <a
            v-for="h in HOTLINES"
            :key="h.numberDisplay"
            class="student-home__emergency-row"
            :class="`student-home__emergency-row--${h.tone}`"
            :href="h.number"
          >
            <span class="student-home__emergency-icon">
              <AppIcon
                :name="(h.icon as never)"
                :size="18"
              />
            </span>
            <div class="student-home__emergency-body">
              <strong>{{ h.numberDisplay }}</strong>
              <small>{{ h.label }} · {{ h.desc }}</small>
            </div>
            <AppIcon
              name="arrow-right"
              :size="14"
              class="student-home__emergency-arrow"
            />
          </a>
        </div>
        <div class="student-home__tip">
          <AppIcon
            name="sparkles"
            :size="14"
          />
          <span>
            凡是要求<strong>转账</strong>、<strong>刷信誉</strong>、<strong>远程屏幕共享</strong>的，
            几乎都是诈骗。
          </span>
        </div>
      </AppCard>
    </section>
  </div>
</template>

<style scoped>
.student-home {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── Hero ─────────────────────────────────────────────────────── */
.student-home__hero {
  overflow: hidden;
}

.student-home__hero-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-6);
  color: #fff;
  align-items: center;
}

@media (width <= 768px) {
  .student-home__hero-grid {
    grid-template-columns: 1fr;
  }

  .student-home__hero-illustration {
    display: none;
  }
}

.student-home__hero-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.student-home__hero-eyebrow {
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

.student-home__hero-eyebrow .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-gold-300);
  box-shadow: 0 0 8px rgb(230 179 73 / 80%);
}

.student-home__hero-title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: clamp(24px, 2.8vw, 36px);
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.student-home__hero-em {
  background: linear-gradient(120deg, var(--color-gold-200) 0%, var(--color-gold-400) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.student-home__hero-lead {
  margin: 0;
  color: rgb(255 255 255 / 80%);
  max-width: 560px;
  line-height: 1.75;
  font-size: var(--font-size-sm);
}

.student-home__hero-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-2);
}

.student-home__hero-soon {
  margin-left: 6px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: rgb(31 8 11 / 18%);
  color: var(--color-brand-700);
  font-size: 10.5px;
  letter-spacing: 0.12em;
  font-weight: var(--font-weight-bold);
  border: 1px solid rgb(134 38 51 / 22%);
}

.student-home__hero-bullets {
  list-style: none;
  margin: var(--space-3) 0 0;
  padding: var(--space-3) 0 0;
  border-top: 1px dashed rgb(255 233 196 / 22%);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-5);
  font-size: var(--font-size-xs);
  color: rgb(255 233 196 / 86%);
  letter-spacing: 0.02em;
}

.student-home__hero-bullets li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.student-home__hero-bullets li svg {
  color: var(--color-gold-300);
  flex-shrink: 0;
}

.student-home__hero-illustration svg {
  filter: drop-shadow(0 16px 32px rgb(0 0 0 / 28%));
  animation: hero-bob 6s ease-in-out infinite;
}

@keyframes hero-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@media (prefers-reduced-motion: reduce) {
  .student-home__hero-illustration svg { animation: none; }
}

/* ── 快捷入口 ─────────────────────────────────────────────────── */
.student-home__quick {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.student-home__quick-card {
  position: relative;
  display: grid;
  grid-template-columns: 48px 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-low);
  overflow: hidden;
  animation: feature-in 500ms var(--easing-out) both;
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
}

.student-home__quick-card::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 0 2px 2px 0;
}

.student-home__quick-card--brand::before { background: var(--color-brand-500); }
.student-home__quick-card--info::before { background: var(--color-info); }
.student-home__quick-card--warning::before { background: var(--color-warning); }

.student-home__quick-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
  border-color: var(--color-border-strong);
}

.student-home__quick-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
}

.student-home__quick-card--brand .student-home__quick-icon {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border-color: rgb(134 38 51 / 12%);
}

.student-home__quick-card--info .student-home__quick-icon {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}

.student-home__quick-card--warning .student-home__quick-icon {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  border-color: rgb(239 108 0 / 22%);
}

.student-home__quick-body h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
}

.student-home__quick-body p {
  margin: 4px 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.55;
}

@keyframes feature-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── 双栏 ─────────────────────────────────────────────────────── */
.student-home__grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-4);
}

@media (width <= 1024px) {
  .student-home__grid {
    grid-template-columns: 1fr;
  }
}

.student-home__grid h3 {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.student-home__grid small {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.student-home__fraud {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-3);
}

.student-home__fraud li {
  position: relative;
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  align-items: center;
  transition: all var(--duration-base) var(--easing-out);
  animation: feature-in 480ms var(--easing-out) both;
}

.student-home__fraud li:hover {
  border-color: var(--color-border-strong);
  transform: translateX(2px);
  box-shadow: var(--shadow-low);
}

.student-home__fraud-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.student-home__fraud-item--warning .student-home__fraud-icon {
  color: var(--color-warning);
  background: rgb(239 108 0 / 8%);
  border-color: rgb(239 108 0 / 18%);
}

.student-home__fraud-item--danger .student-home__fraud-icon {
  color: var(--color-danger);
  background: rgb(198 40 40 / 8%);
  border-color: rgb(198 40 40 / 18%);
}

.student-home__fraud-item--info .student-home__fraud-icon {
  color: var(--color-info);
  background: rgb(21 101 192 / 8%);
  border-color: rgb(21 101 192 / 18%);
}

.student-home__fraud-body strong {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}

.student-home__fraud-body small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 1px;
  display: block;
}

.student-home__fraud-tag {
  font-size: 10.5px;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.student-home__fraud-tag--warning {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
}

.student-home__fraud-tag--danger {
  background: rgb(198 40 40 / 12%);
  color: var(--color-danger);
}

.student-home__fraud-tag--info {
  background: rgb(21 101 192 / 12%);
  color: var(--color-info);
}

/* ── 紧急联系号牌 ─────────────────────────────────────────────── */
.student-home__emergency {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.student-home__emergency-row {
  display: grid;
  grid-template-columns: 36px 1fr 14px;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  text-decoration: none;
  color: inherit;
  transition: all var(--duration-base) var(--easing-out);
  position: relative;
  overflow: hidden;
}

.student-home__emergency-row::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}

.student-home__emergency-row--danger::before { background: var(--color-danger); }
.student-home__emergency-row--warning::before { background: var(--color-warning); }
.student-home__emergency-row--brand::before { background: var(--color-brand-500); }

.student-home__emergency-row:hover {
  background: var(--color-bg-soft);
  border-color: var(--color-border-strong);
  transform: translateX(2px);
}

.student-home__emergency-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-brand-50);
  color: var(--color-brand-700);
  border: 1px solid rgb(134 38 51 / 12%);
}

.student-home__emergency-row--danger .student-home__emergency-icon {
  background: rgb(198 40 40 / 10%);
  color: var(--color-danger);
  border-color: rgb(198 40 40 / 18%);
}

.student-home__emergency-row--warning .student-home__emergency-icon {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  border-color: rgb(239 108 0 / 22%);
}

.student-home__emergency-body strong {
  display: block;
  font-size: var(--font-size-lg);
  font-family: var(--font-family-mono);
  letter-spacing: 0.02em;
  color: var(--color-text-strong);
  font-variant-numeric: tabular-nums slashed-zero;
  font-feature-settings: "tnum" 1, "zero" 1;
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
}

.student-home__emergency-body small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.student-home__emergency-arrow {
  color: var(--color-text-tertiary);
  transition: transform var(--duration-base) var(--easing-out);
}

.student-home__emergency-row:hover .student-home__emergency-arrow {
  transform: translateX(2px);
  color: var(--color-brand-600);
}

.student-home__tip {
  margin-top: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgb(239 108 0 / 6%);
  border: 1px dashed rgb(239 108 0 / 32%);
  color: var(--color-warning);
  font-size: var(--font-size-xs);
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  line-height: 1.6;
}

.student-home__tip strong {
  color: var(--color-warning);
  font-weight: var(--font-weight-bold);
}

.student-home__tip span {
  color: var(--color-text);
}
</style>
