import http from "./http";
import type {
  JudicialDecryptOut,
  JudicialDecryptRequestIn,
  JudicialDecryptRequestOut,
} from "@/types/api";

export const judicialApi = {
  async requestDecryption(body: JudicialDecryptRequestIn): Promise<JudicialDecryptRequestOut> {
    const r = await http.post("/api/v1/judicial-assist/request-decryption", body);
    return r.data;
  },

  async reveal(decryptLogId: string): Promise<JudicialDecryptOut> {
    const r = await http.get(`/api/v1/judicial-assist/${decryptLogId}/reveal`);
    return r.data;
  },
};
