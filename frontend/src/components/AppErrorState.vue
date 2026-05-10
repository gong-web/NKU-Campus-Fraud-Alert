<script setup lang="ts">
interface Props {
  title?: string;
  hint?: string;
  retryLabel?: string;
}

withDefaults(defineProps<Props>(), {
  title: "出错了",
  hint: "请稍后再试，或联系管理员。",
  retryLabel: "重试",
});

defineEmits<{ retry: [] }>();
</script>

<template>
  <div
    class="app-error"
    role="alert"
  >
    <svg
      viewBox="0 0 64 64"
      width="80"
      height="80"
      aria-hidden="true"
    >
      <circle
        cx="32"
        cy="32"
        r="28"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
      />
      <line
        x1="22"
        y1="22"
        x2="42"
        y2="42"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
      />
      <line
        x1="42"
        y1="22"
        x2="22"
        y2="42"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
      />
    </svg>
    <h3>{{ title }}</h3>
    <p>{{ hint }}</p>
    <button
      type="button"
      class="app-error__retry"
      @click="$emit('retry')"
    >
      {{ retryLabel }}
    </button>
  </div>
</template>

<style scoped>
.app-error {
  text-align: center;
  padding: var(--space-8) var(--space-5);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.app-error svg {
  width: 64px;
  height: 64px;
  color: var(--color-danger);
  background: rgb(198 40 40 / 8%);
  border: 1px dashed rgb(198 40 40 / 32%);
  border-radius: 50%;
  padding: 12px;
  box-sizing: content-box;
  margin-bottom: var(--space-4);
}

.app-error h3 {
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  margin: 0 0 var(--space-2);
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.01em;
}

.app-error p {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-4);
  font-size: var(--font-size-sm);
  line-height: 1.6;
  max-width: 360px;
}

.app-error__retry {
  background: linear-gradient(180deg, #9c2c3c 0%, #862633 100%);
  color: var(--color-neutral-0);
  border: 1px solid var(--color-brand-600);
  padding: 8px var(--space-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 40px;
  font-family: inherit;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  letter-spacing: 0.02em;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 14%) inset,
    var(--shadow-glow-brand);
  transition: all var(--duration-base) var(--easing-out);
}

.app-error__retry:hover {
  background: linear-gradient(180deg, #ad3346 0%, #8e2937 100%);
}
</style>
