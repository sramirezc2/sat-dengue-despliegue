import * as XLSX from "xlsx";
import { z } from "zod";

import { getDashboardConfig } from "./dashboard-config";

export const MAX_BYTES = 5 * 1024 * 1024;
const MAX_ROWS = 100_000;
const ENDPOINT = "/api/inferencia/t2";
export const MODEL_UNAVAILABLE = "Modelo T+2 no disponible.";
const period = z.string().regex(/^[0-9]{4}-(0[1-9]|1[0-2])$/);
const code = z.string().regex(/^(50|73)[0-9]{3}$/);
const retrospective = z.literal("retrospective");

const statusSchema = z.object({
  municipalities: z.array(code).length(76),
  model: z
    .object({
      experiment_id: z.string().min(1),
      version: z.string().min(1),
      periods: z.array(period).min(1),
      history_mode: retrospective,
    })
    .nullable(),
});
const resultSchema = z.object({
  code,
  name: z.string().min(1),
  cases: z.number().int().nonnegative().nullable(),
  zone: z.enum(["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"]).nullable(),
  p75t2: z.number().nonnegative().nullable(),
  probability: z.number().min(0).max(1).nullable(),
  reason: z
    .enum([
      "missing_upload",
      "missing_dengue",
      "missing_grave",
      "missing_climate",
      "missing_history",
      "excess_at_origin",
    ])
    .nullable(),
});
const rankingSchema = z.object({
  experiment_id: z.string().min(1),
  model_version: z.string().min(1),
  history_mode: retrospective,
  reference_period: period,
  target_period: period,
  sample: z.boolean(),
  rows: z.array(resultSchema).length(76),
});

type Count = { code: string; dengue: number | null; grave: number | null };
export type Upload = {
  total: number;
  rejected: number;
  excluded: number;
  confirmed: number;
  zeros: number;
  period: string;
  reasons: Record<string, number>;
  rows: Count[];
};
export type Ranking = z.infer<typeof rankingSchema>;
export type InferenceStatus = z.infer<typeof statusSchema>;

export async function getInferenceStatus(): Promise<InferenceStatus> {
  const { apiBaseUrl } = getDashboardConfig();
  const response = await fetch(`${apiBaseUrl}${ENDPOINT}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw Error(MODEL_UNAVAILABLE);
  return statusSchema.parse(await response.json());
}

export async function requestRanking(
  upload: Upload,
  sample: boolean,
  signal: AbortSignal,
): Promise<Ranking> {
  const { apiBaseUrl } = getDashboardConfig();
  const response = await fetch(`${apiBaseUrl}${ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ period: upload.period, rows: upload.rows, sample }),
    signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]),
    cache: "no-store",
  }).catch(() => {
    throw Error(MODEL_UNAVAILABLE);
  });
  if (!response.ok) {
    if (response.status === 422) {
      const error = z
        .object({ message: z.string() })
        .safeParse(await response.json().catch(() => null));
      if (error.success) throw Error(error.data.message);
    }
    throw Error(MODEL_UNAVAILABLE);
  }
  const result = rankingSchema.safeParse(await response.json().catch(() => null));
  if (
    !result.success ||
    result.data.reference_period !== upload.period ||
    result.data.sample !== sample
  ) {
    throw Error("La respuesta de inferencia no corresponde a la carga.");
  }
  return result.data;
}

const text = (value: unknown) => String(value ?? "").trim();

function codePart(value: unknown, length: number) {
  const digits = text(value);
  return /^[0-9]+$/.test(digits) && digits.length <= length ? digits.padStart(length, "0") : "";
}

function month(value: unknown): string {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? "" : value.toISOString().slice(0, 7);
  }
  const raw = text(value);
  const iso = /^(\d{4})-(\d{2})-(\d{2})(?:[ T].+)?$/.exec(raw);
  const local = /^(\d{1,2})\/(\d{1,2})\/(\d{4})(?: .+)?$/.exec(raw);
  const parts = iso ? [iso[1], iso[2], iso[3]] : local ? [local[3], local[2], local[1]] : [];
  const [year, monthNumber, day] = parts.map(Number);
  if (!year || !monthNumber || !day || year < 1900) return "";
  const date = new Date(Date.UTC(year, monthNumber - 1, day));
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== monthNumber - 1 ||
    date.getUTCDate() !== day
  ) {
    return "";
  }
  return date.toISOString().slice(0, 7);
}

function event(value: string): "dengue" | "grave" | null {
  switch (value.toUpperCase()) {
    case "210":
    case "DENGUE":
      return "dengue";
    case "220":
    case "DENGUE GRAVE":
      return "grave";
    default:
      return null;
  }
}

function checkWorkbookSize(buffer: ArrayBuffer) {
  const zip = new DataView(buffer);
  for (let end = zip.byteLength - 22; end >= Math.max(0, zip.byteLength - 65557); end--) {
    if (
      zip.getUint32(end, true) !== 0x06054b50 ||
      end + 22 + zip.getUint16(end + 20, true) !== zip.byteLength
    )
      continue;
    const entries = zip.getUint16(end + 10, true);
    let offset = zip.getUint32(end + 16, true);
    let expanded = 0;
    if (entries > 512 || offset + zip.getUint32(end + 12, true) !== end) break;
    for (let i = 0; i < entries; i++) {
      if (offset + 46 > end || zip.getUint32(offset, true) !== 0x02014b50) {
        throw Error("El archivo no es un Excel (.xlsx) válido.");
      }
      expanded += zip.getUint32(offset + 24, true);
      if (expanded > 32 * 1024 * 1024) throw Error("El contenido expandido de Excel supera 32 MB.");
      offset +=
        46 +
        zip.getUint16(offset + 28, true) +
        zip.getUint16(offset + 30, true) +
        zip.getUint16(offset + 32, true);
    }
    if (offset === end && entries) return;
    break;
  }
  throw Error("El archivo no es un Excel (.xlsx) válido.");
}

