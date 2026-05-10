<script setup lang="ts">
import { useRouter } from "vue-router";
import { AppButton } from "@/components";

const router = useRouter();
</script>

<template>
  <div class="not-found">
    <h1>404</h1>
    <p>找不到页面。</p>
    <AppButton
      variant="primary"
      @click="router.replace('/')"
    >
      返回首页
    </AppButton>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  background: var(--color-bg);
}

.not-found h1 {
  font-size: 96px;
  color: var(--color-brand-500);
  margin: 0;
}

.not-found p {
  color: var(--color-text-secondary);
}
</style>
