<script setup lang="ts">
import { computed } from "vue";

type Variant = "primary" | "secondary" | "ghost" | "ghost-on-brand" | "secondary-on-brand" | "danger" | "gold";
type Size = "sm" | "md" | "lg";

interface Props {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  block?: boolean;
  type?: "button" | "submit";
  ariaLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
  size: "md",
  loading: false,
  disabled: false,
  block: false,
  type: "button",
});

defineEmits<{ click: [evt: MouseEvent] }>();

const cls = computed(() => [
  "app-btn",
  `app-btn--${props.variant}`,
  `app-btn--${props.size}`,
  {
    "app-btn--block": props.block,
    "app-btn--loading": props.loading,
  },
]);
</script>

<template>
  <button
    :type="type"
    :class="cls"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :aria-label="ariaLabel"
    @click="$emit('click', $event)"
  >
    <span
      v-if="loading"
      class="app-btn__spinner"
      aria-hidden="true"
    />
    <slot />
  </button>
</template>

<style scoped>
.app-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.02em;
  cursor: pointer;
  position: relative;
  transition:
    background var(--duration-base) var(--easing-out),
    color var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    transform var(--duration-fast) var(--easing-out);
  min-height: 40px;
  padding-inline: var(--space-4);
  white-space: nowrap;
}

.app-btn:active:not(:disabled) {
  transform: translateY(1px) scale(0.99);
  transition-duration: 80ms;
}

.app-btn--sm {
  font-size: var(--font-size-sm);
  min-height: 32px;
  padding-inline: var(--space-3);
  border-radius: var(--radius-sm);
}

.app-btn--md {
  font-size: var(--font-size-sm);
}

.app-btn--lg {
  font-size: var(--font-size-md);
  min-height: 48px;
  padding-inline: var(--space-5);
}

.app-btn--block {
  width: 100%;
}

/* ── 主 · 南开主紫 ─────────────────────────────────────────── */
.app-btn--primary {
  background: linear-gradient(180deg, #9c2c3c 0%, #862633 100%);
  color: var(--color-neutral-0);
  border-color: var(--color-brand-600);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 14%) inset,
    var(--shadow-glow-brand);
}

.app-btn--primary:hover:not(:disabled) {
  background: linear-gradient(180deg, #ad3346 0%, #8e2937 100%);
  border-color: var(--color-brand-700);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 16%) inset,
    var(--shadow-glow-brand),
    0 0 0 3px rgb(134 38 51 / 14%);
}

.app-btn--primary:active:not(:disabled) {
  background: var(--color-brand-700);
}

/* ── 次 · 浅底深字 ─────────────────────────────────────────── */
.app-btn--secondary {
  background: var(--color-surface);
  color: var(--color-text-strong);
  border-color: var(--color-border-strong);
  box-shadow:
    var(--shadow-low),
    inset 0 1px 0 rgb(255 255 255 / 60%);
}

.app-btn--secondary:hover:not(:disabled) {
  border-color: var(--color-brand-400);
  background: var(--color-bg);
  color: var(--color-brand-700);
}

/* ── Ghost ─────────────────────────────────────────────────── */
.app-btn--ghost {
  background: transparent;
  color: var(--color-link);
  border-color: transparent;
  font-weight: var(--font-weight-medium);
}

.app-btn--ghost:hover:not(:disabled) {
  background: var(--color-brand-50);
  color: var(--color-brand-700);
}

/* ── Ghost on Brand（深色英雄卡背景上的次按钮）──────────────── */
.app-btn--ghost-on-brand {
  background: rgb(255 255 255 / 6%);
  color: rgb(255 233 196 / 92%);
  border-color: rgb(255 233 196 / 24%);
  font-weight: var(--font-weight-semibold);
  backdrop-filter: blur(8px);
}

.app-btn--ghost-on-brand:hover:not(:disabled) {
  background: rgb(255 255 255 / 12%);
  color: #fff;
  border-color: rgb(230 179 73 / 56%);
  box-shadow:
    0 0 0 3px rgb(230 179 73 / 14%),
    inset 0 1px 0 rgb(255 255 255 / 18%);
}

/* ── Secondary on Brand（深色英雄卡背景上的米白主操作）──────── */
.app-btn--secondary-on-brand {
  background: linear-gradient(180deg, #fffaf0 0%, #fdecd0 100%);
  color: var(--color-brand-700);
  border-color: rgb(230 179 73 / 56%);
  font-weight: var(--font-weight-semibold);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 8px 24px -10px rgb(31 8 11 / 56%),
    0 0 0 1px rgb(31 8 11 / 8%);
}

.app-btn--secondary-on-brand:hover:not(:disabled) {
  background: linear-gradient(180deg, #fff 0%, #fdf4dc 100%);
  border-color: var(--color-gold-400);
  color: var(--color-brand-800);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 96%) inset,
    0 12px 28px -10px rgb(31 8 11 / 64%),
    0 0 0 3px rgb(230 179 73 / 22%);
}

/* ── Danger ─────────────────────────────────────────────────── */
.app-btn--danger {
  background: linear-gradient(180deg, #d73a3a 0%, #c62828 100%);
  color: var(--color-neutral-0);
  border-color: #b21e1e;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 14%) inset,
    0 12px 32px -8px rgb(198 40 40 / 36%);
}

.app-btn--danger:hover:not(:disabled) {
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 16%) inset,
    0 16px 36px -8px rgb(198 40 40 / 48%),
    0 0 0 3px rgb(198 40 40 / 14%);
}

/* ── Gold（南开奖章金 · 罕用） ─────────────────────────────── */
.app-btn--gold {
  background: var(--gradient-gold);
  color: #2d1f06;
  border-color: var(--color-gold-600);
  font-weight: var(--font-weight-bold);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 32%) inset,
    var(--shadow-glow-gold);
}

.app-btn--gold:hover:not(:disabled) {
  filter: brightness(1.04);
}

/* ── Disabled ─────────────────────────────────────────────── */
.app-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  filter: saturate(0.6);
}

.app-btn:disabled:active {
  transform: none;
}

.app-btn__spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentcolor;
  border-top-color: transparent;
  animation: app-btn-spin 720ms linear infinite;
}

@keyframes app-btn-spin {
  to { transform: rotate(360deg); }
}
</style>
