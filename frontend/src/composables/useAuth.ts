/**
 * 鉴权相关的组合式函数。
 *
 * 用法：
 *
 * ```ts
 * const { logout, hasPermission } = useAuth();
 * ```
 */
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";

export function useAuth() {
  const auth = useAuthStore();
  const router = useRouter();

  async function logoutAndRedirect(): Promise<void> {
    const url = await auth.logout();
    if (url) window.location.href = url;
    else void router.replace({ name: "login" });
  }

  return {
    me: auth.me,
    role: auth.role,
    hasRole: auth.hasRole,
    hasPermission: auth.hasPermission,
    logout: logoutAndRedirect,
  };
}
