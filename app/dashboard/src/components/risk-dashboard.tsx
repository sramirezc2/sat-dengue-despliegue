import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import boundaries from "@/lib/municipal-boundaries.json";
import { fetchRiskPeriods, fetchRiskRanking } from "@/lib/risk-client";
import { RISK_LEGEND, type Priority, type RiskRanking } from "@/lib/risk-contract";

const normalize = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
const byRank = (a: Priority, b: Priority) =>
  (a.risk_rank ?? 77) - (b.risk_rank ?? 77) ||
  a.municipality_code.localeCompare(b.municipality_code);
const status = (t: Priority) =>
  t.eligibility_status === "INELIGIBLE"
    ? "No elegible"
    : t.selected_for_attention
      ? "Priorizado dentro del cupo"
      : "Fuera del cupo";

export function RiskMap({ rows, department }: { rows: Priority[]; department: "50" | "73" }) {
  const name = department === "50" ? "Meta" : "Tolima";
  const areas = boundaries[department === "50" ? "meta" : "tolima"];
  return (
    <figure className="border border-border bg-card p-4">
      <figcaption className="font-semibold">{name} · prioridades T+2</figcaption>
      <svg viewBox="0 0 1000 400" role="img" aria-label={`Mapa de prioridades de ${name}`}>
        {areas.map((area) => {
          const row = rows.find(
            (r) =>
              r.department_code === department &&
              normalize(r.municipality_name) === normalize(area.name),
          );
          return (
            <path
              key={area.id}
              d={area.path}
              fillRule="evenodd"
              fill={row?.selected_for_attention ? "var(--primary)" : "var(--muted)"}
              stroke="var(--border-strong)"
              strokeWidth="0.7"
            >
              <title>
                {area.name}:{" "}
                {row
                  ? `${status(row)} · posición ${row.risk_rank ?? "no disponible"}`
                  : "Sin correspondencia cartográfica"}
              </title>
            </path>
          );
        })}
      </svg>
      <p className="text-xs text-muted-foreground">
        Color de acento: seleccionado. Gris: resto del territorio.
      </p>
    </figure>
  );
}

