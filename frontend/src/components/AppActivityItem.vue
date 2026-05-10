<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

type Tone = "brand" | "info" | "success" | "warning" | "danger" | "neutral";

interface Props {
  icon?: string;
  tone?: Tone;
  title: string;
  meta?: string;
  time?: string;
}

withDefaults(defineProps<Props>(), {
  tone: "brand",
});
</script>

<template>
  <li
    class="activity"
    :class="`activity--${tone}`"
  >
    <span
      class="activity__rail"
      aria-hidden="true"
    />
    <span
      class="activity__dot"
      aria-hidden="true"
    >
      <AppIcon
        v-if="icon"
        :name="(icon as never)"
        :size="14"
        :stroke-width="2"
      />
    </span>
    <div class="activity__body">
      <p class="activity__title">
        {{ title }}
      </p>
      <p
        v-if="meta"
        class="activity__meta"
      >
        {{ meta }}
      </p>
    </div>
    <span
      v-if="time"
      class="activity__time"
    >
      {{ time }}
    </span>
  </li>
</template>

<style scoped>
.activity {
  position: relative;
  display: grid;
  grid-template-columns: 32px 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px dashed var(--color-border);
}

.activity:last-child {
  border-bottom: none;
}

/* 时间线竖线（每行的左侧穿过 dot 中心） */
.activity__rail {
  position: absolute;
  left: 15px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(
    to bottom,
    transparent 0,
    var(--color-border) 12px,
    var(--color-border) calc(100% - 12px),
    transparent 100%
  );
  z-index: 0;
}

.activity:first-child .activity__rail { top: 50%; }
.activity:last-child .activity__rail { bottom: 50%; }
.activity:only-child .activity__rail { display: none; }

.activity__dot {
  position: relative;
  z-index: 1;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-brand-50);
  color: var(--color-brand-600);
  border: 1px solid rgb(134 38 51 / 14%);
  box-shadow: 0 0 0 3px var(--color-surface);
}

.activity--info .activity__dot {
  background: rgb(21 101 192 / 10%);
  color: var(--color-info);
  border-color: rgb(21 101 192 / 18%);
}

.activity--success .activity__dot {
  background: rgb(46 125 50 / 10%);
  color: var(--color-success);
  border-color: rgb(46 125 50 / 18%);
}

.activity--warning .activity__dot {
  background: rgb(239 108 0 / 12%);
  color: var(--color-warning);
  border-color: rgb(239 108 0 / 22%);
}

.activity--danger .activity__dot {
  background: rgb(198 40 40 / 10%);
  color: var(--color-danger);
  border-color: rgb(198 40 40 / 18%);
}

.activity--neutral .activity__dot {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

.activity__body {
  min-width: 0;
}

.activity__title {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.01em;
}

.activity__meta {
  margin: 2px 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
  letter-spacing: 0.02em;
}

.activity__time {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-tertiary);
  white-space: nowrap;
  font-feature-settings: "tnum" 1;
}
</style>
