<script setup lang="ts">
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

onMounted(async () => {
  // 启动时尝试拿"我"——刷新页面后保留登录态。
  await auth.fetchMe();
});
</script>

<template>
  <RouterView />
</template>
