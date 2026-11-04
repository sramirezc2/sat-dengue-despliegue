import { useState } from "react";

import type { Candidato, DashboardViewModel } from "@/lib/dashboard-view-model";

/**
 * El modelo contra la regla simple.
 *
 * El tablero declaraba que el modelo no esta aprobado y no mostraba contra que
 * se lo habia medido, de modo que "detecta el 26 % de los inicios" quedaba sin
 * referencia. Con la linea base al lado la cifra se puede juzgar, y aparece el
 * resultado incomodo que explica por que no se aprobo nada: a un mes la regla
 * simple no anticipa ni un brote y aun asi tiene menos falsas por aviso, porque
 * solo senala donde el brote ya empezo. Todo sale de la corrida registrada.
 */

const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)} %`);
const coma = (v: number, d = 1) => v.toFixed(d).replace(".", ",");

function Dispersion({ filas }: { filas: Candidato[] }) {
  const W = 620;
  const H = 330;
  const ML = 48;
  const MR = 96;
  const MT = 20;
  const MB = 48;
  const ix = W - ML - MR;
  const iy = H - MT - MB;

  const maxAlertas = Math.ceil(Math.max(...filas.map((f) => f.alerts ?? 0)) / 100) * 100 + 50;
  const maxInicios = filas[0]?.onsets ?? 86;
  const x = (v: number) => ML + (v / maxAlertas) * ix;
  const y = (v: number) => MT + iy - (v / maxInicios) * iy;

  const publicado = filas.find((f) => f.role === "PUBLISHED");
  const puestos = filas.map((f) => ({ f, cx: x(f.alerts ?? 0), cy: y(f.detected ?? 0) }));

  // Etiquetas primero calculadas, despues dibujadas, para que ningun punto
  // tape un nombre y para separar las que se solapan.
  const colocadas: { x: number; y: number }[] = [];
  const etiquetas = [...puestos]
    .sort((a, b) => a.cy - b.cy)
    .map(({ f, cx, cy }) => {
      const der = cx > ML + ix * 0.72;
      const lx = der ? cx - 12 : cx + 12;
      let ly = cy + 4;
      while (colocadas.some((c) => Math.abs(c.y - ly) < 14 && Math.abs(c.x - lx) < 110)) ly += 15;
      colocadas.push({ x: lx, y: ly });
      return { f, cx, cy, lx, ly, der };
    });

  const ticksY = Array.from({ length: Math.floor(maxInicios / 20) + 1 }, (_, i) => i * 20);
  const ticksX = Array.from({ length: Math.floor(maxAlertas / 200) + 1 }, (_, i) => i * 200);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      role="img"
      aria-label={`Avisos emitidos en el eje horizontal contra brotes anticipados en el vertical. ${filas
        .map((f) => `${f.label}: ${f.detected} de ${f.onsets} con ${f.alerts} avisos`)
        .join("; ")}.`}
      className="block max-w-full"
    >
      {ticksY.map((v) => (
        <g key={v}>
          <line x1={ML} y1={y(v)} x2={ML + ix} y2={y(v)} stroke="var(--border)" strokeWidth={1} />
          <text
            x={ML - 7}
            y={y(v) + 4}
            textAnchor="end"
            fontSize={10.5}
            fontFamily="var(--font-mono)"
            fill="var(--muted-foreground)"
          >
            {v}
          </text>
        </g>
      ))}
      {ticksX.map((v) => (
        <text
          key={v}
          x={x(v)}
          y={H - MB + 18}
          textAnchor="middle"
          fontSize={10.5}
          fontFamily="var(--font-mono)"
          fill="var(--muted-foreground)"
        >
          {v}
        </text>
      ))}
      <text
        x={ML + ix / 2}
        y={H - 8}
        textAnchor="middle"
        fontSize={10.5}
        fill="var(--muted-foreground)"
      >
        avisos emitidos en el año
      </text>
      <text
        x={13}
        y={MT + iy / 2}
        textAnchor="middle"
        fontSize={10.5}
        fill="var(--muted-foreground)"
        transform={`rotate(-90 13 ${MT + iy / 2})`}
      >
        brotes anticipados de {maxInicios}
      </text>

      {publicado && (publicado.detected ?? 0) > 0 && (
        <>
          <line
            x1={x(0)}
            y1={y(0)}
            x2={x(
              Math.min(
                maxAlertas,
                maxInicios / ((publicado.detected ?? 1) / (publicado.alerts ?? 1)),
              ),
            )}
            y2={y(
              Math.min(
                maxInicios,
                ((publicado.detected ?? 0) / (publicado.alerts ?? 1)) *
                  Math.min(
                    maxAlertas,
                    maxInicios / ((publicado.detected ?? 1) / (publicado.alerts ?? 1)),
                  ),
              ),
            )}
            stroke="var(--primary)"
            strokeWidth={1}
            strokeDasharray="3 4"
            opacity={0.5}
          />
          <text
            x={ML + ix}
            y={MT + 12}
            textAnchor="end"
            fontSize={9.5}
            fontFamily="var(--font-mono)"
            fill="var(--primary)"
          >
            igual de eficiente
          </text>
        </>
      )}

      {puestos.map(({ f, cx, cy }) =>
        f.role === "BASELINE" ? (
          <rect
            key={f.label}
            x={cx - 6}
            y={cy - 6}
            width={12}
            height={12}
            fill="none"
            stroke="var(--zone-seguridad)"
            strokeWidth={2.5}
          />
        ) : f.role === "PUBLISHED" ? (
          <circle
            key={f.label}
            cx={cx}
            cy={cy}
            r={7}
            fill="var(--primary)"
            stroke="var(--card)"
            strokeWidth={2}
          />
        ) : (
          <circle
            key={f.label}
            cx={cx}
            cy={cy}
            r={5.5}
            fill="none"
            stroke="var(--muted-foreground)"
            strokeWidth={2}
          />
        ),
      )}
      {etiquetas.map(({ f, cx, cy, lx, ly, der }) => (
        <g key={`t-${f.label}`}>
          {ly - cy > 10 && (
            <line
              x1={cx + (der ? -6 : 6)}
              y1={cy + 3}
              x2={lx + (der ? 2 : -2)}
              y2={ly - 4}
              stroke="var(--border-strong)"
              strokeWidth={1}
            />
          )}
          <text
            x={lx}
            y={ly}
            textAnchor={der ? "end" : "start"}
            fontSize={11}
            fontWeight={f.role === "PUBLISHED" ? 600 : 400}
            fill={
              f.role === "BASELINE"
                ? "var(--zone-seguridad)"
                : f.role === "PUBLISHED"
                  ? "var(--foreground)"
                  : "var(--muted-foreground)"
            }
          >
            {f.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

export function ComparacionModelo({ view }: { view: DashboardViewModel }) {
  const [horizonte, setHorizonte] = useState<"T+1" | "T+2">("T+1");
  const filas = view.candidatos.filter((c) => c.horizon === horizonte);
  if (filas.length === 0) return null;

  const base = filas.find((f) => f.role === "BASELINE");
  const publicado = filas.find((f) => f.role === "PUBLISHED");
  const inicios = filas[0]?.onsets ?? 0;

  const relato =
    base && publicado
      ? (base.detected ?? 0) === 0
        ? `Avisando con ${horizonte === "T+1" ? "un mes" : "dos meses"} de anticipación, la regla simple no anticipa ni un solo brote de los ${inicios}. Tiene sentido: solo señala donde el brote ya empezó, y un brote que empieza es justamente el que todavía no está. Aun así emite ${base.alerts} avisos. El modelo publicado anticipa ${publicado.detected}.`
        : `Con ${horizonte === "T+1" ? "un mes" : "dos meses"} de anticipación la regla simple anticipa ${base.detected} de ${inicios} brotes, y le cuesta ${coma((base.falseAlerts ?? 0) / (base.detected || 1))} avisos en falso por acierto. El modelo publicado anticipa ${publicado.detected}, pagando ${coma((publicado.falseAlerts ?? 0) / (publicado.detected || 1))}.`
      : "";

  return (
    <section
      aria-label="Comparación del modelo con la línea base"
      className="min-w-0 border border-border bg-card"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-border p-4">
        <div className="grid gap-1">
          <h2 className="text-base font-semibold">
            Qué tan bien acierta, comparado con la regla simple
          </h2>
          <p className="max-w-prose text-sm text-muted-foreground">
            Durante el periodo evaluado hubo{" "}
            <b className="font-semibold text-foreground">{inicios} brotes que empezaron</b> en los
            municipios de Tolima y Meta. La{" "}
            <b className="font-semibold text-foreground">regla simple</b> es la forma más básica de
            avisar: señalar los municipios donde el brote ya está ocurriendo.
          </p>
        </div>
        <div
          className="inline-flex border border-border-strong"
          role="group"
          aria-label="Horizonte de pronóstico"
        >
          {(["T+1", "T+2"] as const).map((h) => (
            <button
              key={h}
              type="button"
              aria-pressed={horizonte === h}
              onClick={() => setHorizonte(h)}
              className={`px-3 py-1.5 text-xs ${horizonte === h ? "bg-secondary font-medium text-foreground" : "text-muted-foreground"}`}
            >
              Aviso a {h === "T+1" ? "un mes" : "dos meses"}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-5 p-4 lg:grid-cols-2">
        <div className="min-w-0">
          <Dispersion filas={filas} />
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <li className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: "var(--primary)" }} />
              Modelo publicado
            </li>
            <li className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full border-2 border-muted-foreground" />
              Otros modelos probados
            </li>
            <li className="flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 border-2"
                style={{ borderColor: "var(--zone-seguridad)" }}
              />
              Regla simple
            </li>
          </ul>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{relato}</p>
        </div>

        <div className="min-w-0 overflow-x-auto">
          <table className="w-full min-w-[26rem] border-collapse text-sm">
            <caption className="sr-only">
              Desempeño de cada candidato evaluado en el horizonte {horizonte}
            </caption>
            <thead>
              <tr>
                {["Quién avisa", "Brotes", "Avisos", "En falso", "Falsos por acierto"].map(
                  (h, i) => (
                    <th
                      key={h}
                      scope="col"
                      className={`border-b border-border px-2 py-2 font-mono text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground ${i === 0 ? "text-left" : "text-right"}`}
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr
                  key={f.label}
                  className={`border-b border-border ${f.role === "PUBLISHED" ? "bg-accent font-semibold" : ""}`}
                >
                  <td className="px-2 py-2">
                    {f.label}
                    {f.role === "BASELINE" && (
                      <span className="text-muted-foreground"> · línea base</span>
                    )}
                    {f.role === "PUBLISHED" && (
                      <span className="text-muted-foreground"> · publicado</span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums">
                    {f.detected} de {f.onsets}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums">{f.alerts}</td>
                  <td className="px-2 py-2 text-right tabular-nums">{f.falseAlerts}</td>
                  <td className="px-2 py-2 text-right tabular-nums">
                    {f.detected ? coma((f.falseAlerts ?? 0) / f.detected) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            Ninguno de los modelos fue autorizado. Para aprobarse, un modelo debe anticipar bastante
            más brotes que la regla simple <b className="font-semibold">sin</b> disparar los avisos
            en falso. Los tres fallaron por lo segundo, no por lo primero. El criterio completo está
            en la propuesta de política de decisión del repositorio.
          </p>
        </div>
      </div>

      <p className="border-t border-border p-4 text-xs text-muted-foreground">
        Porcentaje de brotes anticipados: {pct(publicado?.sensitivity ?? null)} el modelo publicado,{" "}
        {pct(base?.sensitivity ?? null)} la regla simple.
      </p>
    </section>
  );
}
