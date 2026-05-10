<script setup lang="ts">
import { computed } from "vue";
import AppIcon from "./AppIcon.vue";

type IconTone = "brand" | "info" | "success" | "warning" | "danger" | "neutral";

interface Props {
  label: string;
  value: string | number;
  hint?: string;
  icon?: string;
  tone?: IconTone;
  delta?: number;
  deltaLabel?: string;
  loading?: boolean;
  /** 当 value 为「—」「-」「待接入」等占位符时，以更弱的视觉显示 */
  placeholder?: string;
  /** 可选的迷你趋势点（0-100），最多 12 个，自动渲染为 sparkline */
  trend?: readonly number[];
}

const props = withDefaults(defineProps<Props>(), {
  tone: "brand",
  loading: false,
  placeholder: "",
});

const isPlaceholder = computed<boolean>(() => {
  if (props.loading) return false;
  const v = String(props.value ?? "").trim();
  if (!v) return true;
  if (v === "—" || v === "-" || v === "待接入" || v === "—") return true;
  return false;
});

const sparkPath = computed<string>(() => {
  const t = props.trend;
  if (!t || t.length < 2) return "";
  const W = 88;
  const H = 24;
  const max = Math.max(...t, 1);
  const min = Math.min(...t, 0);
  const span = max - min || 1;
  const step = W / (t.length - 1);
  return t
    .map((v, i) => {
      const x = i * step;
      const y = H - ((v - min) / span) * H;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
});
</script>

<template>
  <article
    class="stat-card"
    :class="`stat-card--${tone}`"
  >
    <div class="stat-card__top">
      <span class="stat-card__label">{{ label }}</span>
      <span
        v-if="icon"
        class="stat-card__icon"
        aria-hidden="true"
      >
        <AppIcon
          :name="(icon as never)"
          :size="18"
        />
      </span>
    </div>
    <div
      v-if="loading"
      class="stat-card__skeleton"
      aria-hidden="true"
    />
    <strong
      v-else
      class="stat-card__value"
      :class="{ 'stat-card__value--placeholder': isPlaceholder }"
    >
      <template v-if="isPlaceholder">
        <span class="stat-card__value-dash">—</span>
        <small v-if="placeholder">{{ placeholder }}</small>
      </template>
      <template v-else>
        {{ value }}
      </template>
    </strong>
    <div class="stat-card__bottom">
      <span
        v-if="typeof delta === 'number'"
        class="stat-card__delta"
        :class="{ 'is-up': delta > 0, 'is-down': delta < 0 }"
      >
        <span aria-hidden="true">
          {{ delta > 0 ? "▲" : delta < 0 ? "▼" : "·" }}
        </span>
        {{ Math.abs(delta) }}{{ deltaLabel ? ` ${deltaLabel}` : "" }}
      </span>
      <span
        v-if="hint"
        class="stat-card__hint"
      >
        {{ hint }}
      </span>
      <svg
        v-if="sparkPath"
        class="stat-card__spark"
        viewBox="0 0 88 24"
        aria-hidden="true"
      >
        <path
          :d="sparkPath"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          :d="`${sparkPath} L88 24 L0 24 Z`"
          fill="currentColor"
          opacity="0.12"
        />
      </svg>
    </div>
  </article>
</template>

<style scoped>
.stat-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-low);
  overflow: hidden;
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
}

.stat-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 32px;
  height: 3px;
  border-radius: 0 0 4px 0;
  background: var(--color-brand-500);
  opacity: 0.9;
}

.stat-card--info::before { background: var(--color-info); }
.stat-card--success::before { background: var(--color-success); }
.stat-card--warning::before { background: var(--color-warning); }
.stat-card--danger::before { background: var(--color-danger); }
.stat-card--neutral::before { background: var(--color-neutral-400); }

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-mid);
  border-color: var(--color-border-strong);
}

.stat-card::after {
  content: "";
  position: absolute;
  inset: auto -20% -50% auto;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  filter: blur(56px);
  opacity: 0.18;
  pointer-events: none;
  z-index: 0;
}

.stat-card--brand::after { background: var(--color-brand-500); }
.stat-card--info::after { background: var(--color-info); }
.stat-card--success::after { background: var(--color-success); }
.stat-card--warning::after { background: var(--color-warning); }
.stat-card--danger::after { background: var(--color-danger); }
.stat-card--neutral::after { background: var(--color-neutral-400); }

.stat-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.stat-card__label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.04em;
}

.stat-card__icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-brand-50);
  color: var(--color-brand-600);
  border: 1px solid rgb(134 38 51 / 12%);
}

.stat-card--info .stat-card__icon {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}

.stat-card--success .stat-card__icon {
  background: rgb(46 125 50 / 10%);
  color: var(--color-success);
  border-color: rgb(46 125 50 / 18%);
}

.stat-card--warning .stat-card__icon {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  border-color: rgb(239 108 0 / 22%);
}

.stat-card--danger .stat-card__icon {
  background: rgb(198 40 40 / 10%);
  color: var(--color-danger);
  border-color: rgb(198 40 40 / 18%);
}

.stat-card--neutral .stat-card__icon {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

.stat-card__value {
  position: relative;
  z-index: 1;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.02em;
  color: var(--color-text-strong);
  line-height: 1.05;
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-2);
}

.stat-card__value--placeholder {
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
}

.stat-card__value-dash {
  font-family: var(--font-family-serif);
  font-size: var(--font-size-3xl);
  letter-spacing: 0;
  color: var(--color-neutral-300);
  line-height: 0.9;
}

.stat-card__value--placeholder small {
  font-family: var(--font-family-sans);
  font-size: 11px;
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
  border: 1px solid var(--color-border);
}

.stat-card__bottom {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.stat-card__delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
  font-weight: var(--font-weight-medium);
}

.stat-card__delta.is-up {
  color: var(--color-success);
  background: rgb(46 125 50 / 10%);
}

.stat-card__delta.is-down {
  color: var(--color-danger);
  background: rgb(198 40 40 / 10%);
}

.stat-card__spark {
  margin-left: auto;
  width: 88px;
  height: 24px;
  color: var(--color-brand-500);
  flex-shrink: 0;
}

.stat-card--info .stat-card__spark { color: var(--color-info); }
.stat-card--success .stat-card__spark { color: var(--color-success); }
.stat-card--warning .stat-card__spark { color: var(--color-warning); }
.stat-card--danger .stat-card__spark { color: var(--color-danger); }

.stat-card__skeleton {
  position: relative;
  z-index: 1;
  width: 60%;
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-neutral-100) 0%,
    var(--color-neutral-200) 50%,
    var(--color-neutral-100) 100%
  );
  background-size: 200% 100%;
  animation: stat-shimmer 1.4s ease-in-out infinite;
}

@keyframes stat-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
