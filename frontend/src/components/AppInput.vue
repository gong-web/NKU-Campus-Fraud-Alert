<script setup lang="ts">
import { computed } from "vue";

interface Props {
  modelValue: string;
  label?: string;
  placeholder?: string;
  type?: "text" | "password" | "email" | "tel" | "search" | "textarea";
  required?: boolean;
  disabled?: boolean;
  error?: string;
  hint?: string;
  autocomplete?: string;
  maxlength?: number;
  ariaLabel?: string;
  /** 输入框前置图标（Lucide name 字符串） */
  prefixIcon?: string;
  /** textarea 行数 */
  rows?: number;
}

withDefaults(defineProps<Props>(), {
  label: "",
  placeholder: "",
  type: "text",
  required: false,
  disabled: false,
  error: "",
  hint: "",
  prefixIcon: "",
  rows: 4,
});

defineEmits<{
  "update:modelValue": [v: string];
  blur: [];
  focus: [];
}>();

const inputId = computed(
  () => `app-input-${Math.random().toString(36).slice(2, 8)}`,
);
</script>

<template>
  <div
    class="app-input"
    :class="{ 'has-error': !!error, 'has-prefix': !!prefixIcon }"
  >
    <label
      v-if="label"
      :for="inputId"
      class="app-input__label"
    >
      {{ label }}
      <span
        v-if="required"
        aria-hidden="true"
        class="app-input__required"
      >*</span>
    </label>
    <div class="app-input__wrap">
      <span
        v-if="prefixIcon"
        class="app-input__prefix"
        aria-hidden="true"
      >
        <slot name="prefix" />
      </span>
      <textarea
        v-if="type === 'textarea'"
        :id="inputId"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :aria-required="required || undefined"
        :aria-invalid="!!error || undefined"
        :aria-describedby="hint || error ? `${inputId}-help` : undefined"
        :aria-label="ariaLabel"
        :maxlength="maxlength"
        :rows="rows"
        class="app-input__field app-input__field--area"
        @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      />
      <input
        v-else
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :aria-required="required || undefined"
        :aria-invalid="!!error || undefined"
        :aria-describedby="hint || error ? `${inputId}-help` : undefined"
        :aria-label="ariaLabel"
        :autocomplete="autocomplete"
        :maxlength="maxlength"
        class="app-input__field"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @blur="$emit('blur')"
        @focus="$emit('focus')"
      >
    </div>
    <p
      v-if="error || hint"
      :id="`${inputId}-help`"
      class="app-input__help"
      :class="{ 'is-error': !!error }"
    >
      <span
        v-if="error"
        class="app-input__help-icon"
        aria-hidden="true"
      >!</span>
      {{ error || hint }}
    </p>
  </div>
</template>

<style scoped>
.app-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.app-input__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
  letter-spacing: 0.02em;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.app-input__required {
  color: var(--color-danger);
  margin-inline-start: 2px;
}

.app-input__wrap {
  position: relative;
  display: flex;
  align-items: stretch;
}

.app-input__prefix {
  position: absolute;
  left: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  display: inline-flex;
  align-items: center;
  pointer-events: none;
}

.app-input__field {
  width: 100%;
  height: 44px;
  padding: 0 var(--space-3);
  font-size: var(--font-size-md);
  font-family: inherit;
  color: var(--color-text-strong);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  box-shadow: var(--shadow-inner-deep);
  transition:
    border-color var(--duration-base) var(--easing-out),
    box-shadow var(--duration-base) var(--easing-out),
    background var(--duration-base) var(--easing-out);
}

.app-input.has-prefix .app-input__field {
  padding-left: 36px;
}

.app-input__field--area {
  min-height: 96px;
  height: auto;
  padding: 10px 12px;
  font-size: var(--font-size-sm);
  line-height: 1.65;
  resize: vertical;
  font-family: inherit;
}

.app-input__field::placeholder {
  color: var(--color-text-tertiary);
}

.app-input__field:hover:not(:disabled) {
  border-color: var(--color-border-strong);
}

.app-input__field:focus {
  border-color: var(--color-brand-500);
  background: var(--color-surface);
  box-shadow:
    var(--shadow-ring-focus),
    var(--shadow-inner-deep);
}

.app-input__field:disabled {
  background: var(--color-neutral-100);
  cursor: not-allowed;
  opacity: 0.7;
}

.app-input.has-error .app-input__field {
  border-color: var(--color-danger);
  background: rgb(198 40 40 / 4%);
}

.app-input.has-error .app-input__field:focus {
  box-shadow: 0 0 0 3px rgb(198 40 40 / 22%);
}

.app-input__help {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}

.app-input__help.is-error {
  color: var(--color-danger);
}

.app-input__help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-danger);
  color: #fff;
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  font-family: var(--font-family-serif);
}
</style>
