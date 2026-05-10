<script setup lang="ts">
interface Props {
  /** 视觉强度：plain（默认）、brand（品牌渐变）、surface-low（更轻底）、glass（玻璃）。 */
  tone?: "plain" | "brand" | "surface-low" | "glass";
  padding?: "sm" | "md" | "lg";
  /** 加 hover 抬升动画。 */
  interactive?: boolean;
  /** 显示左上角的金箔角线（仅在 plain/glass 调）。 */
  corner?: boolean;
}

withDefaults(defineProps<Props>(), {
  tone: "plain",
  padding: "md",
  interactive: false,
  corner: false,
});
</script>

<template>
  <section
    class="app-card"
    :class="[
      `app-card--${tone}`,
      `app-card--p-${padding}`,
      { 'app-card--interactive': interactive, 'app-card--corner': corner },
    ]"
  >
    <span
      v-if="corner"
      class="app-card__corner"
      aria-hidden="true"
    />
    <header
      v-if="$slots.header"
      class="app-card__header"
    >
      <slot name="header" />
    </header>
    <div class="app-card__body">
      <slot />
    </div>
    <footer
      v-if="$slots.footer"
      class="app-card__footer"
    >
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.app-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-low);
  transition:
    transform var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    border-color var(--duration-base) var(--easing-out);
}

/* 浅色卡片：顶部一条极细高光，让卡片有「真实纸张」的反光 */
.app-card--plain::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background:
    linear-gradient(
      180deg,
      rgb(255 255 255 / 70%) 0,
      transparent 1px
    );
}

.app-card--p-sm {
  padding: var(--space-3) var(--space-4);
}

.app-card--p-md {
  padding: var(--space-4) var(--space-5);
}

.app-card--p-lg {
  padding: var(--space-5) var(--space-6);
}

.app-card--brand {
  background: var(--gradient-haihe);
  border-color: transparent;
  color: var(--color-neutral-0);
  box-shadow:
    var(--shadow-glow-brand),
    inset 0 1px 0 rgb(255 255 255 / 10%);
  overflow: hidden;
}

.app-card--brand::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    radial-gradient(at 80% 0%, rgb(230 179 73 / 22%), transparent 55%),
    radial-gradient(at 0% 100%, rgb(255 255 255 / 14%), transparent 60%);
  pointer-events: none;
}

.app-card--brand::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background-image:
    var(--pattern-lotus),
    var(--pattern-noise);
  background-size: 280px 280px, 160px 160px;
  background-position: 100% 100%, 0 0;
  background-repeat: no-repeat, repeat;
  opacity: 0.36;
  mix-blend-mode: overlay;
  pointer-events: none;
}

.app-card--surface-low {
  background: var(--color-bg);
  box-shadow: none;
  border-color: var(--color-border-soft);
}

.app-card--glass {
  background: var(--glass-surface);
  backdrop-filter: blur(var(--glass-blur));
  border-color: rgb(255 255 255 / 56%);
  box-shadow: var(--shadow-mid);
}

.app-card--corner .app-card__corner {
  position: absolute;
  top: -1px;
  left: -1px;
  width: 18px;
  height: 18px;
  border-top: 2px solid var(--color-gold-400);
  border-left: 2px solid var(--color-gold-400);
  border-top-left-radius: var(--radius-lg);
  pointer-events: none;
  filter: drop-shadow(0 0 6px rgb(230 179 73 / 32%));
}

.app-card--interactive {
  cursor: pointer;
}

.app-card--interactive:hover {
  transform: translateY(-2px);
  box-shadow:
    var(--shadow-mid),
    0 0 0 3px rgb(134 38 51 / 8%);
  border-color: var(--color-brand-300);
}

.app-card__header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.app-card__body {
  position: relative;
  z-index: 1;
}

.app-card__footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.app-card--brand .app-card__footer {
  border-top-color: rgb(255 255 255 / 18%);
}
</style>
