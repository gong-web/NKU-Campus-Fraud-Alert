<script setup lang="ts">
interface Props {
  status: "info" | "success" | "warning" | "danger" | "neutral";
  text: string;
  /** 预警三级专用语义；与 status 二选一 */
  warnLevel?: "info" | "warning" | "urgent";
}

const props = defineProps<Props>();

function clsFor(): string {
  if (props.warnLevel) return `warn-${props.warnLevel}`;
  return props.status;
}
</script>

<template>
  <span
    class="app-status-tag"
    :class="`app-status-tag--${clsFor()}`"
  >
    <span
      class="app-status-tag__dot"
      aria-hidden="true"
    />
    {{ text }}
  </span>
</template>

<style scoped>
.app-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 8px;
  font-size: 11.5px;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.04em;
  border-radius: var(--radius-pill);
  border: 1px solid currentcolor;
  background: transparent;
  line-height: 1.3;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.app-status-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentcolor;
  box-shadow: 0 0 0 2px rgb(255 255 255 / 70%);
}

.app-status-tag--info {
  color: var(--color-info);
  background: rgb(21 101 192 / 8%);
  border-color: rgb(21 101 192 / 24%);
}

.app-status-tag--success {
  color: var(--color-success);
  background: rgb(46 125 50 / 8%);
  border-color: rgb(46 125 50 / 24%);
}

.app-status-tag--warning {
  color: var(--color-warning);
  background: rgb(239 108 0 / 10%);
  border-color: rgb(239 108 0 / 26%);
}

.app-status-tag--danger {
  color: var(--color-danger);
  background: rgb(198 40 40 / 8%);
  border-color: rgb(198 40 40 / 26%);
}

.app-status-tag--neutral {
  color: var(--color-neutral-600);
  background: var(--color-neutral-100);
  border-color: var(--color-border);
}

/* PRD 6.1 预警三级 */
.app-status-tag--warn-info {
  color: var(--color-warn-info);
  background: rgb(25 118 210 / 10%);
  border-color: rgb(25 118 210 / 26%);
}

.app-status-tag--warn-warning {
  color: var(--color-warn-warning);
  background: rgb(239 108 0 / 10%);
  border-color: rgb(239 108 0 / 26%);
}

.app-status-tag--warn-urgent {
  color: var(--color-warn-urgent);
  background: rgb(198 40 40 / 10%);
  border-color: rgb(198 40 40 / 28%);
  animation: tag-urgent-pulse 2.4s ease-in-out infinite;
}

@keyframes tag-urgent-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgb(198 40 40 / 0%); }
  50% { box-shadow: 0 0 0 4px rgb(198 40 40 / 14%); }
}

@media (prefers-reduced-motion: reduce) {
  .app-status-tag--warn-urgent { animation: none; }
}
</style>
