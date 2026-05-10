# Anti-Fraud Frontend

> Vue 3 + TypeScript SPA。学生 / 审核员 / 系统管理员三套布局共享一套设计系统。

## 目录

```
src/
  api/         # axios 实例 + 各模块 API 封装
  assets/      # 静态资源
  components/  # 共享 App* 组件（设计系统）
  composables/ # 组合式函数
  layouts/     # AdminLayout / StudentLayout / SysAdminLayout / AuthLayout
  pages/       # 页面级组件
  router/      # 路由 + 守卫
  stores/      # Pinia store
  styles/      # tokens.css + global.css
  types/       # 共享 TS 类型
  utils/       # 工具函数
```

## 设计系统铁律

页面**只能**用 `@/components` 下的 `App*`，不直接用 Element Plus 原生组件。详见 `docs/conventions.md`。

## 本地开发

```bash
npm install
npm run dev
```

`vite.config.ts` 已把 `/api/*` 代理到 `VITE_API_BASE_URL`（默认 `http://localhost:8000`）。
