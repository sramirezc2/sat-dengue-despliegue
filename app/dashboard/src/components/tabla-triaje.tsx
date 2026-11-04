import { useMemo, useState } from "react";

import type { Muni, Zone } from "@/lib/dashboard-view-model";

/**
 * Triaje del departamento.
 *
 * El tablero respondia "como esta este municipio", de a uno, por un desplegable
 * de 47 entradas. La pregunta que una secretaria de salud tiene que resolver es
 * otra: a cuales de sus municipios manda equipo este mes. Esta tabla responde
 * esa, y la vista de municipio pasa a ser el detalle al que se entra desde aca.
 *
 * No consume nada nuevo del API: la respuesta del departamento ya trae los
 * municipios con su zona, sus casos y sus dos pronosticos.
 */

/** Las cuatro zonas son una escala ordenada. La luminancia de los tonos
 *  convencionales no es monotona, asi que el orden no puede ir en el color: lo
 *  lleva la cantidad de segmentos llenos, y el nombre va siempre al lado. */
const NIVEL: Record<Zone, number> = {
  Éxito: 1,
  Seguridad: 2,
  Alerta: 3,
  Exceso: 4,
  "No disponible": 0,
};

const COLOR_ZONA: Record<Zone, string> = {
  Éxito: "var(--zone-exito)",
  Seguridad: "var(--zone-seguridad)",
  Alerta: "var(--zone-alerta)",
  Exceso: "var(--zone-exceso)",
  "No disponible": "var(--muted-foreground)",
};

const ZONAS: Zone[] = ["Exceso", "Alerta", "Seguridad", "Éxito"];

function NivelZona({ zone }: { zone: Zone }) {
  const n = NIVEL[zone];
  return (
    <span className="inline-flex flex-none gap-px" style={{ color: COLOR_ZONA[zone] }} aria-hidden>
      {[1, 2, 3, 4].map((k) => (
        <i
          key={k}
          className="block h-3 w-1"
          style={{ background: k <= n ? "currentColor" : "var(--border)" }}
        />
      ))}
    </span>
  );
}