export function RiskContent({ ranking }: { ranking: RiskRanking }) {
  const [department, setDepartment] = useState("");
  const [search, setSearch] = useState("");
  const [selectedCode, setSelectedCode] = useState("");
  const rows = [...ranking.municipalities].sort(byRank);
  const visible = rows.filter(
    (t) =>
      (!department || t.department_code === department) &&
      normalize(t.municipality_name).includes(normalize(search)),
  );
  const selected = visible.filter((t) => t.selected_for_attention);
  const detail = rows.find((t) => t.municipality_code === selectedCode) ?? selected[0];
  return (
    <>
      <section className="border border-border bg-card p-4" aria-label="Gobernanza y alcance">
        <p className="font-semibold">{RISK_LEGEND}</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Configuración seleccionada para el informe. Reproducción histórica aprobada. Champion no
          seleccionado. Datos consolidados: disponibilidad histórica en tiempo real no demostrada.
        </p>
        {ranking.data_kind === "SYNTHETIC" && <p>FUENTES ARTIFICIALES · prueba de software.</p>}
        <p className="mt-2 font-mono text-sm">
          T+2 · objetivo {ranking.target_period} · corte {ranking.data_cutoff}
        </p>
      </section>
      <section
        className="space-y-4 border border-border bg-card p-4"
        aria-label="Prioridades municipales"
      >
        <div className="flex flex-wrap gap-4">
          <label>
            Departamento{" "}
            <select
              aria-label="Departamento"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="border border-border bg-background p-2"
            >
              <option value="">Meta y Tolima</option>
              <option value="50">Meta</option>
              <option value="73">Tolima</option>
            </select>
          </label>
          <label>
            Buscar municipio{" "}
            <input
              aria-label="Buscar municipio"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border border-border bg-background p-2"
            />
          </label>
        </div>
        <h2 className="text-xl font-semibold">Ocho prioridades globales</h2>
        <p>
          {selected.length} de los 8 priorizados globales visibles. Los filtros no reasignan plazas
          ni posiciones.
        </p>
        <ol aria-label="Municipios seleccionados" className="grid gap-3 md:grid-cols-2">
          {selected.map((t) => (
            <li key={t.municipality_code} className="border border-border p-3">
              <button
                type="button"
                onClick={() => setSelectedCode(t.municipality_code)}
                className="text-left"
              >
                <span className="font-mono">Posición global {t.risk_rank}</span>
                <span className="block font-semibold">
                  {t.municipality_name} · {t.department_name}
                </span>
                <span className="text-sm">
                  {ranking.target_period} · {status(t)}
                </span>
              </button>
            </li>
          ))}
        </ol>
        {!selected.length && <p>Ningún municipio priorizado coincide con estos filtros.</p>}
        <details>
          <summary>Ver el universo territorial y las exclusiones</summary>
          <div className="overflow-auto">
            <table className="w-full text-left text-sm">
              <caption>
                Posiciones globales entre {ranking.eligible_count} elegibles de 76 municipios
              </caption>
              <thead>
                <tr>
                  <th>Posición global</th>
                  <th>Municipio</th>
                  <th>Departamento</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((t) => (
                  <tr key={t.municipality_code} className="border-t border-border">
                    <td className="p-2 font-mono">{t.risk_rank ?? "No aplica"}</td>
                    <td>
                      <button type="button" onClick={() => setSelectedCode(t.municipality_code)}>
                        {t.municipality_name}
                      </button>
                    </td>
                    <td>{t.department_name}</td>
                    <td>{status(t)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
      <div className="grid gap-4 lg:grid-cols-2">
        {(!department || department === "50") && (
          <RiskMap rows={ranking.municipalities} department="50" />
        )}
        {(!department || department === "73") && (
          <RiskMap rows={ranking.municipalities} department="73" />
        )}
      </div>
      {detail && (
        <section className="border border-border bg-card p-4" aria-label="Detalle de prioridad">
          <h2 className="font-semibold">
            {detail.municipality_name} · {detail.department_name}
          </h2>
          <p>
            DIVIPOLA {detail.municipality_code} · posición global {detail.risk_rank ?? "no aplica"}{" "}
            · {status(detail)}
          </p>
          {detail.ineligibility_reason && <p>Motivo: {detail.ineligibility_reason}</p>}
          <p>
            Objetivo {ranking.target_period} · horizonte T+2 · corte {ranking.data_cutoff}
          </p>
        </section>
      )}
      <details className="border border-border p-4">
        <summary>Trazabilidad de la publicación</summary>
        <p>
          Datos: {ranking.data_version} · presupuesto global: {ranking.selection_budget}
        </p>
        <dl className="mt-3 space-y-2 break-all font-mono text-xs">
          {Object.entries(ranking.trace).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </details>
    </>
  );
}

export function RiskDashboard() {
  const [chosenPeriod, setChosenPeriod] = useState("");
  const periods = useQuery({
    queryKey: ["risk-periods-v1"],
    queryFn: ({ signal }) => fetchRiskPeriods(signal),
    retry: false,
  });
  const target = chosenPeriod || periods.data?.[0] || "";
  const ranking = useQuery({
    queryKey: ["risk-ranking-v1", target, "T2"],
    queryFn: ({ signal }) => fetchRiskRanking(target, signal),
    enabled: Boolean(target),
    retry: false,
  });
  const failed = periods.isError || ranking.isError;
  return (
    <main className="mx-auto max-w-7xl space-y-5 px-4 py-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="rotulo">SAT Dengue · Meta y Tolima</p>
          <h1 className="text-2xl font-semibold">Prioridades municipales de 2025</h1>
        </div>
        <label>
          Mes objetivo{" "}
          <select
            aria-label="Mes objetivo"
            value={target}
            onChange={(e) => setChosenPeriod(e.target.value)}
            className="border border-border bg-background p-2"
          >
            {!target && <option value="">Sin publicación</option>}
            {(periods.data ?? []).map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
      </header>
      <div role="tablist" aria-label="Horizonte">
        <button role="tab" aria-selected="true" className="border-b-2 border-primary p-3">
          T+2 · principal
        </button>
        <button role="tab" aria-selected="false" disabled className="p-3 text-muted-foreground">
          T+1 · sin publicación secundaria
        </button>
      </div>
      {failed ? (
        <section role="alert">
          <p>No se pudo validar la publicación de prioridades.</p>
          <button
            onClick={() => {
              void periods.refetch();
              if (target) void ranking.refetch();
            }}
          >
            Reintentar
          </button>
        </section>
      ) : ranking.data ? (
        <RiskContent key={target} ranking={ranking.data} />
      ) : (
        <p>
          {periods.isPending || (target && ranking.isPending)
            ? "Consultando prioridades publicadas…"
            : "Todavía no hay una edición de prioridades publicada."}
        </p>
      )}
    </main>
  );
}
