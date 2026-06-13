import http from "./http";
import type { PaginationOut } from "@/types/api";
import { downloadBlob } from "@/utils/download";
import type {
  AssignedQuizCreateBody,
  QuestionAdmin,
  QuestionCreateBody,
  QuestionListParams,
  QuestionUpdateBody,
  QuizCancelBody,
  QuizCompletionReport,
  QuizDetail,
  QuizHistoryItem,
  QuizListItem,
  StartQuizOut,
  SubmitQuizBody,
  SubmitQuizOut,
  WrongQuestion,
} from "@/types/quiz";

export const quizApi = {
  // ── 学生侧 ─────────────────────────────────────────────────
  async startRandom(): Promise<StartQuizOut> {
    const r = await http.post("/api/v1/quiz/random/start");
    return r.data;
  },
  async listAssigned(status?: string): Promise<QuizListItem[]> {
    const r = await http.get("/api/v1/quiz/assigned", { params: status ? { status } : {} });
    return r.data;
  },
  async startAssigned(quizId: string): Promise<StartQuizOut> {
    const r = await http.post(`/api/v1/quiz/assigned/${quizId}/start`);
    return r.data;
  },
  async submit(attemptId: string, body: SubmitQuizBody): Promise<SubmitQuizOut> {
    const r = await http.post(`/api/v1/quiz/attempts/${attemptId}/submit`, body);
    return r.data;
  },
  async listWrong(limit = 100): Promise<WrongQuestion[]> {
    const r = await http.get("/api/v1/quiz/wrong-questions", { params: { limit } });
    return r.data;
  },
  async listHistory(params?: { page?: number; size?: number }): Promise<PaginationOut<QuizHistoryItem>> {
    const r = await http.get("/api/v1/quiz/history", { params });
    return r.data;
  },

  // ── 管理员：题库 ─────────────────────────────────────────────
  async createQuestion(body: QuestionCreateBody): Promise<QuestionAdmin> {
    const r = await http.post("/api/v1/admin/quiz/questions", body);
    return r.data;
  },
  async listQuestions(params?: QuestionListParams): Promise<PaginationOut<QuestionAdmin>> {
    const r = await http.get("/api/v1/admin/quiz/questions", { params });
    return r.data;
  },
  async getQuestion(qid: string): Promise<QuestionAdmin> {
    const r = await http.get(`/api/v1/admin/quiz/questions/${qid}`);
    return r.data;
  },
  async updateQuestion(qid: string, body: QuestionUpdateBody): Promise<QuestionAdmin> {
    const r = await http.patch(`/api/v1/admin/quiz/questions/${qid}`, body);
    return r.data;
  },
  async deleteQuestion(qid: string): Promise<{ status: string }> {
    const r = await http.delete(`/api/v1/admin/quiz/questions/${qid}`);
    return r.data;
  },

  // ── 管理员：指定测验 ─────────────────────────────────────────
  async createAssigned(body: AssignedQuizCreateBody): Promise<QuizDetail> {
    const r = await http.post("/api/v1/admin/quiz/quizzes", body);
    return r.data;
  },
  async listAdminQuizzes(params?: {
    status?: string;
    keyword?: string;
    page?: number;
    size?: number;
  }): Promise<PaginationOut<QuizListItem>> {
    const r = await http.get("/api/v1/admin/quiz/quizzes", { params });
    return r.data;
  },
  async getAdminQuiz(quizId: string): Promise<QuizDetail> {
    const r = await http.get(`/api/v1/admin/quiz/quizzes/${quizId}`);
    return r.data;
  },
  async cancel(quizId: string, body: QuizCancelBody): Promise<{ status: string }> {
    const r = await http.post(`/api/v1/admin/quiz/quizzes/${quizId}/cancel`, body);
    return r.data;
  },
  async report(quizId: string): Promise<QuizCompletionReport> {
    const r = await http.get(`/api/v1/admin/quiz/quizzes/${quizId}/report`);
    return r.data;
  },
  /** 触发浏览器下载报告 XLSX。 */
  reportExportUrl(quizId: string): string {
    return `/api/v1/admin/quiz/quizzes/${quizId}/report/export`;
  },
  async downloadReport(quizId: string): Promise<void> {
    const r = await http.get(this.reportExportUrl(quizId), { responseType: "blob" });
    downloadBlob(
      r.data as unknown as Blob,
      r.headers?.["content-disposition"] as string | undefined,
      `quiz_report_${quizId}.xlsx`,
    );
  },
};

export const QUIZ_STATUS_LABEL: Record<string, string> = {
  ACTIVE: "进行中",
  CANCELLED: "已撤回",
  FINISHED: "已结束",
};

export const QUIZ_STATUS_TONE: Record<string, "info" | "warning" | "danger" | "success"> = {
  ACTIVE: "success",
  CANCELLED: "info",
  FINISHED: "warning",
};

export const DIFFICULTY_LABEL: Record<number, string> = {
  1: "简单",
  2: "中等",
  3: "困难",
};

export const SCOPE_LABEL: Record<string, string> = {
  ALL: "全校",
  DEPT: "按院系",
  USERS: "按学生",
};
