import { useState } from "react";

import type { DashboardViewModel, FilaRetro } from "@/lib/dashboard-view-model";

/**
 * Retroanalisis de ventana expansiva sobre los anios de desarrollo.
 *
 * Va en su propia seccion, debajo de la comparacion de la corrida congelada y
 * nunca mezclado con ella. Son dos evaluaciones distintas: la corrida mide
 * doce meses de 2025 con 86 inicios, esta mide siete anios con 647. Juntar sus
 * numeros en una tabla sugeriria que son comparables y no lo son.
 *
 * La procedencia va en pantalla, no en una nota al pie: lo produjo el banco de
 * experimentacion del proyecto y no la tuberia cientifica. Quien lea tiene que
 * poder pesarlo.
 */

const coma = (v: number, d = 2) => v.toFixed(d).replace(".", ",");
const costo = (f: FilaRetro) => (f.detected ? f.falseAlerts / f.detected : null);

const ORDEN = ["vigente_mas_g", "endemic_channel", "vigente", "persistence"];

function Barras({ filas, inicios }: { filas: FilaRetro[]; inicios: number }) {
  const max = Math.max(inicios, 1);
  return (
    <div className="grid gap-1">
      {filas.map((f) => {
        const destacado = f.candidate === "vigente_mas_g";
        const referencia = f.candidate === "endemic_channel";
        return (
          <div key={f.candidate} className="grid grid-cols-[9rem_1fr_3.5rem] items-center gap-2">
            <span className={`truncate text-xs ${destacado ? "font-semibold" : ""}`}>
              {f.label}
            </span>
            <span className="relative block h-3 bg-muted">
              <i
                className="absolute inset-y-0 left-0 block"
                style={{
                  width: `${(f.detected / max) * 100}%`,
                  background: referencia
                    ? "var(--zone-exceso)"
                    : destacado
                      ? "var(--primary)"
                      : "var(--muted-foreground)",
                  opacity: destacado || referencia ? 0.85 : 0.4,
                }}
              />
            </span>
            <span className="text-right font-mono text-xs tabular-nums">{f.detected}</span>
          </div>
        );
      })}
    </div>
  );
}

