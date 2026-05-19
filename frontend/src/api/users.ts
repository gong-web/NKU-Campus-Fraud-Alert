import http from "./http";
import type { PaginationOut, UserCreateIn, UserOut, UserUpdateIn } from "@/types/api";

export const usersApi = {
  async list(params: {
    role_id?: number;
    department_id?: number;
    status?: number;
    keyword?: string;
    page?: number;
    size?: number;
  } = {}): Promise<PaginationOut<UserOut>> {
    const r = await http.get("/api/v1/users", { params });
    return r.data;
  },

  async get(userId: string): Promise<UserOut> {
    const r = await http.get(`/api/v1/users/${userId}`);
    return r.data;
  },

  async create(body: UserCreateIn, idempotencyKey?: string): Promise<UserOut> {
    const config = idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : {};
    const r = await http.post("/api/v1/users", body, config);
    return r.data;
  },

  async patch(userId: string, body: UserUpdateIn): Promise<{ ok: boolean }> {
    const r = await http.patch(`/api/v1/users/${userId}`, body);
    return r.data;
  },

  async importCsv(csvText: string, dryRun = false): Promise<{ ok: boolean; imported?: number }> {
    const r = await http.post("/api/v1/users/import", {
      csv_text: csvText,
      dry_run: dryRun,
    });
    return r.data;
  },
};
