<script setup lang="ts">
interface Props {
  title?: string | undefined;
  hint?: string | undefined;
  illustration?: "default" | "search" | "warning" | undefined;
}

withDefaults(defineProps<Props>(), {
  title: "暂无数据",
  hint: "",
  illustration: "default",
});
</script>

<template>
  <div
    class="app-empty"
    role="status"
  >
    <div
      class="app-empty__art"
      aria-hidden="true"
    >
      <svg
        v-if="illustration === 'search'"
        viewBox="0 0 64 64"
        width="96"
        height="96"
        fill="none"
      >
        <circle
          cx="28"
          cy="28"
          r="18"
          stroke="currentColor"
          stroke-width="3"
        />
        <line
          x1="42"
          y1="42"
          x2="56"
          y2="56"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
        />
      </svg>
      <svg
        v-else-if="illustration === 'warning'"
        viewBox="0 0 64 64"
        width="96"
        height="96"
        fill="none"
      >
        <path
          d="M32 6 L60 56 L4 56 Z"
          stroke="currentColor"
          stroke-width="3"
          stroke-linejoin="round"
        />
        <line
          x1="32"
          y1="24"
          x2="32"
          y2="40"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
        />
        <circle
          cx="32"
          cy="48"
          r="2"
          fill="currentColor"
        />
      </svg>
      <svg
        v-else
        viewBox="0 0 64 64"
        width="96"
        height="96"
        fill="none"
      >
        <rect
          x="10"
          y="14"
          width="44"
          height="36"
          rx="4"
          stroke="currentColor"
          stroke-width="3"
        />
        <line
          x1="10"
          y1="26"
          x2="54"
          y2="26"
          stroke="currentColor"
          stroke-width="3"
        />
      </svg>
    </div>
    <h3 class="app-empty__title">
      {{ title }}
    </h3>
    <p
      v-if="hint"
      class="app-empty__hint"
    >
      {{ hint }}
    </p>
    <div
      v-if="$slots.action"
      class="app-empty__action"
    >
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.app-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-8) var(--space-5);
  color: var(--color-text-secondary);
}

.app-empty__art {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, var(--color-brand-50), transparent 70%),
    var(--color-bg-soft);
  border: 1px dashed var(--color-border-strong);
  color: var(--color-brand-300);
  margin-bottom: var(--space-4);
}

.app-empty__art svg {
  width: 56px;
  height: 56px;
}

.app-empty__title {
  margin: 0 0 var(--space-2);
  font-family: var(--font-family-serif);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: -0.01em;
}

.app-empty__hint {
  margin: 0 0 var(--space-4);
  font-size: var(--font-size-sm);
  max-width: 360px;
  line-height: 1.6;
}
</style>
