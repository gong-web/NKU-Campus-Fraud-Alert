import http from "./http";
import type { WhoAmI } from "@/types/api";

export const authApi = {
  async loginUrl(service?: string): Promise<{ login_url: string; provider: string; healthy: boolean }> {
    const r = await http.get("/api/v1/auth/cas/login-url", { params: { service } });
    return r.data;
  },

  async mockLogin(casAccount: string): Promise<WhoAmI> {
    const r = await http.post("/api/v1/auth/cas/mock-login", { cas_account: casAccount });
    return r.data;
  },

  async whoami(): Promise<WhoAmI> {
    const r = await http.get("/api/v1/auth/me");
    return r.data;
  },

  async logout(): Promise<{ cas_logout_url: string }> {
    const r = await http.post("/api/v1/auth/logout");
    return r.data;
  },
};
