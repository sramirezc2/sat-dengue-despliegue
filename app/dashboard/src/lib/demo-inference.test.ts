import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { createHash, webcrypto } from "node:crypto";
import { resolve } from "node:path";
import { loadDefaultPackage, loadPackage, parseFile, rank } from "./demo-inference";

const sample = resolve("../../datos/202510_ejemplo.xlsx");
const model = resolve("../../pipeline/data/demo/package.json");
const predictor = "dengue_notifications_count";
const history = [
  ...Array.from({ length: 5 }, (_, i) =>
    ["10", "11", "12"].map((month) => `${2020 + i}-${month}`),
  ).flat(),
  "2025-07",
  "2025-08",
  "2025-09",
].map((year_month) => ({
  year_month,
  municipality_code: "73001",
  dengue_notifications_count: 1,
  dengue_grave_notifications_count: 0,
  total_notifications_count: 1,
}));
const payload = {
  schema: "sat-dengue.monthly-demo/v1",
  metadata: { kind: "synthetic", horizon: 2, supported_periods: ["2025-10"] },
  history,
  geography: [
    { municipality_code: "73001", municipality_name: "IBAGUÉ" },
    { municipality_code: "50001", municipality_name: "VILLAVICENCIO" },
  ],
  model: {
    schema: "sat-dengue.logistic-inference/v1",
    classes: [0, 1],
    coef: [[2]],
    intercept: [0],
    mean: [0],
    std: [2],
    spec: {
      family: "logistic_onset",
      version: "v1",
      config_json: JSON.stringify({
        predictors: [predictor],
        preparation: {
          zone_encoding: "fixed_onehot",
          zone_columns: ["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"].map((v) => `zona_canal_t__${v}`),
          matrix_columns: [predictor],
          log1p_columns: [predictor],
          scaling: "standard_train",
          imputation: "none",
          variables_g: false,
        },
      }),
    },
  },
};
function envelope(value: typeof payload) {
  const text = JSON.stringify(value);
  return `{"payload":${text},"sha256":"${createHash("sha256").update(text).digest("hex")}"}`;
}

afterEach(() => vi.unstubAllGlobals());

describe("demostración mensual", () => {
  it("acepta códigos de residencia y fechas colombianas", () => {
    const csv =
      "COD_DPTO_R,COD_MUN_R,INI_SIN,confirmados\n50,001,8/10/2025 12:00:00,1\n50,001,2025-02-30,1\n";
    const upload = parseFile(new TextEncoder().encode(csv).buffer);
    expect(upload.last).toBe("2025-10");
    expect(upload.confirmed).toBe(1);
    expect(upload.rejected).toBe(1);
    expect(upload.counts.get("50001:2025-10")).toBe(1);
  });
  it.skipIf(!existsSync(sample) || !existsSync(model))(
    "procesa el ejemplo local con el modelo local",
    async () => {
      vi.stubGlobal("crypto", webcrypto);
      const bytes = readFileSync(sample);
      const upload = parseFile(
        bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
      );
      const pkg = await loadPackage(readFileSync(model, "utf8"));
      const result = rank(pkg, upload);
      expect(upload.total).toBe(231);
      expect(upload.last).toBe("2025-10");
      expect(result.some((r) => r.probability !== null)).toBe(true);
      expect(
        result.every((r) => r.probability === null || (r.probability >= 0 && r.probability <= 1)),
      ).toBe(true);
    },
  );
  it("rechaza paquetes alterados o incompatibles aunque el hash corresponda", async () => {
    vi.stubGlobal("crypto", webcrypto);
    await expect(loadPackage(envelope(payload).replace("IBAGUÉ", "Ibagué"))).rejects.toThrow(
      /incompatible o está alterado/,
    );
    await expect(
      loadPackage(envelope({ ...payload, metadata: { ...payload.metadata, horizon: 1 } })),
    ).rejects.toThrow(/incompatible o está alterado/);
    await expect(
      loadPackage(envelope({ ...payload, model: { ...payload.model, std: [2, 3] } })),
    ).rejects.toThrow(/incompatible o está alterado/);
  });

  it("carga el paquete integrado, reintenta si falta y reutiliza el modelo verificado", async () => {
    vi.stubGlobal("crypto", webcrypto);
    const fetchModel = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 404 }))
      .mockResolvedValueOnce(new Response(envelope(payload)));
    vi.stubGlobal("fetch", fetchModel);
    await expect(loadDefaultPackage()).rejects.toThrow(/No se pudo cargar el modelo logístico/);
    const pending = loadDefaultPackage();
    expect(loadDefaultPackage()).toBe(pending);
    const pkg = await pending;
    expect(await loadDefaultPackage()).toBe(pkg);
    expect(fetchModel).toHaveBeenCalledTimes(2);
    expect(fetchModel.mock.calls[1]?.[0]).toBe("/demo/logistica-t2.json");
    const csv = "municipality_code,INI_SIN,confirmados\n73001,2025-10-02,1\n";
    const upload = parseFile(new TextEncoder().encode(csv).buffer);
    const result = rank(pkg, upload);
    expect(result[0]).toMatchObject({ code: "73001", probability: 2 / 3 });
    expect(result[1]).toMatchObject({ code: "50001", probability: null });
    expect(() => rank(pkg, { ...upload, last: "2025-09" })).toThrow(/2025-10/);
  });
});
