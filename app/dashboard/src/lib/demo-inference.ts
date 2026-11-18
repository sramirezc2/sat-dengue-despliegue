import * as XLSX from "xlsx";

type Row = Record<string, unknown>;
type Count = {
  dengue_notifications_count: number;
  dengue_grave_notifications_count: number;
  total_notifications_count: number;
};
type Package = {
  schema: string;
  metadata: { kind: string; horizon: number; supported_periods: string[] };
  history: (Count & { municipality_code: string; year_month: string })[];
  geography: { municipality_code: string; municipality_name: string }[];
  model: {
    schema: string;
    classes: number[];
    coef: number[][];
    intercept: number[];
    mean: number[];
    std: number[];
    spec: { config_json: string };
  };
};
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

export async function loadPackage(file: File): Promise<Package> {
  const text = await file.text();
  const doc = JSON.parse(text);
  const end = text.lastIndexOf(',"sha256":');
  if (!text.startsWith('{"payload":') || end < 0) throw Error("Formato de paquete inválido.");
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text.slice(11, end)),
  );
  const actual = Array.from(new Uint8Array(digest), (n) => n.toString(16).padStart(2, "0")).join(
    "",
  );
  if (
    actual !== doc.sha256 ||
    doc.payload?.schema !== "sat-dengue.monthly-demo/v1" ||
    doc.payload?.metadata?.kind !== "synthetic" ||
    doc.payload?.metadata?.horizon !== 2 ||
    doc.payload?.model?.schema !== "sat-dengue.logistic-inference/v1" ||
    JSON.stringify(doc.payload.model.classes) !== "[0,1]"
  )
    throw Error("Paquete sintético inválido o alterado.");
  return doc.payload as Package;
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
  if (!upload.last || !pkg.metadata.supported_periods.includes(upload.last))
    throw Error("El mes de referencia no está soportado por el paquete sintético.");
  const history = new Map<string, Count>(
    pkg.history.map((r) => [`${r.municipality_code}:${r.year_month}`, r]),
  );
  for (const [key, count] of upload.counts)
    history.set(key, {
      dengue_notifications_count: count,
      dengue_grave_notifications_count: 0,
      total_notifications_count: count,
    });
  const model = pkg.model,
    conf = JSON.parse(model.spec.config_json),
    prep = conf.preparation;
  if (
    !Array.isArray(model.coef[0]) ||
    !Number.isFinite(model.intercept[0]) ||
    model.coef[0].some((v) => !Number.isFinite(v)) ||
    model.mean.some((v) => !Number.isFinite(v)) ||
    model.std.some((v) => !Number.isFinite(v) || v <= 0)
  )
    throw Error("Modelo incompatible");
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
        for (const key of conf.predictors as string[]) {
          const value = f[key];
          if (key === "zona_canal_t")
            matrix.push(
              ...(prep.zone_columns as string[]).map((col) =>
                Number(col === `zona_canal_t__${value}`),
              ),
            );
          else {
            if (typeof value !== "number" || !Number.isFinite(value))
              throw Error("Variable ausente");
            matrix.push(prep.log1p_columns.includes(key) ? Math.log1p(Math.max(0, value)) : value);
          }
        }
        if (
          matrix.length !== model.mean.length ||
          matrix.length !== model.std.length ||
          matrix.length !== model.coef[0]!.length ||
          model.std.some((v) => !Number.isFinite(v) || v <= 0)
        )
          throw Error("Modelo incompatible");
        const score = matrix.reduce(
          (sum, x, i) => sum + (model.coef[0]![i]! * (x - model.mean[i]!)) / model.std[i]!,
          model.intercept[0]!,
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
