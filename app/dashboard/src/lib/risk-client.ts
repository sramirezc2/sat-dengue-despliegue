import { getDashboardConfig } from "./dashboard-config";
import { riskPeriodsSchema, riskViewSchema } from "./risk-contract";

/** Consultar exclusivamente resultados persistidos del contrato de prioridades. */
async function request(path: string, signal?: AbortSignal): Promise<unknown> {
  const base = getDashboardConfig().apiBaseUrl;
  const response = await fetch(base ? new URL(path, `${base}/`) : path, {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("No se pudo consultar la publicación de prioridades.");
  return response.json();
}

export async function fetchRiskPeriods(signal?: AbortSignal) {
  return riskPeriodsSchema.parse(await request("/api/prioridades/v1/periodos", signal));
}

export async function fetchRiskRanking(target: string, signal?: AbortSignal) {
  const query = new URLSearchParams({ target_period: target, horizon: "T2" });
  return riskViewSchema.parse(await request(`/api/prioridades/v1?${query}`, signal)).ranking;
}
