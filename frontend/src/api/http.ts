/**
 * 全局 axios 实例。
 *
 * 约定
 * ----
 * - 自动带 `X-Requested-With` header（CSRF 防护，与后端中间件配合）。
 * - 自动带 cookie（登录态）。
 * - 401 自动跳登录；5xx 弹友好错误并打点上报。
 * - 响应统一脱出 `{ code, message, data }` 结构；只把 `data` 给业务层，
 *   出错统一抛 `ApiError` 让上层 `try/catch`。
 */

import axios from "axios";
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig , AxiosError } from "axios";
import { ElMessage } from "element-plus";

/** 后端统一响应体。 */
interface StandardResponse<T = unknown> {
  code: number;
  message: string;
  data: T | null;
  trace_id?: string;
}

export class ApiError extends Error {
  public readonly code: number;
  public readonly httpStatus?: number | undefined;
  public readonly traceId?: string | undefined;

  constructor(message: string, code: number, httpStatus?: number, traceId?: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.httpStatus = httpStatus;
    this.traceId = traceId;
  }
}

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
  withCredentials: true,
  headers: {
    "X-Requested-With": "XMLHttpRequest",
  },
});

http.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  cfg.headers.set("X-Requested-With", "XMLHttpRequest");
  return cfg;
});

http.interceptors.response.use(
  (resp: AxiosResponse<StandardResponse>) => {
    const body = resp.data;
    if (body && typeof body === "object" && "code" in body) {
      if (body.code === 0) {
        return { ...resp, data: body.data } as unknown as AxiosResponse;
      }
      throw new ApiError(body.message || "失败", body.code, resp.status, body.trace_id);
    }
    return resp;
  },
  (err: AxiosError<StandardResponse>) => {
    const status = err.response?.status;
    const body = err.response?.data;
    const traceId = body?.trace_id;
    const code = body?.code ?? 0;
    const message = body?.message || err.message || "网络错误";

    if (status === 401) {
      // 跳登录页（避免 Vue Router 在拦截器里直接 import → 循环依赖）
      window.dispatchEvent(new CustomEvent("auth:unauthenticated"));
    } else if (status && status >= 500) {
      ElMessage.error({
        message: `服务器错误 (${code || status})${traceId ? "·" + traceId.slice(0, 8) : ""}`,
        duration: 0,
        showClose: true,
      });
    }

    throw new ApiError(message, code, status, traceId);
  },
);

export default http;
