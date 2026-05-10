<script setup lang="ts">
interface Props {
  title: string;
  subtitle?: string;
  /** 标题左侧的小印章字（如「概览」「审计」「司法」） */
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
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) 0 var(--space-5);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
  animation: page-header-in 520ms var(--easing-out) both;
}

@keyframes page-header-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .app-page-header { animation: none; }
}

.app-page-header::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: linear-gradient(
    to right,
    var(--color-brand-500) 0,
    var(--color-brand-500) 56px,
    var(--color-gold-400) 56px,
    var(--color-gold-400) 72px,
    var(--color-border) 72px,
    var(--color-border) 100%
  );
  border-radius: 1px;
}

.app-page-header__main {
  min-width: 0;
}

.app-page-header__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 7px;
  margin-bottom: var(--space-3);
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, var(--color-brand-50) 0%, #fad6dc 100%);
  border: 1px solid rgb(134 38 51 / 22%);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: var(--font-weight-bold);
  color: var(--color-brand-700);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 1px 3px -1px rgb(134 38 51 / 18%);
}

.app-page-header__badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-brand-500);
  box-shadow: 0 0 0 2px rgb(134 38 51 / 18%);
}

.app-page-header__title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: clamp(28px, 3vw, 36px);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
  letter-spacing: -0.025em;
  line-height: 1.15;
}

.app-page-header__subtitle {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
  max-width: 720px;
}

.app-page-header__actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}
</style>
