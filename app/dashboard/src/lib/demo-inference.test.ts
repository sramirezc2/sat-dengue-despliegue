import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { parseFile, requestRanking } from "./demo-inference";

const csv = (rows: string[]) =>
  parseFile(
    new TextEncoder().encode(["municipality_code,INI_SIN,confirmados,COD_EVE", ...rows].join("\n"))
      .buffer,
    "ejemplo.csv",
    new Set(["50001", "73001"]),
  );

afterEach(() => vi.unstubAllGlobals());

describe("carga mensual T+2", () => {
  it("conserva ceros explícitos, excluye otros departamentos y rechaza datos inválidos", () => {
    const upload = csv([
      "50001,2025-10-01,0,210",
      "50001,02/10/2025,0,220",
      "73001,2025-10-03,1,210",
      "73999,2025-10-04,1,210",
      "11001,2025-10-01,1,210",
      "73001,2025-10-04,,210",
    ]);
    expect(upload).toMatchObject({
      period: "2025-10",
      zeros: 2,
      excluded: 1,
      rejected: 2,
      confirmed: 1,
    });
    expect(upload.rows).toEqual([
      { code: "50001", dengue: 0, grave: 0 },
      { code: "73001", dengue: 1, grave: null },
    ]);
  });

  it("rechaza cargas con meses mezclados", () => {
    expect(() => csv(["50001,2025-10-01,0,210", "73001,2025-11-01,1,210"])).toThrow(/un solo mes/);
  });

  it("acepta el Excel real incluido con 13 filas fuera de alcance", () => {
    const file = Uint8Array.from(readFileSync("../../datos/202510_ejemplo.xlsx"));
    const catalog = readFileSync("../../pipeline/conf/geografia/divipola_coordenadas.csv", "utf8");
    const codes = new Set(
      Array.from(catalog.matchAll(/^"(?:50|73)","[^"]+","([0-9]+)"/gm), (m) => m[1]!),
    );
    const upload = parseFile(file.buffer, "202510_ejemplo.xlsx", codes);
    expect(upload).toMatchObject({
      total: 231,
      confirmed: 218,
      rejected: 0,
      excluded: 13,
      period: "2025-10",
    });
    expect(upload.rows).toHaveLength(37);
    expect(upload.rows.every((row) => row.grave === null)).toBe(true);
  });

  it("envía únicamente agregados y maneja la indisponibilidad del servicio", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      requestRanking(csv(["50001,2025-10-01,0,210"]), false, new AbortController().signal),
    ).rejects.toThrow("Modelo T+2 no disponible.");
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("/api/inferencia/t2");
    expect(JSON.parse(init.body)).toEqual({
      period: "2025-10",
      rows: [{ code: "50001", dengue: 0, grave: null }],
      sample: false,
    });
  });
});
