import * as XLSX from "xlsx";
import { z } from "zod";

type Row = Record<string, unknown>;
const countSchema = z.object({
  dengue_notifications_count: z.number().int().nonnegative(),
  dengue_grave_notifications_count: z.number().int().nonnegative(),
  total_notifications_count: z.number().int().nonnegative(),
});
type Count = z.infer<typeof countSchema>;
const municipalityCode = z.string().regex(/^(50|73)\d{3}$/);
const period = z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/);
const packageSchema = z.object({
  schema: z.literal("sat-dengue.monthly-demo/v1"),
  metadata: z.object({
    kind: z.literal("synthetic"),
    horizon: z.literal(2),
    supported_periods: z.array(period).min(1),
  }),
  history: z.array(countSchema.extend({ municipality_code: municipalityCode, year_month: period })),
  geography: z
    .array(z.object({ municipality_code: municipalityCode, municipality_name: z.string().min(1) }))
    .min(1),
  model: z.object({
    schema: z.literal("sat-dengue.logistic-inference/v1"),
    classes: z.tuple([z.literal(0), z.literal(1)]),
    coef: z.tuple([z.array(z.number()).min(1)]),
    intercept: z.tuple([z.number()]),
    mean: z.array(z.number()),
    std: z.array(z.number().positive()),
    spec: z.object({
      family: z.literal("logistic_onset"),
      version: z.literal("v1"),
      config_json: z.string(),
    }),
  }),
});
const configSchema = z.object({
  predictors: z.array(z.string()).min(1),
  preparation: z.object({
    zone_encoding: z.literal("fixed_onehot"),
    zone_columns: z.array(z.string()).length(4),
    matrix_columns: z.array(z.string()),
    log1p_columns: z.array(z.string()),
    scaling: z.literal("standard_train"),
    imputation: z.literal("none"),
    variables_g: z.literal(false),
  }),
});
type Package = z.infer<typeof packageSchema> & { config: z.infer<typeof configSchema> };
const MODEL_PATH = "/demo/logistica-t2.json";
const INVALID_MODEL = "El modelo logístico T+2 es incompatible o está alterado.";
let defaultPackage: Promise<Package> | undefined;
export type Upload = {
  total: number;
  rejected: number;
  confirmed: number;
  last: string;
  counts: Map<string, number>;
};
export type Result = {
  code: string;
  name: string;
  probability: number | null;
  cases: number | null;
  zone: string | null;
  p75t2: number | null;
};

export function parseFile(buffer: ArrayBuffer): Upload {
  const book = XLSX.read(new Uint8Array(buffer), { type: "array", cellDates: true, raw: true });
  const rows = XLSX.utils.sheet_to_json<Row>(book.Sheets[book.SheetNames[0]!]!, { defval: "" });
  if (!rows.length) throw Error("El archivo no contiene filas.");
  const headers = Object.keys(rows[0]!).map((s) => s.toLowerCase());
  if (
    !["ini_sin", "confirmados"].every((s) => headers.includes(s)) ||
    !(
      headers.includes("municipality_code") ||
      ["cod_dpto_r", "cod_mun_r"].every((s) => headers.includes(s))
    )
  )
    throw Error("Faltan INI_SIN, confirmados o códigos de residencia.");
  let rejected = 0,
    confirmed = 0,
    last = "";
  const counts = new Map<string, number>();
  for (const raw of rows) {
    const r = Object.fromEntries(Object.entries(raw).map(([k, v]) => [k.toLowerCase(), v]));
    const codePart = (v: unknown, n: number) =>
      /^\d+$/.test(String(v).trim()) ? String(v).trim().padStart(n, "0") : "";
    const code = r["municipality_code"]
      ? codePart(r["municipality_code"], 5)
      : codePart(r["cod_dpto_r"], 2) + codePart(r["cod_mun_r"], 3);
    const d = r["ini_sin"];
    let date =
      d instanceof Date && !Number.isNaN(d.getTime())
        ? d.toISOString().slice(0, 10)
        : (String(d).trim().split(" ")[0] ?? "");
    const match = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(date);
    if (match) date = `${match[3]}-${match[2]!.padStart(2, "0")}-${match[1]!.padStart(2, "0")}`;
    const parsed = /^\d{4}-\d{2}-\d{2}$/.test(date) ? new Date(`${date}T00:00:00Z`) : null;
    const value = String(r["confirmados"]).trim();
    if (
      !/^(50|73)\d{3}$/.test(code) ||
      !parsed ||
      Number.isNaN(parsed.getTime()) ||
      parsed.toISOString().slice(0, 10) !== date ||
      !["0", "1"].includes(value)
    ) {
      rejected++;
      continue;
    }
    const month = date.slice(0, 7);
    last = month > last ? month : last;
    const key = `${code}:${month}`;
    counts.set(key, (counts.get(key) ?? 0) + Number(value));
    if (value === "1") confirmed++;
  }
  return { total: rows.length, rejected, confirmed, last, counts };
}

