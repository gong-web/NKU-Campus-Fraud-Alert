import http from "./http";

/** 院系字典项（来自 `GET /api/v1/departments`）。 */
export interface DepartmentOut {
  dept_id: number;
  dept_code: string;
  dept_name: string;
  parent_dept_id: number | null;
  dept_level: number;
  sort_order: number;
}

export const departmentsApi = {
  /** 全量院系字典，按 sort_order 升序，供下拉框使用。 */
  async list(): Promise<DepartmentOut[]> {
    const r = await http.get("/api/v1/departments");
    return r.data;
  },
};
