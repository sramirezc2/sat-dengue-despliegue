import type { DashboardViewModel, Muni } from "@/lib/dashboard-view-model";

/**
 * Detalle del municipio elegido en el triaje.
 *
 * Arranca por la decision y no por la cifra. La probabilidad era antes lo mas
 * grande de la pantalla, y es justamente lo que peor se lee: no dice magnitud
 * ni duracion, solo con que probabilidad se cruza un umbral. Aca el titular es
 * la frase que la secretaria necesita y la probabilidad la sostiene.
 *
 * La serie va en casos divididos por el P75 del mes, no en casos crudos,
 * porque el P75 se mueve mes a mes y municipio a municipio: en Ibague va de
 * 141 a 683 segun el mes, de modo que una escala en casos aplasta el ano
 * entero para acomodar enero. En esta unidad el umbral queda fijo en 1,0 y dos
 * municipios se pueden comparar.
 *
 * El pronostico va en un panel aparte con su propia escala, a proposito: el
 * modelo no predice cuantos casos habra, solo con que probabilidad se cruza el
 * umbral. Dibujarlo como un punto mas de la serie sugiere una magnitud que
 * nadie calculo.
 */

const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)} %`);
const coma = (v: number, d = 2) => v.toFixed(d).replace(".", ",");

function GraficoDistancia({ muni }: { muni: Muni }) {
  const W = 640;
  const H = 236;
  const ML = 46;
  const MR = 12;
  const MT = 14;
  const MB = 30;
  const PANEL = 154;
  const HUECO = 22;

  const obs = muni.channel
    .map((p) => (p.observed !== null && p.p75 ? { m: p.month, r: p.observed / p.p75 } : null))
    .filter((p): p is { m: string; r: number } => p !== null);
  if (obs.length < 2) return null;

  const ix = W - ML - MR - PANEL - HUECO;
  const iy = H - MT - MB;
  const yMax = Math.ceil(Math.max(...obs.map((p) => p.r), 1.1) * 4) / 4 + 0.1;
  const x = (i: number) => ML + (i / (obs.length - 1)) * ix;
  const y = (v: number) => MT + iy - (Math.min(v, yMax) / yMax) * iy;
  const xdiv = ML + ix + HUECO / 2;
  const px0 = xdiv + HUECO / 2;

  const pasos =
    yMax <= 1.5
      ? [0, 0.5, 1]
      : yMax <= 4
        ? [0, 1, 2, Math.ceil(yMax)]
        : [0, 1, Math.round(yMax / 2), Math.ceil(yMax)];
  const puntos = obs.map((p, i) => [x(i), y(p.r)] as const);
  const ultimo = puntos[puntos.length - 1]!;
  const pronosticos = [muni.t1, muni.t2];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      role="img"
      aria-label={`${muni.name}: casos observados divididos por el P75 de cada mes. El umbral de exceso es 1,0 y el último mes cerró en ${coma(obs[obs.length - 1]!.r)}. A la derecha, en escala aparte, la probabilidad de superar el umbral en los dos meses siguientes.`}
      className="block max-w-full"
    >
      {yMax > 1 && (
        <rect
          x={ML}
          y={MT}
          width={ix}
          height={y(1) - MT}
          fill="var(--zone-exceso)"
          opacity={0.07}
        />
      )}
      {pasos
        .filter((v) => v <= yMax)
        .map((v) => (
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
              {coma(v, v % 1 ? 1 : 0)}
            </text>
          </g>
        ))}
      <line
        x1={ML}
        y1={y(1)}
        x2={ML + ix}
        y2={y(1)}
        stroke="var(--zone-exceso)"
        strokeWidth={2}
        strokeDasharray="5 4"
      />
      <text
        x={ML + 4}
        y={y(1) - 7}
        fontSize={10.5}
        fontFamily="var(--font-mono)"
        fill="var(--zone-exceso)"
      >
        nivel alto
      </text>

      <polyline
        points={puntos.map((p) => p.join(",")).join(" ")}
        fill="none"
        stroke="var(--foreground)"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {puntos.map((p, i) => (
        <circle
          key={obs[i]!.m}
          cx={p[0]}
          cy={p[1]}
          r={i === puntos.length - 1 ? 4.5 : 2.5}
          fill={i === puntos.length - 1 ? "var(--foreground)" : "var(--card)"}
          stroke="var(--foreground)"
          strokeWidth={1.8}
        />
      ))}
      <text
        x={ultimo[0]}
        y={ultimo[1] - 12}
        textAnchor="middle"
        fontSize={11.5}
        fontWeight={600}
        fill="var(--foreground)"
      >
        {coma(obs[obs.length - 1]!.r)}
      </text>
      {obs.map((p, i) =>
        obs.length > 10 && i % 2 === 1 ? null : (
          <text
            key={p.m}
            x={x(i)}
            y={H - 11}
            textAnchor="middle"
            fontSize={10}
            fontFamily="var(--font-mono)"
            fill="var(--muted-foreground)"
          >
            {p.m}
          </text>
        ),
      )}

      <line
        x1={xdiv}
        y1={MT - 3}
        x2={xdiv}
        y2={H - MB + 5}
        stroke="var(--border)"
        strokeWidth={1}
        strokeDasharray="2 4"
      />
      <text
        x={px0}
        y={MT + 9}
        fontSize={9.5}
        fontFamily="var(--font-mono)"
        fill="var(--muted-foreground)"
      >
        RIESGO DE SUPERARLO
      </text>
      {pronosticos.map((f, k) => {
        const top = MT + 34 + k * 66;
        const alto = 20;
        const p = f.prob ?? 0;
        const u = f.threshold ?? 0;
        return (
          <g key={f.horizon}>
            <text x={px0} y={top - 6} fontSize={10.5} fill="var(--foreground)">
              {f.targetMonth}
            </text>
            <text
              x={px0 + PANEL}
              y={top - 6}
              textAnchor="end"
              fontSize={11.5}
              fontWeight={600}
              fontFamily="var(--font-mono)"
              fill="var(--foreground)"
            >
              {pct(f.prob)}
            </text>
            <rect
              x={px0}
              y={top}
              width={PANEL}
              height={alto}
              fill="var(--card)"
              stroke="var(--border)"
            />
            <rect
              x={px0}
              y={top}
              width={PANEL * Math.min(p, 1)}
              height={alto}
              fill={f.alertStatus === "ALERT" ? "var(--zone-exceso)" : "var(--zone-seguridad)"}
              opacity={0.55}
            />
            <line
              x1={px0 + PANEL * u}
              y1={top - 4}
              x2={px0 + PANEL * u}
              y2={top + alto + 4}
              stroke="var(--foreground)"
              strokeWidth={2}
            />
            <text
              x={px0 + PANEL * u + 4}
              y={top + alto + 15}
              fontSize={9.5}
              fontFamily="var(--font-mono)"
              fill="var(--muted-foreground)"
            >
              avisa desde {pct(f.threshold)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function DetalleMunicipio({ muni, view }: { muni: Muni; view: DashboardViewModel }) {
  const alerta = muni.t1.alertStatus === "ALERT";
  const disponible = muni.t1.available;

  return (
    <section
      aria-label={`Detalle de ${muni.name}`}
      className="min-w-0 border border-border bg-card"
    >
      <div className="grid gap-2 border-b border-border p-5">
        <p className="rotulo">
          {muni.name} · {muni.t1.targetMonth}
        </p>
        {disponible ? (
          <>
            <h2 className="text-xl font-semibold tracking-tight">
              <span className={alerta ? "text-zone-exceso" : "text-zone-exito"}>
                {alerta ? "Se emite alerta" : "No se emite alerta"}
              </span>{" "}
              para {muni.t1.targetMonth.toLowerCase()}
            </h2>
            <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">
              {muni.name} cerró {view.periodLabel.toLowerCase()} con{" "}
              {muni.observedT ?? "un número no disponible de"} casos, en zona de{" "}
              {muni.zoneT.toLowerCase()}. El riesgo de superar su P75 histórico es{" "}
              {pct(muni.t1.prob)}, {alerta ? "por encima" : "por debajo"} del{" "}
              {pct(muni.t1.threshold)} a partir del cual se avisa.
            </p>
          </>
        ) : (
          <>
            <h2 className="text-xl font-semibold tracking-tight">Sin resultado publicado</h2>
            <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">
              {muni.t1.availabilityReason ?? muni.t1.availabilityLabel}
            </p>
          </>
        )}
      </div>

      <div className="grid grid-cols-2 gap-px border-b border-border bg-border md:grid-cols-4">
        {[
          { r: `Casos en ${view.periodLabel.split(" ")[0]}`, v: String(muni.observedT ?? "—") },
          { r: "Zona del canal", v: muni.zoneT },
          {
            r: "P25 · mediana · P75",
            v: [muni.p25, muni.median, muni.p75].map((n) => n ?? "—").join(" · "),
          },
          {
            r: muni.t2.targetMonth,
            v: `${pct(muni.t2.prob)} · ${muni.t2.alertStatus === "ALERT" ? "alerta" : "sin alerta"}`,
          },
        ].map((c) => (
          <div key={c.r} className="grid gap-1 bg-card p-4">
            <span className="rotulo">{c.r}</span>
            <b className="text-base font-semibold tabular-nums">{c.v}</b>
          </div>
        ))}
      </div>

      <div className="p-4">
        <GraficoDistancia muni={muni} />
      </div>

      <ul className="flex flex-wrap gap-x-4 gap-y-1 px-4 pb-4 text-xs text-muted-foreground">
        <li className="flex items-center gap-1.5">
          <span className="h-0.5 w-5 bg-foreground" />
          Casos del mes ÷ P75 del mes
        </li>
        <li className="flex items-center gap-1.5">
          <span className="h-0.5 w-5" style={{ background: "var(--zone-exceso)" }} />
          Nivel alto (1,0)
        </li>
        <li className="flex items-center gap-1.5">
          <span
            className="h-2 w-5"
            style={{ background: "var(--zone-seguridad)", opacity: 0.55 }}
          />
          Riesgo en escala propia, rojo si cruza el punto de aviso
        </li>
      </ul>

      <p className="border-t border-border p-4 text-xs leading-relaxed text-muted-foreground">
        La línea no muestra casos sueltos sino{" "}
        <b className="font-semibold">casos divididos por el P75 de ese mes</b>, porque ese nivel
        cambia mes a mes y municipio a municipio. Así el 1,0 significa siempre lo mismo y dos
        municipios se pueden comparar. El riesgo va aparte porque mide otra cosa: con qué
        probabilidad se cruza el nivel, no cuántos casos habrá.
      </p>
    </section>
  );
}
