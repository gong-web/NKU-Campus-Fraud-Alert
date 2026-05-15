import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import type { WhoAmI } from "@/types/api";

declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    roles?: Array<WhoAmI["role_code"]>;
    title?: string;
  }
}

const routes: RouteRecordRaw[] = [
  // ── 公共 ─────────────────────────────────────────────────
  {
    path: "/login",
    name: "login",
    component: () => import("@/pages/auth/LoginPage.vue"),
    meta: { title: "登录" },
  },
  // ── 学生端 ───────────────────────────────────────────────
  {
    path: "/student",
    component: () => import("@/layouts/StudentLayout.vue"),
    meta: { requiresAuth: true, roles: ["STUDENT"] },
    children: [
      {
        path: "",
        redirect: "/student/home",
      },
      {
        path: "home",
        name: "student-home",
        component: () => import("@/pages/student/HomePage.vue"),
        meta: { title: "学生首页" },
      },
      // UC-01：上报
      {
        path: "report",
        name: "report-form",
        component: () => import("@/pages/student/ReportFormPage.vue"),
        meta: { title: "我要上报" },
      },
      {
        path: "report/success",
        name: "report-success",
        component: () => import("@/pages/student/ReportSuccessPage.vue"),
        meta: { title: "上报成功" },
      },
      // UC-02：个人中心 + 我的上报
      {
        path: "profile",
        name: "student-profile",
        component: () => import("@/pages/student/ProfilePage.vue"),
        meta: { title: "个人中心" },
      },
      {
        path: "reports",
        name: "my-reports",
        component: () => import("@/pages/student/MyReportsPage.vue"),
        meta: { title: "我的上报" },
      },
      {
        path: "reports/:case_id",
        name: "report-detail",
        component: () => import("@/pages/student/ReportDetailPage.vue"),
        meta: { title: "案件详情" },
      },
      {
        path: "drafts",
        name: "drafts",
        component: () => import("@/pages/student/DraftsPage.vue"),
        meta: { title: "草稿箱" },
      },
    ],
  },
  // ── 审核管理员 ───────────────────────────────────────────
  {
    path: "/admin",
    component: () => import("@/layouts/AdminLayout.vue"),
    meta: { requiresAuth: true, roles: ["REVIEWER", "SYS_ADMIN"] },
    children: [
      {
        path: "",
        redirect: "/admin/dashboard",
      },
      {
        path: "dashboard",
        name: "admin-dashboard",
        component: () => import("@/pages/admin/DashboardPage.vue"),
        meta: { title: "审核工作台" },
      },
    ],
  },
  // ── 系统管理员 ───────────────────────────────────────────
  {
    path: "/sys",
    component: () => import("@/layouts/SysAdminLayout.vue"),
    meta: { requiresAuth: true, roles: ["SYS_ADMIN"] },
    children: [
      {
        path: "",
        redirect: "/sys/dashboard",
      },
      {
        path: "dashboard",
        name: "sys-dashboard",
        component: () => import("@/pages/sys/DashboardPage.vue"),
        meta: { title: "系统管理首页" },
      },
      {
        path: "users",
        name: "sys-users",
        component: () => import("@/pages/sys/UsersPage.vue"),
        meta: { title: "账号管理" },
      },
      {
        path: "audit",
        name: "sys-audit",
        component: () => import("@/pages/sys/AuditLogsPage.vue"),
        meta: { title: "审计日志" },
      },
      {
        path: "judicial-assist",
        name: "sys-judicial",
        component: () => import("@/pages/sys/JudicialAssistPage.vue"),
        meta: { title: "司法协助查询" },
      },
    ],
  },
  // ── Mock 登录页（仅 mock 模式下用，不需要会话）───────────
  {
    path: "/auth/mock-login",
    name: "mock-login",
    component: () => import("@/pages/auth/MockLoginPage.vue"),
    meta: { title: "Mock 登录（开发用）" },
  },
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/pages/error/NotFoundPage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  if (to.meta.title) {
    document.title = `${String(to.meta.title)} · 校园电信诈骗上报与预警平台`;
  }
  const auth = useAuthStore();

  if (to.meta.requiresAuth) {
    if (!auth.isLoggedIn) {
      await auth.fetchMe();
    }
    if (!auth.isLoggedIn) {
      return { name: "login", query: { redirect: to.fullPath } };
    }
    if (to.meta.roles && !to.meta.roles.includes(auth.role!)) {
      return { name: "login", query: { reason: "forbidden" } };
    }
  }

  // 已登录访问登录页 → 跳到对应工作台
  if (to.name === "login" && auth.isLoggedIn) {
    return roleHome(auth.role);
  }
  return true;
});

export function roleHome(role: WhoAmI["role_code"] | null): string {
  if (role === "STUDENT") return "/student/home";
  if (role === "REVIEWER") return "/admin/dashboard";
  if (role === "SYS_ADMIN") return "/sys/dashboard";
  return "/login";
}

// 全局 401 监听 → 清状态 + 仅在受保护路由下跳登录页
// （在 /login 与 /auth/mock-login 等公开路由上, 401 是预期行为, 不能再跳）
const PUBLIC_ROUTE_NAMES = new Set(["login", "mock-login", "not-found"]);
window.addEventListener("auth:unauthenticated", () => {
  const auth = useAuthStore();
  auth.clearLocal();
  const current = router.currentRoute.value;
  if (current.meta.requiresAuth && !PUBLIC_ROUTE_NAMES.has(String(current.name ?? ""))) {
    void router.replace({ name: "login", query: { redirect: current.fullPath } });
  }
});

export default router;
