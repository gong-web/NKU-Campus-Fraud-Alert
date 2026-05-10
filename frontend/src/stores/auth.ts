import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { authApi } from "@/api/auth";
import type { WhoAmI } from "@/types/api";

export const useAuthStore = defineStore("auth", () => {
  const me = ref<WhoAmI | null>(null);
  const loading = ref<boolean>(false);
  const lastFetchedAt = ref<number>(0);

  const isLoggedIn = computed<boolean>(() => me.value !== null);
  const role = computed<WhoAmI["role_code"] | null>(() => me.value?.role_code ?? null);
  const permissions = computed<Set<string>>(() => new Set(me.value?.permissions ?? []));

  function hasRole(...roles: WhoAmI["role_code"][]): boolean {
    return role.value !== null && roles.includes(role.value);
  }

  function hasPermission(code: string): boolean {
    return permissions.value.has(code);
  }

  async function fetchMe(force = false): Promise<WhoAmI | null> {
    if (!force && me.value && Date.now() - lastFetchedAt.value < 30_000) {
      return me.value;
    }
    loading.value = true;
    try {
      me.value = await authApi.whoami();
      lastFetchedAt.value = Date.now();
      return me.value;
    } catch {
      me.value = null;
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function mockLogin(casAccount: string): Promise<WhoAmI> {
    me.value = await authApi.mockLogin(casAccount);
    lastFetchedAt.value = Date.now();
    return me.value;
  }

  async function logout(): Promise<string | null> {
    try {
      const { cas_logout_url } = await authApi.logout();
      me.value = null;
      return cas_logout_url;
    } catch {
      me.value = null;
      return null;
    }
  }

  function clearLocal(): void {
    me.value = null;
    lastFetchedAt.value = 0;
  }

  return {
    me,
    loading,
    isLoggedIn,
    role,
    permissions,
    hasRole,
    hasPermission,
    fetchMe,
    mockLogin,
    logout,
    clearLocal,
  };
});