const sinTildes = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)} %`);

export function TablaTriaje({
  munis,
  selected,
  onSelect,
  targetMonth,
}: {
  munis: Muni[];
  selected: string;
  onSelect: (id: string) => void;
  targetMonth: string;
}) {
  const [texto, setTexto] = useState("");
  const [zona, setZona] = useState<"" | Zone>("");
  const [soloAlerta, setSoloAlerta] = useState(false);

  const ordenados = useMemo(
    () => [...munis].sort((a, b) => (b.t1.prob ?? -1) - (a.t1.prob ?? -1)),
    [munis],
  );
  const enAlerta = ordenados.filter((m) => m.t1.alertStatus === "ALERT").length;
  const busqueda = sinTildes(texto.trim());
  const filtrados = ordenados.filter(
    (m) =>
      (!busqueda || sinTildes(m.name).includes(busqueda)) &&
      (!zona || m.zoneT === zona) &&
      (!soloAlerta || m.t1.alertStatus === "ALERT"),
  );

  const limpiar = () => {
    setTexto("");
    setZona("");
    setSoloAlerta(false);
  };

  return (
    <section aria-label="Triaje de municipios" className="min-w-0 border border-border bg-card">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border p-4">
        <h2 className="text-base font-semibold">Riesgo para {targetMonth}</h2>
        <div className="flex flex-wrap gap-2 font-mono text-xs">
          <span className="border border-zone-exceso px-2 py-1 text-zone-exceso">
            <b className="font-semibold">{enAlerta}</b> en alerta
          </span>
          <span className="border border-border px-2 py-1">
            <b className="font-semibold">{ordenados.length - enAlerta}</b> sin alerta
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-border bg-muted/50 p-3">
        <input
          type="search"
          id="triaje-buscar"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Buscar municipio…"
          aria-label="Buscar municipio por nombre"
          className="min-w-0 flex-1 border border-border-strong bg-input px-2 py-1.5 text-sm"
        />
        <select
          id="triaje-zona"
          value={zona}
          onChange={(e) => setZona(e.target.value as "" | Zone)}
          aria-label="Filtrar por zona del canal endémico"
          className="border border-border-strong bg-input px-2 py-1.5 text-sm"
        >
          <option value="">Todas las zonas</option>
          {ZONAS.map((z) => (
            <option key={z} value={z}>
              {z}
            </option>
          ))}
        </select>
        <div
          className="inline-flex border border-border-strong"
          role="group"
          aria-label="Filtrar por estado de alerta"
        >
          {[
            { k: false, t: "Todos" },
            { k: true, t: "Solo en alerta" },
          ].map(({ k, t }) => (
            <button
              key={t}
              type="button"
              aria-pressed={soloAlerta === k}
              onClick={() => setSoloAlerta(k)}
              className={`px-3 py-1.5 text-xs ${soloAlerta === k ? "bg-secondary font-medium text-foreground" : "text-muted-foreground"}`}
            >
              {t}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={limpiar}
          className="text-xs text-muted-foreground underline underline-offset-4"
        >
          Limpiar
        </button>
      </div>

      <div className="max-h-96 overflow-auto">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <caption className="sr-only">
            Municipios del departamento ordenados por riesgo estimado para {targetMonth}
          </caption>
          <thead>
            <tr>
              {["Municipio", "Casos", "Zona del canal", "Riesgo contra umbral", "Riesgo"].map(
                (h, i) => (
                  <th
                    key={h}
                    scope="col"
                    className={`sticky top-0 z-10 border-b border-border bg-secondary px-2 py-2 font-mono text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground ${i === 1 || i === 4 ? "text-right" : "text-left"}`}
                  >
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {filtrados.map((m) => {
              const alerta = m.t1.alertStatus === "ALERT";
              const prob = m.t1.prob ?? 0;
              const umbral = m.t1.threshold ?? 0;
              return (
                <tr
                  key={m.id}
                  onClick={() => onSelect(m.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(m.id);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`${m.name}, zona ${m.zoneT}, riesgo ${pct(m.t1.prob)}${alerta ? ", en alerta" : ""}`}
                  aria-pressed={m.id === selected}
                  className={`cursor-pointer border-b border-border ${m.id === selected ? "bg-accent shadow-[inset_3px_0_0_var(--primary)]" : "hover:bg-muted/60"}`}
                >
                  <td className="px-2 py-2 font-medium">{m.name}</td>
                  <td className="px-2 py-2 text-right tabular-nums">{m.observedT ?? "—"}</td>
                  <td className="px-2 py-2">
                    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
                      <NivelZona zone={m.zoneT} />
                      {m.zoneT}
                    </span>
                  </td>
                  <td className="px-2 py-2">
                    <span className="relative block h-3.5 min-w-24 border border-border bg-muted">
                      <i
                        className="absolute inset-y-0 left-0 block"
                        style={{
                          width: `${(prob * 100).toFixed(1)}%`,
                          background: alerta ? "var(--zone-exceso)" : "var(--muted-foreground)",
                          opacity: alerta ? 0.75 : 0.45,
                        }}
                      />
                      <i
                        className="absolute -top-0.5 -bottom-0.5 block w-0.5 bg-foreground"
                        style={{ left: `${(umbral * 100).toFixed(1)}%` }}
                      />
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right font-mono tabular-nums">{pct(m.t1.prob)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtrados.length === 0 && (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Ningún municipio coincide con el filtro.
          </p>
        )}
      </div>

      <p className="border-t border-border p-3 text-xs leading-relaxed text-muted-foreground">
        Ordenado de mayor a menor riesgo. <b className="font-semibold">Riesgo</b> es la probabilidad
        estimada de que el municipio supere en {targetMonth} su P75 histórico de casos. La línea
        vertical de cada barra es el punto a partir del cual se emite alerta. Elegí una fila para
        ver el detalle.
      </p>
    </section>
  );
}
