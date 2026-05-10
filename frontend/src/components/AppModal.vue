<script setup lang="ts">
import { onMounted, onUnmounted, watch } from "vue";

interface Props {
  modelValue: boolean;
  title?: string;
  width?: string;
  closeOnBackdrop?: boolean;
  closeOnEsc?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "",
  width: "480px",
  closeOnBackdrop: true,
  closeOnEsc: true,
});

const emit = defineEmits<{
  "update:modelValue": [v: boolean];
  close: [];
}>();

function close(): void {
  emit("update:modelValue", false);
  emit("close");
}

function onKeydown(e: KeyboardEvent): void {
  if (props.closeOnEsc && e.key === "Escape" && props.modelValue) close();
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));

watch(
  () => props.modelValue,
  (open) => {
    document.body.style.overflow = open ? "hidden" : "";
  },
);
</script>

<template>
  <Teleport to="body">
    <Transition name="app-modal">
      <div
        v-if="modelValue"
        class="app-modal"
        role="dialog"
        aria-modal="true"
        :aria-label="title || '对话框'"
        @click.self="closeOnBackdrop && close()"
      >
        <div
          class="app-modal__panel"
          :style="{ width }"
          role="document"
        >
          <header
            v-if="title || $slots.header"
            class="app-modal__header"
          >
            <slot name="header">
              <h2 class="app-modal__title">
                {{ title }}
              </h2>
            </slot>
            <button
              type="button"
              class="app-modal__close"
              aria-label="关闭"
              @click="close"
            >
              ×
            </button>
          </header>
          <section class="app-modal__body">
            <slot />
          </section>
          <footer
            v-if="$slots.footer"
            class="app-modal__footer"
          >
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.app-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(at 30% 30%, rgb(31 8 11 / 56%), transparent 70%),
    rgb(15 18 28 / 56%);
  backdrop-filter: blur(6px);
  z-index: var(--z-modal);
  padding: var(--space-4);
}

.app-modal__panel {
  position: relative;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow:
    var(--shadow-overlay),
    inset 0 1px 0 rgb(255 255 255 / 70%);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 64px);
  overflow: hidden;
}

.app-modal__panel::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    to right,
    var(--color-brand-500) 0,
    var(--color-brand-500) 64px,
    transparent 64px
  );
}

.app-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.app-modal__title {
  margin: 0;
  font-family: var(--font-family-serif);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.01em;
  color: var(--color-text-strong);
}

.app-modal__close {
  background: transparent;
  border: 1px solid transparent;
  font-size: 18px;
  line-height: 1;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base) var(--easing-out);
}

.app-modal__close:hover {
  background: var(--color-neutral-100);
  border-color: var(--color-border);
  color: var(--color-danger);
}

.app-modal__body {
  padding: var(--space-5) var(--space-6);
  overflow-y: auto;
}

.app-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-soft);
}

/* 进出过渡 */
.app-modal-enter-active,
.app-modal-leave-active {
  transition: opacity var(--duration-slow) var(--easing-out);
}

.app-modal-enter-from,
.app-modal-leave-to {
  opacity: 0;
}

.app-modal-enter-active .app-modal__panel,
.app-modal-leave-active .app-modal__panel {
  transition:
    transform var(--duration-slow) var(--easing-out),
    opacity var(--duration-slow) var(--easing-out);
}

.app-modal-enter-from .app-modal__panel {
  transform: translateY(12px) scale(0.97);
  opacity: 0;
}

.app-modal-leave-to .app-modal__panel {
  transform: translateY(8px) scale(0.98);
  opacity: 0;
}
</style>
