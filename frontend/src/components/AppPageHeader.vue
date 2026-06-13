<script setup lang="ts">
interface Props {
  title: string;
  subtitle?: string;
  /** 标题左侧的小印章字（如概览、审计、司法） */
  badge?: string;
}

withDefaults(defineProps<Props>(), { subtitle: "", badge: "" });
</script>

<template>
  <header class="app-page-header">
    <div class="app-page-header__main">
      <div
        v-if="badge"
        class="app-page-header__badge"
      >
        <span class="app-page-header__badge-dot" />
        <span>{{ badge }}</span>
      </div>
      <h1 class="app-page-header__title">
        {{ title }}
      </h1>
      <p
        v-if="subtitle"
        class="app-page-header__subtitle"
      >
        {{ subtitle }}
      </p>
    </div>
    <div
      v-if="$slots.actions"
      class="app-page-header__actions"
    >
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.app-page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 0 var(--space-4);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.app-page-header__main {
  min-width: 0;
}

.app-page-header__badge {
  display: block;
  margin-bottom: var(--space-1);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  letter-spacing: 0.02em;
}

.app-page-header__badge-dot {
  display: none;
}

.app-page-header__title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: clamp(22px, 2.5vw, 28px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.app-page-header__subtitle {
  margin: var(--space-1) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  max-width: 56ch;
}

.app-page-header__actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}
</style>
