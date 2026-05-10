<script setup lang="ts">
import { computed } from "vue";

/**
 * 内置图标库（lucide.dev 启发的描边风格）。
 *
 * 为什么自建
 * ----------
 * - 反诈平台必须能在内网 / 受限环境运行；不能依赖 CDN 拉图标。
 * - 通过单组件 + 受控 path 集合，确保线宽 / 视图框一致。
 * - 添加新图标：在 ICONS 表中加一项，描边宽度 1.6 / viewBox 24。
 */

type IconName =
  | "shield-check"
  | "shield-alert"
  | "alert-triangle"
  | "lock"
  | "key"
  | "user"
  | "user-cog"
  | "users"
  | "file-text"
  | "list-checks"
  | "scale"
  | "gavel"
  | "siren"
  | "bell"
  | "activity"
  | "radar"
  | "search"
  | "log-in"
  | "log-out"
  | "arrow-right"
  | "chevron-right"
  | "circle-check"
  | "circle-x"
  | "info"
  | "sparkles"
  | "graduation-cap"
  | "book-open"
  | "clipboard-list"
  | "plus"
  | "filter"
  | "download"
  | "shield";

interface Props {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  ariaLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  size: 18,
  strokeWidth: 1.7,
});

const ICONS: Record<IconName, string> = {
  "shield-check":
    "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10ZM9 12l2 2 4-4",
  "shield-alert":
    "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z M12 8v4 M12 16h.01",
  "alert-triangle":
    "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z M12 9v4 M12 17h.01",
  lock: "M5 11h14v10H5z M8 11V7a4 4 0 0 1 8 0v4",
  key: "M21 2 9 14 M14 9l4 4 M9.5 14.5 5 19a2 2 0 1 0 2 2l4.5-4.5",
  user:
    "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  "user-cog":
    "M12 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M2 21v-2a4 4 0 0 1 4-4h6 M19.4 21.6a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M19.4 14v1.5 M19.4 21.5V23 M22.5 17.5l-1.3.7 M17.6 20.3l-1.3.7 M16.3 17.5l1.3.7 M21.2 20.3l1.3.7",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M12 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  "file-text":
    "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
  "list-checks":
    "M3 6h.01 M3 12h.01 M3 18h.01 M8 6h13 M8 12h7 M8 18h13 M16 11l2 2 4-4",
  scale:
    "M3 21h18 M12 3v18 M5 9h14 M5 9l-3 6a4 4 0 0 0 6 0Z M19 9l-3 6a4 4 0 0 0 6 0Z",
  gavel:
    "m13 13 6-6 M11 11l9 9 M2 22l9-9 M14 4l6 6 M3 18l3 3",
  siren:
    "M7 18v-6a5 5 0 0 1 10 0v6 M5 21h14 M3 18h18 M12 2v2 M5.6 5.6l1.4 1.4 M16.6 7l1.4-1.4",
  bell:
    "M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9 M10 21a2 2 0 0 0 4 0",
  activity:
    "M22 12h-4l-3 9-6-18-3 9H2",
  radar:
    "M19.07 4.93A10 10 0 0 0 5 18 M12 12 4.93 19.07 M12 7v5l3 3 M2 12a10 10 0 1 0 20 0 10 10 0 0 0-20 0",
  search:
    "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z M21 21l-4.3-4.3",
  "log-in":
    "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4 M10 17l5-5-5-5 M15 12H3",
  "log-out":
    "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9",
  "arrow-right": "M5 12h14 M12 5l7 7-7 7",
  "chevron-right": "m9 18 6-6-6-6",
  "circle-check":
    "M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4 12 14.01l-3-3",
  "circle-x":
    "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z M15 9l-6 6 M9 9l6 6",
  info: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z M12 16v-4 M12 8h.01",
  sparkles:
    "M12 3v18 M3 12h18 M5.6 5.6l12.8 12.8 M18.4 5.6 5.6 18.4",
  "graduation-cap":
    "M22 10v6 M2 10l10-5 10 5-10 5z M6 12v5c3 3 9 3 12 0v-5",
  "book-open":
    "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
  "clipboard-list":
    "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M9 2h6v4H9z M12 11h4 M12 16h4 M8 11h.01 M8 16h.01",
  plus: "M5 12h14 M12 5v14",
  filter: "M22 3H2l8 9.46V19l4 2v-8.54Z",
  download: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z",
};

const path = computed<string>(() => ICONS[props.name]);
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke-width="strokeWidth"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="ariaLabel ? 'img' : 'presentation'"
    :aria-label="ariaLabel"
    :aria-hidden="ariaLabel ? undefined : true"
    class="app-icon"
  >
    <path :d="path" />
  </svg>
</template>

<style scoped>
.app-icon {
  flex-shrink: 0;
  display: inline-block;
  vertical-align: -0.15em;
}
</style>