function readRows(buffer: ArrayBuffer, filename: string): unknown[][] {
  const csv = /\.csv$/i.test(filename);
  if (!csv && !/\.xlsx$/i.test(filename)) throw Error("Selecciona un CSV o un Excel (.xlsx).");
  if (!buffer.byteLength || buffer.byteLength > MAX_BYTES) {
    throw Error("El archivo debe contener datos y pesar como máximo 5 MB.");
  }
  if (!csv) checkWorkbookSize(buffer);
  let workbook: XLSX.WorkBook;
  try {
    const bytes = new Uint8Array(buffer);
    const input = csv ? new TextDecoder("utf-8", { fatal: true }).decode(bytes) : bytes;
    workbook = XLSX.read(input, {
      type: csv ? "string" : "array",
      cellDates: true,
      cellFormula: false,
      raw: true,
      sheetRows: MAX_ROWS + 2,
    });
  } catch {
    throw Error("No se pudo leer el archivo. Usa CSV UTF-8 o Excel (.xlsx).");
  }
  const sheets = workbook.SheetNames.map((name) => workbook.Sheets[name]).filter(
    (sheet) => sheet?.["!ref"],
  );
  if (sheets.length !== 1) throw Error("El archivo debe contener una sola hoja con datos.");
  const sheet = sheets[0]!;
  const range = XLSX.utils.decode_range(sheet["!fullref"] || sheet["!ref"]!);
  if (range.e.r - range.s.r > MAX_ROWS || range.e.c - range.s.c >= 256) {
    throw Error("El archivo admite hasta 100 000 filas y 256 columnas.");
  }
  return XLSX.utils.sheet_to_json<unknown[]>(sheet, { header: 1, defval: "", blankrows: false });
}

export function parseFile(
  buffer: ArrayBuffer,
  filename: string,
  municipalities?: ReadonlySet<string>,
): Upload {
  const [header, ...rows] = readRows(buffer, filename);
  if (!header || !rows.length) throw Error("El archivo no contiene filas.");
  const columns = header.map((cell) => text(cell).toLowerCase());
  const named = columns.filter(Boolean);
  if (new Set(named).size !== named.length)
    throw Error("El archivo contiene encabezados repetidos.");
  const pos = (name: string) => columns.indexOf(name);
  if (
    pos("ini_sin") < 0 ||
    pos("confirmados") < 0 ||
    (pos("municipality_code") < 0 && (pos("cod_dpto_r") < 0 || pos("cod_mun_r") < 0))
  )
    throw Error("Faltan INI_SIN, confirmados o los códigos de residencia.");
  const [dateCol, valueCol, codeCol, depCol, muniCol, eventCol, labelCol] = [
    "ini_sin",
    "confirmados",
    "municipality_code",
    "cod_dpto_r",
    "cod_mun_r",
    "cod_eve",
    "nombre_evento",
  ].map(pos) as [number, number, number, number, number, number, number];

  const periods = new Set<string>();
  const counts = new Map<string, Count>();
  const reasons: Record<string, number> = {};
  let confirmed = 0,
    rejected = 0,
    excluded = 0,
    zeros = 0;
  function reject(reason: string) {
    rejected++;
    reasons[reason] = (reasons[reason] ?? 0) + 1;
  }
  for (const row of rows) {
    const full = codePart(row[codeCol], 5);
    const department = codePart(row[depCol], 2);
    const muni = codePart(row[muniCol], 3);
    const split = department && muni ? department + muni : "";
    const municipality = full || split;
    if (!municipality || (text(row[codeCol]) && !full) || (full && split && full !== split)) {
      reject("Código DIVIPOLA inválido");
      continue;
    }
    if (!/^(50|73)/.test(municipality)) {
      excluded++;
      continue;
    }
    if (municipalities && !municipalities.has(municipality)) {
      reject("Código DIVIPOLA inválido");
      continue;
    }
    const t = month(row[dateCol]);
    const value = text(row[valueCol]);
    const rawEvent = text(row[eventCol]);
    const rawLabel = text(row[labelCol]);
    const fromCode = event(rawEvent);
    const fromLabel = event(rawLabel);
    const kind = rawEvent || rawLabel ? (fromCode ?? fromLabel) : "dengue";
    if (!t) {
      reject("Fecha INI_SIN inválida");
    } else if (value !== "0" && value !== "1") {
      reject("Confirmados debe ser 0 o 1");
    } else if (
      !kind ||
      (rawEvent && !fromCode) ||
      (rawLabel && !fromLabel) ||
      (fromCode && fromLabel && fromCode !== fromLabel)
    ) {
      reject("Evento inválido o contradictorio");
    } else {
      const count = counts.get(municipality) ?? { code: municipality, dengue: null, grave: null };
      count[kind] = (count[kind] ?? 0) + Number(value);
      counts.set(municipality, count);
      periods.add(t);
      if (value === "0") zeros++;
      else confirmed++;
    }
  }
  if (periods.size > 1) throw Error("Carga un archivo con un solo mes de referencia.");
  return {
    total: rows.length,
    confirmed,
    rejected,
    excluded,
    zeros,
    reasons,
    period: periods.values().next().value ?? "",
    rows: [...counts.values()],
  };
}
