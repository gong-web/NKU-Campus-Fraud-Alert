import { describe, expect, it } from "vitest";
import { filenameFromContentDisposition } from "./download";

describe("filenameFromContentDisposition", () => {
  it("decodes RFC 5987 UTF-8 filenames", () => {
    expect(
      filenameFromContentDisposition(
        "attachment; filename=\"report.xlsx\"; filename*=UTF-8''%E5%8F%8D%E8%AF%88.xlsx",
        "fallback.xlsx",
      ),
    ).toBe("反诈.xlsx");
  });

  it("uses a plain filename when no encoded filename exists", () => {
    expect(
      filenameFromContentDisposition(
        'attachment; filename="audit_logs.csv"',
        "fallback.csv",
      ),
    ).toBe("audit_logs.csv");
  });

  it("falls back when the encoded filename is invalid", () => {
    expect(
      filenameFromContentDisposition(
        "attachment; filename*=UTF-8''%E0%A4%A",
        "fallback.csv",
      ),
    ).toBe("fallback.csv");
  });
});
