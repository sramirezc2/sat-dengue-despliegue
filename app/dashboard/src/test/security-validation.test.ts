import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { z as legacy } from "zod/v3";
import { dashboardResponseSchema, type DashboardResponse } from "@/lib/dashboard-contract";

function fixture(): DashboardResponse {
  return JSON.parse(
    readFileSync(resolve(import.meta.dirname, "fixtures/respuesta_tolima.json"), "utf8"),
  ) as DashboardResponse;
}

describe("security upgrade preserves the JSON contract", () => {
  it.each([
    "12345678-1234-0234-0234-123456789abc",
    "00000000-0000-0000-0000-000000000000",
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
    "A2345678-1234-4234-8234-123456789ABC",
    "invalid",
  ])("retains UUID acceptance for %s", (value) => {
    const input = fixture();
    input.metadata.result_set_id = value;
    expect(dashboardResponseSchema.safeParse(input).success).toBe(
      legacy.string().uuid().safeParse(value).success,
    );
  });

  it.each([
    "2026-11-08T12:34Z",
    "2026-11-08T12:34:56Z",
    "2026-11-08T12:34:56.123456Z",
    "2026-11-08T12:34:56+0500",
    "2026-11-08T12:34:56-05:00",
    "2026-11-08T12:34:56+9999",
    "2024-02-29T12:34:56Z",
    "2025-02-29T12:34:56Z",
    "2026-11-08T24:00:00Z",
    "2026-11-08T12:34:56",
  ])("retains timestamp acceptance for %s", (value) => {
    const input = fixture();
    input.metadata.generated_at = value;
    expect(dashboardResponseSchema.safeParse(input).success).toBe(
      legacy.string().datetime({ offset: true }).safeParse(value).success,
    );
  });

  it.each([0, 1, Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER + 1, -1, 0.5])(
    "retains nonnegative integer acceptance for %s",
    (value) => {
      const input = fixture();
      input.evaluation_context.evaluation_records[0]!.false_alerts = value;
      expect(dashboardResponseSchema.safeParse(input).success).toBe(
        legacy.number().int().nonnegative().safeParse(value).success,
      );
    },
  );

  it("rejects an oversized horizon array before reading any element", () => {
    const input = fixture();
    let reads = 0;
    const oversized = Array.from({ length: 3 }, () => ({
      get horizon() {
        reads += 1;
        return "T1";
      },
    }));
    Object.assign(input.municipalities[0]!, { results: oversized });
    expect(dashboardResponseSchema.safeParse(input).success).toBe(false);
    expect(reads).toBe(0);
  });
});
