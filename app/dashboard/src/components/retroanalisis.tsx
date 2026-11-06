import { useState } from "react";

import { enVolumen } from "@/lib/curva-retro";
import type { DashboardViewModel, FilaRetro, PuntoCurva } from "@/lib/dashboard-view-model";

/**
 * Retroanalisis de ventana expansiva sobre los anios de desarrollo.
 *
 * Va en su propia seccion, debajo de la comparacion de la corrida congelada y
 * nunca mezclado con ella. Son dos evaluaciones distintas: la corrida mide
 * doce meses de 2025 con 86 inicios, esta mide siete anios con 647.
 *
 * Tres correcciones que esta vista existe para no repetir, las tres salidas de
 * revisiones del equipo y no de releer el propio trabajo:
 *
 * 1. El costo se mide contra INICIO y no contra exceso. Contar una alerta
 *    como acertada porque el municipio ya estaba en exceso favorece al canal,
 *    que alerta justamente ahi, y es el defecto que la propia politica v2 del
 *    proyecto le achaca a la compuerta G5.
 * 2. Se muestra la curva y no un punto. Dos personas midiendo el mismo modelo
 *    a volumenes de alerta distintos sacan conclusiones distintas y las dos
 *    tienen razon en su punto; la curva hace visible de que depende.
 * 3. La linea base es el canal CONDICIONADO: el que ademas solo alerta donde
 *    el municipio no esta en exceso. Sin esa condicion el canal gasta su
 *    presupuesto en filas donde anticipar un inicio es imposible por
 *    definicion, y la ventaja del modelo sale inflada. Es la linea base justa
 *    porque usa la misma informacion que el modelo tiene en X.
 */

const coma = (v: number, d = 2) => v.toFixed(d).replace(".", ",");
const costo = (f: FilaRetro) => (f.detected ? f.falseAlertsOnset / f.detected : null);

const ORDEN = [
  "vigente_mas_g",
  "vigente_mas_g_gated",
  "vigente",
  "endemic_channel_gated",
  "endemic_channel_tuned",
  "endemic_channel",
  "persistence",
];

const COLOR: Record<string, string> = {
  vigente_mas_g: "var(--primary)",
  vigente: "var(--muted-foreground)",
  endemic_channel: "var(--zone-exceso)",
  endemic_channel_gated: "var(--zone-exceso)",
};

const DISCONTINUA: Record<string, string> = {
  vigente: "4 3",
  endemic_channel_gated: "5 3",
};

const EN_LA_CURVA = ["endemic_channel", "endemic_channel_gated", "vigente", "vigente_mas_g"];