export function Retroanalisis({ view }: { view: DashboardViewModel }) {
  const [horizonte, setHorizonte] = useState<"T+1" | "T+2">("T+1");
  const retro = view.retro;
  if (!retro) return null;

  const delHorizonte = retro.filas.filter((f) => f.horizon === horizonte);
  const acumulado = ORDEN.map((c) =>
    delHorizonte.find((f) => f.year === null && f.candidate === c),
  ).filter((f): f is FilaRetro => f !== undefined);
  const anios = [...new Set(delHorizonte.filter((f) => f.year !== null).map((f) => f.year))].sort(
    (a, b) => (a ?? 0) - (b ?? 0),
  );
  if (acumulado.length === 0) return null;

  const canal = acumulado.find((f) => f.candidate === "endemic_channel");
  const conMargen = acumulado.find((f) => f.candidate === "vigente_mas_g");
  const sinMargen = acumulado.find((f) => f.candidate === "vigente");
  const veces = canal && conMargen && canal.detected ? conMargen.detected / canal.detected : null;

  return (
    <section
      aria-label="Retroanálisis de ventana expansiva"
      className="min-w-0 border border-border bg-card"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-border p-4">
        <div className="grid gap-1">
          <h2 className="text-base font-semibold">Y sobre siete años, no sobre uno</h2>
          <p className="max-w-prose text-sm text-muted-foreground">
            La comparación de arriba mide doce meses. Esta mide{" "}
            <b className="font-semibold text-foreground">
              {retro.desde.slice(0, 4)} a {retro.hasta.slice(0, 4)}
            </b>
            , reentrenando cada año con todo lo anterior y prediciendo el año siguiente:{" "}
            <b className="font-semibold text-foreground">
              {acumulado[0]?.onsets ?? 0} brotes que empezaron
            </b>{" "}
            en vez de 86. Son dos evaluaciones distintas y sus cifras no se suman.
          </p>
        </div>
        <div
          className="inline-flex border border-border-strong"
          role="group"
          aria-label="Horizonte del retroanálisis"
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
          <p className="rotulo mb-2">Brotes anticipados de {acumulado[0]?.onsets ?? 0}</p>
          <Barras filas={acumulado} inicios={acumulado[0]?.onsets ?? 1} />
          {canal && conMargen && veces && (
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              El modelo con el margen anticipa{" "}
              <b className="font-semibold text-foreground">
                {coma(veces, 1)} veces más brotes que el canal endémico
              </b>{" "}
              ({conMargen.detected} contra {canal.detected} de {canal.onsets}),{" "}
              {coma(costo(conMargen) ?? 0) === coma(costo(canal) ?? 0) ? (
                <>
                  <b className="font-semibold text-foreground">al mismo costo por acierto</b>:{" "}
                  {coma(costo(conMargen) ?? 0)} avisos en falso cada uno.
                </>
              ) : (
                <>
                  y cada acierto le cuesta {coma(costo(conMargen) ?? 0)} avisos en falso contra{" "}
                  {coma(costo(canal) ?? 0)} del canal.
                </>
              )}
              {sinMargen && (
                <>
                  {" "}
                  Sin el margen el mismo modelo anticipa {sinMargen.detected} a{" "}
                  {coma(costo(sinMargen) ?? 0)}: esa diferencia es lo que aporta la variable.
                </>
              )}
            </p>
          )}
        </div>

        <div className="min-w-0 overflow-x-auto">
          <table className="w-full min-w-[22rem] border-collapse text-sm">
            <caption className="sr-only">
              Desempeño acumulado {retro.desde} a {retro.hasta}, horizonte {horizonte}
            </caption>
            <thead>
              <tr>
                {["Quién avisa", "Brotes", "Cobertura", "En falso", "Falsos por acierto"].map(
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
              {acumulado.map((f) => {
                const k = costo(f);
                return (
                  <tr
                    key={f.candidate}
                    className={`border-b border-border ${f.candidate === "vigente_mas_g" ? "bg-accent font-semibold" : ""}${f.role === "REFERENCE" ? " text-zone-exceso" : ""}`}
                  >
                    <td className="px-2 py-2">{f.label}</td>
                    <td className="px-2 py-2 text-right tabular-nums">
                      {f.detected} de {f.onsets}
                    </td>
                    <td className="px-2 py-2 text-right tabular-nums">
                      {Math.round((f.detected / (f.onsets || 1)) * 100)} %
                    </td>
                    <td className="px-2 py-2 text-right tabular-nums">{f.falseAlerts}</td>
                    <td className="px-2 py-2 text-right tabular-nums">
                      {k === null ? "—" : coma(k)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <table className="mt-4 w-full border-collapse text-xs">
            <caption className="rotulo mb-1 text-left">Año por año, brotes anticipados</caption>
            <thead>
              <tr>
                <th scope="col" className="text-left font-mono font-medium text-muted-foreground">
                  Año
                </th>
                {anios.map((a) => (
                  <th
                    key={a}
                    scope="col"
                    className="text-right font-mono font-medium text-muted-foreground"
                  >
                    {a}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {["endemic_channel", "vigente_mas_g"].map((cand) => {
                const fila = acumulado.find((f) => f.candidate === cand);
                if (!fila) return null;
                return (
                  <tr key={cand} className={cand === "vigente_mas_g" ? "font-semibold" : ""}>
                    <td
                      className={`py-1 pr-2 ${cand === "endemic_channel" ? "text-zone-exceso" : ""}`}
                    >
                      {fila.label}
                    </td>
                    {anios.map((a) => {
                      const f = delHorizonte.find((x) => x.year === a && x.candidate === cand);
                      return (
                        <td key={a} className="py-1 text-right tabular-nums">
                          {f ? f.detected : "—"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
              <tr className="text-muted-foreground">
                <td className="py-1 pr-2">Brotes reales</td>
                {anios.map((a) => {
                  const f = delHorizonte.find((x) => x.year === a);
                  return (
                    <td key={a} className="py-1 text-right tabular-nums">
                      {f ? f.onsets : "—"}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-2 border-t border-border p-4 text-xs leading-relaxed text-muted-foreground">
        <p>
          <b className="font-semibold">Qué es el margen.</b> El canal endémico decide con una línea:
          avisa cuando los casos superan el P75 del mes que viene. El modelo recibía si esa línea se
          cruzó o no, pero no a qué distancia estaba. El margen es esa distancia, y es lo único que
          cambia entre las dos filas del modelo.
        </p>
        <p>
          <b className="font-semibold">De dónde sale esto y qué no es.</b>{" "}
          {retro.propio ? (
            <>
              Lo produjo el banco de experimentación del proyecto, <b>no la tubería científica</b>,
              y por eso no es todavía un resultado del procedimiento evaluado ni cambia su estado de
              gobernanza. Que un tercero reproduzca esta misma validación sobre la tubería real es
              el control que falta.
            </>
          ) : (
            <>Lo produjo la tubería científica del proyecto.</>
          )}{" "}
          El bloque congelado de 2025 no se tocó: esta evaluación termina en{" "}
          {retro.hasta.slice(0, 4)}.
          {retro.semillas.length > 1 && (
            <> El resultado se repitió con {retro.semillas.length} semillas distintas.</>
          )}
        </p>
      </div>
    </section>
  );
}