export async function loadPackage(text: string): Promise<Package> {
  const start = '{"payload":';
  const end = text.lastIndexOf(',"sha256":');
  if (!text.startsWith(start) || end < 0) throw Error(INVALID_MODEL);
  if (!globalThis.crypto?.subtle)
    throw Error("Abre el tablero por HTTPS o localhost para verificar el modelo logístico T+2.");
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text.slice(start.length, end)),
  );
  const actual = Array.from(new Uint8Array(digest), (n) => n.toString(16).padStart(2, "0")).join(
    "",
  );
  try {
    const doc = JSON.parse(text);
    if (actual !== doc.sha256) throw Error(INVALID_MODEL);
    const pkg = packageSchema.parse(doc.payload);
    const config = configSchema.parse(JSON.parse(pkg.model.spec.config_json));
    const { predictors, preparation } = config;
    const columns = predictors.flatMap((name) =>
      name === "zona_canal_t" ? preparation.zone_columns : [name],
    );
    if (
      new Set(columns).size !== columns.length ||
      columns.length !== preparation.matrix_columns.length ||
      columns.some((name, i) => name !== preparation.matrix_columns[i]) ||
      [pkg.model.coef[0], pkg.model.mean, pkg.model.std].some((v) => v.length !== columns.length)
    )
      throw Error(INVALID_MODEL);
    return { ...pkg, config };
  } catch {
    throw Error(INVALID_MODEL);
  }
}

export function loadDefaultPackage(): Promise<Package> {
  defaultPackage ??= fetch(MODEL_PATH, { cache: "no-store", signal: AbortSignal.timeout(10_000) })
    .then(async (response) => {
      if (!response.ok) throw Error();
      return response.text();
    })
    .catch(() => {
      throw Error("No se pudo cargar el modelo logístico T+2. Vuelve a intentar el cálculo.");
    })
    .then(loadPackage)
    .catch((error: unknown) => {
      defaultPackage = undefined;
      throw error;
    });
  return defaultPackage;
}

function shift(month: string, n: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(Date.UTC(y!, m! - 1 + n, 1));
  return d.toISOString().slice(0, 7);
}
function quantile(values: number[], q: number): number {
  const a = [...values].sort((x, y) => x - y);
  const i = (a.length - 1) * q,
    k = Math.floor(i);
  return a[k]! + (i - k) * (a[Math.ceil(i)]! - a[k]!);
}
export function rank(pkg: Package, upload: Upload): Result[] {
  if (!upload.last) throw Error("El archivo no contiene filas válidas para calcular T+2.");
  const periods = pkg.metadata.supported_periods;
  if (!periods.includes(upload.last))
    throw Error(`El modelo logístico T+2 admite estos meses de referencia: ${periods.join(", ")}.`);
  const history = new Map<string, Count>(
    pkg.history.map((r) => [`${r.municipality_code}:${r.year_month}`, r]),
  );
  for (const [key, count] of upload.counts)
    history.set(key, {
      dengue_notifications_count: count,
      dengue_grave_notifications_count: 0,
      total_notifications_count: count,
    });
  const { model, config } = pkg;
  const prep = config.preparation;
  return pkg.geography
    .map(({ municipality_code: code, municipality_name: name }) => {
      try {
        const get = (m: string): Count => {
          const v = history.get(`${code}:${m}`);
          if (!v) throw Error("Historia insuficiente");
          return v;
        };
        const h5 = (period: string) =>
          Array.from(
            { length: 5 },
            (_, i) =>
              get(`${Number(period.slice(0, 4)) - 5 + i}${period.slice(4)}`)
                .dengue_notifications_count,
          );
        const current = get(upload.last),
          c = h5(upload.last),
          p25 = quantile(c, 0.25),
          p50 = quantile(c, 0.5),
          p75 = quantile(c, 0.75),
          n = current.dengue_notifications_count;
        const f: Record<string, number | string> = {
          ...current,
          p25_canal_t: p25,
          p50_canal_t: p50,
          p75_canal_t: p75,
          zona_canal_t: n < p25 ? "EXITO" : n <= p50 ? "SEGURIDAD" : n <= p75 ? "ALERTA" : "EXCESO",
          month_of_year: Number(upload.last.slice(5)),
        };
        for (const key of [
          "dengue_notifications_count",
          "dengue_grave_notifications_count",
          "total_notifications_count",
        ] as const)
          for (const lag of [1, 2, 3, 12])
            f[`${key}_lag${lag}`] = get(shift(upload.last, -lag))[key];
        for (const h of [1, 2]) {
          const values = h5(shift(upload.last, h));
          f[`p25_h5_t${h}`] = quantile(values, 0.25);
          f[`p75_h5_t${h}`] = quantile(values, 0.75);
        }
        const matrix: number[] = [];
        for (const key of config.predictors) {
          const value = f[key];
          if (key === "zona_canal_t")
            matrix.push(
              ...prep.zone_columns.map((col) => Number(col === `zona_canal_t__${value}`)),
            );
          else {
            if (typeof value !== "number" || !Number.isFinite(value))
              throw Error("Variable ausente");
            matrix.push(prep.log1p_columns.includes(key) ? Math.log1p(Math.max(0, value)) : value);
          }
        }
        const score = matrix.reduce(
          (sum, x, i) => sum + (model.coef[0][i]! * (x - model.mean[i]!)) / model.std[i]!,
          model.intercept[0],
        );
        if (!Number.isFinite(score)) throw Error("Resultado inválido");
        return {
          code,
          name,
          cases: n,
          zone: String(f["zona_canal_t"]),
          p75t2: Number(f["p75_h5_t2"]),
          probability:
            score >= 0 ? 1 / (1 + Math.exp(-score)) : Math.exp(score) / (1 + Math.exp(score)),
        };
      } catch {
        return {
          code,
          name,
          probability: null,
          cases: history.get(`${code}:${upload.last}`)?.dengue_notifications_count ?? null,
          zone: null,
          p75t2: null,
        };
      }
    })
    .sort((a, b) => (b.probability ?? -1) - (a.probability ?? -1) || a.code.localeCompare(b.code));
}