function Curva({ puntos, filas }: { puntos: PuntoCurva[]; filas: FilaRetro[] }) {
  const W = 560;
  const H = 300;
  const ML = 46;
  const MR = 14;
  const MT = 14;
  const MB = 44;
  if (puntos.length === 0) return null;

  const maxX = Math.max(...puntos.map((p) => p.alerts));
  const maxY = Math.max(...puntos.map((p) => p.detected), 1);
  const ix = W - ML - MR;
  const iy = H - MT - MB;
  const x = (v: number) => ML + (v / maxX) * ix;
  const y = (v: number) => MT + iy - (v / maxY) * iy;

  const series = EN_LA_CURVA.map((c) => ({
    c,
    pts: puntos.filter((p) => p.candidate === c).sort((a, b) => a.alerts - b.alerts),
  })).filter((s) => s.pts.length > 1);

  // Los puntos de operacion que la tabla cita, para poder leer la curva contra
  // las cifras de al lado.
  const marcas = filas
    .filter((f) =>
      ["endemic_channel", "endemic_channel_gated", "vigente_mas_g"].includes(f.candidate),
    )
    .map((f) => ({ label: f.label, alerts: f.alerts, detected: f.detected, c: f.candidate }));

  const pasosY = [0, Math.round(maxY / 3), Math.round((2 * maxY) / 3), maxY];
  const pasosX = [0, Math.round(maxX / 3), Math.round((2 * maxX) / 3), maxX];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      role="img"
      aria-label={`Inicios anticipados según el volumen de alertas emitidas. ${series
        .map((s) => {
          const ultimo = s.pts[s.pts.length - 1]!;
          return `${s.c}: hasta ${ultimo.detected} con ${ultimo.alerts} alertas`;
        })
        .join(
          ". ",
        )}. La ventaja del modelo depende del volumen: a volúmenes bajos el canal condicionado va parejo, y la distancia se abre al subir.`}
      className="block max-w-full"
    >
      {pasosY.map((v) => (
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
      {pasosX.map((v) => (
        <text
          key={v}
          x={x(v)}
          y={H - MB + 16}
          textAnchor="middle"
          fontSize={10}
          fontFamily="var(--font-mono)"
          fill="var(--muted-foreground)"
        >
          {v}
        </text>
      ))}
      <text
        x={ML + ix / 2}
        y={H - 6}
        textAnchor="middle"
        fontSize={10.5}
        fill="var(--muted-foreground)"
      >
        alertas emitidas en siete años
      </text>

      {series.map(({ c, pts }) => (
        <polyline
          key={c}
          points={pts.map((p) => `${x(p.alerts)},${y(p.detected)}`).join(" ")}
          fill="none"
          stroke={COLOR[c] ?? "var(--muted-foreground)"}
          strokeWidth={c === "vigente_mas_g" ? 2.5 : 1.8}
          strokeDasharray={DISCONTINUA[c]}
          strokeLinejoin="round"
        />
      ))}

      {marcas.map((m) => (
        <g key={m.c}>
          <circle
            cx={x(m.alerts)}
            cy={y(m.detected)}
            r={4}
            fill="var(--card)"
            stroke={COLOR[m.c] ?? "var(--foreground)"}
            strokeWidth={2}
          />
          <text
            x={x(m.alerts)}
            y={y(m.detected) - 9}
            textAnchor="middle"
            fontSize={10}
            fontWeight={600}
            fill={COLOR[m.c] ?? "var(--foreground)"}
          >
            {m.detected}
          </text>
        </g>
      ))}
    </svg>
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
  if (acumulado.length === 0) return null;

  const canal = acumulado.find((f) => f.candidate === "endemic_channel");
  const condicionado = acumulado.find((f) => f.candidate === "endemic_channel_gated");
  const conMargen = acumulado.find((f) => f.candidate === "vigente_mas_g");
  const sinMargen = acumulado.find((f) => f.candidate === "vigente");
  const conCompuerta = acumulado.find((f) => f.candidate === "vigente_mas_g_gated");
  const curva = retro.curva.filter((p) => p.horizon === horizonte);
  const reales = acumulado[0]?.onsets ?? 0;

  const curvaCond = curva.filter((p) => p.candidate === "endemic_channel_gated");
  const curvaModelo = curva.filter((p) => p.candidate === "vigente_mas_g");
  // En el punto de operación de cada uno, cuánto anticipa el otro.
  const modeloEnElPuntoDelCanal = condicionado ? enVolumen(curvaModelo, condicionado.alerts) : null;
  const canalEnElPuntoDelModelo = conMargen ? enVolumen(curvaCond, conMargen.alerts) : null;
  const techoCond = curvaCond.length
    ? {
        alertas: Math.max(...curvaCond.map((p) => p.alerts)),
        inicios: Math.max(...curvaCond.map((p) => p.detected)),
      }
    : null;
  const techoModelo = curvaModelo.length ? Math.max(...curvaModelo.map((p) => p.detected)) : null;

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
            , reentrenando cada año con todo lo anterior y prediciendo el siguiente:{" "}
            <b className="font-semibold text-foreground">{reales} brotes que empezaron</b> en vez de
            86. Son dos evaluaciones distintas y sus cifras no se suman.
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
          <p className="rotulo mb-1">Brotes anticipados según cuántas alertas se emitan</p>
          <Curva puntos={curva} filas={acumulado} />
          <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <li className="flex items-center gap-1.5">
              <span className="h-0.5 w-5" style={{ background: "var(--primary)" }} />
              Modelo con el margen
            </li>
            <li className="flex items-center gap-1.5">
              <span
                className="h-0.5 w-5"
                style={{
                  background:
                    "repeating-linear-gradient(90deg,var(--muted-foreground) 0 4px,transparent 4px 7px)",
                }}
              />
              Modelo sin el margen
            </li>
            <li className="flex items-center gap-1.5">
              <span
                className="h-0.5 w-5"
                style={{
                  background:
                    "repeating-linear-gradient(90deg,var(--zone-exceso) 0 5px,transparent 5px 8px)",
                }}
              />
              Canal condicionado
            </li>
            <li className="flex items-center gap-1.5">
              <span className="h-0.5 w-5" style={{ background: "var(--zone-exceso)" }} />
              Canal endémico
            </li>
          </ul>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            <b className="font-semibold text-foreground">
              Cuánto aporta el modelo depende de cuántas alertas se puedan atender.
            </b>{" "}
            {condicionado && modeloEnElPuntoDelCanal !== null && (
              <>
                Con {condicionado.alerts} alertas el canal condicionado anticipa{" "}
                {condicionado.detected} brotes y el modelo {modeloEnElPuntoDelCanal}.{" "}
              </>
            )}
            {conMargen && canalEnElPuntoDelModelo !== null && (
              <>
                Con {conMargen.alerts}, que es donde está puesto el modelo, son{" "}
                {canalEnElPuntoDelModelo} contra {conMargen.detected}.{" "}
              </>
            )}
            {techoCond && techoModelo !== null && (
              <>
                Y el canal condicionado tiene techo: no puede emitir más de {techoCond.alertas}{" "}
                alertas ni anticipar más de {techoCond.inicios} de {reales} brotes, mientras el
                modelo llega a {techoModelo}. La ventaja del modelo es de escala, no de punto.
              </>
            )}
          </p>
        </div>

        <div className="min-w-0 overflow-x-auto">
          <table className="w-full min-w-[24rem] border-collapse text-sm">
            <caption className="sr-only">
              Desempeño acumulado {retro.desde} a {retro.hasta}, horizonte {horizonte}
            </caption>
            <thead>
              <tr>
                {["Quién avisa", "Brotes", "Alertas", "Falsas por acierto"].map((h, i) => (
                  <th
                    key={h}
                    scope="col"
                    className={`border-b border-border px-2 py-2 font-mono text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground ${i === 0 ? "text-left" : "text-right"}`}
                  >
                    {h}
                  </th>
                ))}
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
                    <td className="px-2 py-2 text-right tabular-nums">{f.alerts}</td>
                    <td className="px-2 py-2 text-right tabular-nums">
                      {k === null ? "—" : coma(k)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="mt-3 grid gap-2 text-xs leading-relaxed text-muted-foreground">
            {canal && condicionado && (
              <p>
                <b className="font-semibold">
                  Qué es el canal condicionado, y por qué es la línea base correcta.
                </b>{" "}
                El canal que se usa hoy alerta cuando los casos superan el P75, esté el municipio
                como esté. Buena parte de esas alertas cae sobre municipios que{" "}
                <i>ya están en exceso</i>, donde anticipar un inicio es imposible por definición. El
                canal condicionado alerta sólo donde el municipio no está en exceso y los casos
                pasan una fracción del P75, elegida con el año anterior: misma regla, sin modelo, y
                con la misma información que el modelo recibe. Con la condición anticipa{" "}
                {condicionado.detected} brotes de {reales} con {condicionado.alerts} alertas, contra{" "}
                {canal.detected} con {canal.alerts}, y pasa de{" "}
                {coma(canal.falseAlertsOnset / Math.max(canal.detected, 1))} a{" "}
                {coma(condicionado.falseAlertsOnset / Math.max(condicionado.detected, 1))} falsas
                por acierto.{" "}
                {condicionado.detected < canal.detected && (
                  <>
                    Anticipa menos brotes que el canal sin condicionar, no más: a este horizonte la
                    condición también descarta municipios que están en exceso hoy y vuelven a
                    empezar dentro del horizonte. Lo que mejora es el costo de cada acierto.{" "}
                  </>
                )}
                <b className="font-semibold">Esta línea base no es nuestra:</b> la propuso una
                revisión del equipo, y publicar la comparación contra el canal sin condicionar
                exageraba la ventaja del modelo.
              </p>
            )}
            {conMargen && sinMargen && (
              <p>
                <b className="font-semibold">Qué aporta el margen.</b> El canal decide con una
                línea; el modelo recibía si esa línea se cruzó, pero no a qué distancia estaba. Con
                esa distancia pasa de {sinMargen.detected} a {conMargen.detected} brotes, con las
                mismas {conMargen.alerts} alertas.
              </p>
            )}
            {conCompuerta && conMargen && (
              <p>
                <b className="font-semibold">La comparación simétrica.</b> Darle al modelo la misma
                condición que al canal lo deja en {conCompuerta.detected} brotes contra{" "}
                {conMargen.detected}
                {conCompuerta.detected === conMargen.detected
                  ? ": a un mes no cambia nada, porque el modelo ya sabía dónde no alertar."
                  : ": a dos meses lo empeora, que es lo que se espera si la condición es la restricción equivocada a ese horizonte."}
              </p>
            )}
            <p>
              <b className="font-semibold">Qué puede mirar la condición, y qué no.</b> A un mes, el
              mes anterior al brote es el mes en curso y se conoce al emitir. A dos meses no: el mes
              anterior al brote todavía no ha ocurrido, así que la condición sólo puede mirar el
              exceso del mes en curso. Usar el otro mes infla la línea base con información que
              nadie tiene al decidir; la bitácora mide cuánto.
            </p>
            <p>
              <b className="font-semibold">Cómo se cuenta una falsa acá.</b> Contra{" "}
              <i>inicio de brote</i>, no contra exceso. Una alerta sobre un municipio que ya está en
              exceso no anticipa nada, y contarla como acierto infla al canal, que alerta justamente
              ahí. Es el defecto que la propuesta de política v2 del repositorio le señala a la
              compuerta vigente, y evitarlo acá es coherencia, no severidad.
            </p>
            <p>
              <b className="font-semibold">De dónde sale esto y qué no es.</b>{" "}
              {retro.propio ? (
                <>
                  Lo produjo el banco de experimentación del proyecto,{" "}
                  <b>no la tubería científica</b>, y por eso no es todavía un resultado del
                  procedimiento evaluado ni cambia su estado de gobernanza. Que un tercero
                  reproduzca esta validación sobre la tubería real es el control que falta.
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
        </div>
      </div>
    </section>
  );
}
