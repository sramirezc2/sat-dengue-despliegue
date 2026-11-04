import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import { getDashboardConfig } from "./dashboard-config";

/**
 * Periodos que el servicio tiene publicados, consultados en `/api/salud`.
 *
 * El selector de mes nativo del navegador se renderiza en el idioma del
 * navegador, no en el de la pagina, y permite elegir cualquier mes de la
 * historia: un usuario llegaba a un 404 sin saber por que. Pedir al servicio
 * que diga que publico convierte el control en una lista corta y correcta.
 */
const saludSchema = z.object({
  periodos_por_departamento: z.record(z.string(), z.array(z.string())),
});

export type PeriodosPorDepartamento = Record<string, string[]>;

export async function obtenerPeriodos(signal?: AbortSignal): Promise<PeriodosPorDepartamento> {
  const { apiBaseUrl } = getDashboardConfig();
  const url = apiBaseUrl ? `${apiBaseUrl}/api/salud` : "/api/salud";
  const respuesta = await fetch(url, {
    headers: { Accept: "application/json" },
    signal: signal ?? null,
  });
  if (!respuesta.ok) throw new Error(`El servicio respondió ${respuesta.status} en /api/salud.`);
  const cuerpo = saludSchema.safeParse(await respuesta.json());
  if (!cuerpo.success) throw new Error("La respuesta de /api/salud no tiene el formato esperado.");
  const ordenados: PeriodosPorDepartamento = {};
  for (const [departamento, periodos] of Object.entries(cuerpo.data.periodos_por_departamento)) {
    ordenados[departamento] = [...periodos].sort().reverse();
  }
  return ordenados;
}

export function usePeriodos() {
  return useQuery({
    queryKey: ["periodos"],
    queryFn: ({ signal }) => obtenerPeriodos(signal),
    retry: false,
    staleTime: 300_000,
  });
}

const MESES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

/** Convierte `2026-09` en `Septiembre 2026`. */
export function etiquetaPeriodo(periodo: string): string {
  const [anio, mes] = periodo.split("-");
  const indice = Number(mes) - 1;
  return MESES[indice] ? `${MESES[indice]} ${anio}` : periodo;
}
