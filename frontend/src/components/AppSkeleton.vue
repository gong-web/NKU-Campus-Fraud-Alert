<script setup lang="ts">
interface Props {
  rows?: number;
  height?: string;
  width?: string;
  rounded?: boolean;
}

withDefaults(defineProps<Props>(), {
  rows: 3,
  height: "16px",
  width: "100%",
  rounded: true,
});
</script>

<template>
  <div
    class="app-skeleton"
    role="status"
    aria-live="polite"
    aria-busy="true"
  >
    <div
      v-for="i in rows"
      :key="i"
      class="app-skeleton__bar"
      :class="{ 'is-rounded': rounded }"
      :style="{ height, width: i === rows && rows > 1 ? '60%' : width }"
    />
    <span class="app-skeleton__sr">加载中…</span>
  </div>
</template>

<style scoped>
.app-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) 0;
}

.app-skeleton__bar {
  background: linear-gradient(
    90deg,
    var(--color-neutral-100) 0%,
    var(--color-neutral-200) 50%,
    var(--color-neutral-100) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.app-skeleton__bar.is-rounded {
  border-radius: var(--radius-sm);
}

.app-skeleton__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
