import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import {
  AlertTriangle,
  ShieldOff,
  Activity,
  CalendarClock,
  Database,
  FileCode2,
  Bell,
  BellOff,
  CircleSlash,
  ChevronDown,
  Info,
  MapPinned,
  Eye,
  Copy,
  Check,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import {
  DEPTS,
  MONTHS,
  MONTHS_FULL,
  DEFAULT_PERIODS,
  DEPARTMENT_CODES,
  type Dept,
  type Zone,
  type Forecast,
  type Muni,
  type DashboardViewModel,
} from "@/lib/dashboard-view-model";
import { Button } from "@/components/ui/button";
import { MunicipalMap } from "@/components/municipal-map";
import { TablaTriaje } from "@/components/tabla-triaje";
import { DetalleMunicipio } from "@/components/detalle-municipio";
import { useDashboard } from "@/lib/use-dashboard";
import { DashboardClientError } from "@/lib/dashboard-client";
import { etiquetaPeriodo, usePeriodos } from "@/lib/periodos";
import { getDashboardConfig } from "@/lib/dashboard-config";
import { enlacesDeEvidencia, textoDeGobernanza } from "@/lib/gobernanza";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Alerta Temprana de Dengue — Tolima y Meta" },
      {
        name: "description",
        content:
          "Tablero de solo lectura para vigilancia de dengue en Tolima y Meta: canal endémico, pronósticos T+1 y T+2 y desempeño del procedimiento evaluado.",
      },
      { property: "og:title", content: "Alerta Temprana de Dengue — Tolima y Meta" },
      {
        property: "og:description",
        content: "Canal endémico, pronósticos T+1 y T+2 y estado de gobernanza del modelo.",
      },
      { property: "og:type", content: "website" },
    ],
  }),
  component: Dashboard,
});

const ZONE_STYLE: Record<Zone, { cls: string; var: string; icon: string }> = {
  Éxito: {
    cls: "text-zone-exito border-zone-exito/40 bg-zone-exito/10",
    var: "var(--zone-exito)",
    icon: "▼",
  },
  Seguridad: {
    cls: "text-zone-seguridad border-zone-seguridad/40 bg-zone-seguridad/10",
    var: "var(--zone-seguridad)",
    icon: "●",
  },
  Alerta: {
    cls: "text-zone-alerta border-zone-alerta/40 bg-zone-alerta/10",
    var: "var(--zone-alerta)",
    icon: "▲",
  },
  Exceso: {
    cls: "text-zone-exceso border-zone-exceso/40 bg-zone-exceso/10",
    var: "var(--zone-exceso)",
    icon: "◆",
  },
  "No disponible": {
    cls: "text-muted-foreground border-border bg-muted",
    var: "var(--map-unavailable)",
    icon: "–",
  },
};
const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)} %`);

function ZoneBadge({ zone }: { zone: Zone }) {
  const z = ZONE_STYLE[zone];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold ${z.cls}`}
    >
      <span aria-hidden>{z.icon}</span>
      {zone}
    </span>
  );
}
function AlertBadge({ f }: { f: Forecast }) {
  if (!f.available)
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground"
        title={f.availabilityReason ?? f.availabilityLabel}
      >
        <CircleSlash className="h-3.5 w-3.5" />
        {f.availabilityLabel}
      </span>
    );
  return f.alertStatus === "ALERT" ? (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zone-exceso/40 bg-zone-exceso/10 px-2 py-0.5 text-xs font-semibold text-zone-exceso">
      <Bell className="h-3.5 w-3.5" />
      Alerta emitida
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zone-exito/40 bg-zone-exito/10 px-2 py-0.5 text-xs font-semibold text-zone-exito">
      <BellOff className="h-3.5 w-3.5" />
      Sin alerta
    </span>
  );
}
function Card({
  title,
  children,
  className = "",
  aside,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  aside?: React.ReactNode;
}) {
  return (
    <section className={`border border-border bg-card ${className}`} aria-label={title}>
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-5 py-3">
        <h2 className="rotulo">{title}</h2>
        {aside}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}

function useBogotaNow() {
  const [now, setNow] = useState<string>("");
  useEffect(() => {
    const fmt = () =>
      new Intl.DateTimeFormat("es-CO", {
        timeZone: "America/Bogota",
        dateStyle: "long",
        timeStyle: "short",
      }).format(new Date());
    setNow(fmt());
    const t = setInterval(() => setNow(fmt()), 30000);
    return () => clearInterval(t);
  }, []);
  return now;
}

export function Dashboard() {
  const [dept, setDept] = useState<Dept>("tolima");
  const [period, setPeriod] = useState(DEFAULT_PERIODS.tolima);
  const [muniId, setMuniId] = useState("");
  const [vista, setVista] = useState<"vigilar" | "acierta">("vigilar");
  const periodos = usePeriodos();
  const now = useBogotaNow();
  // Memorizado porque `?? []` crea un arreglo nuevo en cada render, y ese
  // arreglo es dependencia del efecto de mas abajo: sin esto el efecto se
  // reevalua siempre, aunque los periodos publicados no hayan cambiado.
  const periodosDelDepto = useMemo(
    () => periodos.data?.[DEPARTMENT_CODES[dept]] ?? [],
    [periodos.data, dept],
  );
  const periodoVigente = periodosDelDepto[0];

  // No se consulta hasta saber que periodos publico el servicio. Preguntar por
  // uno inventado devolvia 404 en la primera carga y hacia parpadear la
  // tarjeta de error antes de corregirse sola.
  const periodoConocido = periodos.isError || periodosDelDepto.includes(period);
  const dashboard = useDashboard(DEPARTMENT_CODES[dept], period, {
    enabled: periodos.isFetched && periodoConocido,
  });

  // El periodo por defecto no puede estar quemado en el codigo: lo publicado
  // cambia cada vez que se agrega una corrida. Si el seleccionado no esta
  // entre los publicados, el tablero se mueve al mas reciente que si exista.
  useEffect(() => {
    if (periodoVigente && !periodosDelDepto.includes(period)) {
      setPeriod(periodoVigente);
      setMuniId("");
    }
  }, [periodoVigente, periodosDelDepto, period]);

  const switchDept = (d: Dept) => {
    setDept(d);
    const publicados = periodos.data?.[DEPARTMENT_CODES[d]] ?? [];
    setPeriod(publicados[0] ?? DEFAULT_PERIODS[d]);
    setMuniId("");
  };

  const view = dashboard.data ?? null;
  const munis = view?.municipalities ?? [];
  const muni = munis.find((item) => item.id === muniId) ?? munis[0] ?? null;

  // El encabezado se arma siempre, tambien sin datos. Si un periodo no tiene
  // resultado el usuario tiene que poder cambiar de departamento o de mes; la
  // version anterior reemplazaba la pantalla entera por la tarjeta de error y
  // lo dejaba sin controles.
  const encabezado = (
    <Encabezado
      dept={dept}
      onDept={switchDept}
      period={period}
      periodos={periodosDelDepto}
      onPeriod={(valor) => {
        setPeriod(valor);
        setMuniId("");
      }}
      munis={munis}
      muniId={muni?.id ?? ""}
      onMuni={setMuniId}
      view={view}
      muni={muni}
      now={now}
    />
  );

  if (dashboard.isError || view === null || muni === null) {
    const cargando =
      !dashboard.isError && (periodos.isPending || !periodoConocido || dashboard.isPending);
    return (
      <div className="min-h-screen bg-background">
        {encabezado}
        <main className="mx-auto max-w-7xl px-4 py-12">
          {!cargando && dashboard.isError ? (
            <DashboardError
              error={dashboard.error}
              onRetry={() => void dashboard.refetch()}
              onReset={() => {
                setPeriod(periodoVigente ?? DEFAULT_PERIODS[dept]);
                setMuniId("");
              }}
            />
          ) : (
            <DashboardState
              title="Cargando resultados"
              message="Consultando el servicio de solo lectura."
            />
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {encabezado}

      <main className="mx-auto max-w-7xl space-y-5 px-4 py-6">
        {/* 1. Gobernanza. Una linea, no un bloque: la politica del proyecto
            exige declarar el estado, pero explicarlo en extenso ocupaba el
            lugar de la informacion y no ayudaba a nadie a decidir. */}
        <section
          aria-label="Estado de gobernanza del modelo"
          className="border-b border-border pb-4 text-sm leading-relaxed text-muted-foreground"
        >
          <span className="font-semibold text-foreground">
            {view.governanceStatus === "APPROVED" ? "Modelo aprobado." : "Ejercicio de evaluación."}
          </span>{" "}
          {textoDeGobernanza(view.governanceStatus, view.championStatus, view.periodYear)}{" "}
          {enlacesDeEvidencia(getDashboardConfig().repositorioUrl).map((enlace) => (
            <a
              key={enlace.href}
              href={enlace.href}
              title={enlace.descripcion}
              target="_blank"
              rel="noreferrer noopener"
              className="ml-3 inline-flex items-center gap-1 whitespace-nowrap text-primary underline underline-offset-4"
            >
              {enlace.rotulo}
              <ExternalLink aria-hidden className="h-3 w-3" />
            </a>
          ))}
        </section>

        {/* El tablero responde dos preguntas distintas y antes las mezclaba en
            una sola pagina larga. Separadas, cada una se puede leer entera. */}
        <nav role="tablist" aria-label="Vistas del tablero" className="flex border-b border-border">
          {[
            { k: "vigilar" as const, t: "Qué municipios vigilar" },
            { k: "acierta" as const, t: "Qué tan bien acierta" },
          ].map(({ k, t }) => (
            <button
              key={k}
              type="button"
              role="tab"
              id={`tab-${k}`}
              aria-selected={vista === k}
              aria-controls={`panel-${k}`}
              onClick={() => setVista(k)}
              className={`-mb-px border-b-2 px-4 py-3 text-sm font-medium ${
                vista === k
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </nav>

        {vista === "vigilar" ? (
          <div
            id="panel-vigilar"
            role="tabpanel"
            aria-labelledby="tab-vigilar"
            className="space-y-5"
          >
            {/* El triaje va antes del detalle porque la primera pregunta de una
                secretaria es a cuales municipios atender, no como esta uno. */}
            <div className="grid gap-5 lg:grid-cols-2">
              <TablaTriaje
                munis={munis}
                selected={muni.id}
                onSelect={setMuniId}
                targetMonth={muni.t1.targetMonth}
              />
              <DetalleMunicipio muni={muni} view={view} />
            </div>

            {/* Las tarjetas de pronostico dejan de ser el titular -esa es ahora
                la frase de decision- pero se quedan: son las que exponen la
                trazabilidad del resultado, limitada a los cinco campos
                autorizados. */}
            <div className="grid gap-5 lg:grid-cols-2">
              {[muni.t1, muni.t2].map((f) => (
                <ForecastCard key={`${muni.id}-${f.horizon}`} f={f} />
              ))}
            </div>

            <div className="grid gap-5 lg:grid-cols-5">
              <TerritoryMap dept={dept} munis={munis} selected={muni.id} onSelect={setMuniId} />
              <HorizonChart muni={muni} />
            </div>

            <ChannelChart muni={muni} view={view} />
          </div>
        ) : (
          <div
            id="panel-acierta"
            role="tabpanel"
            aria-labelledby="tab-acierta"
            className="space-y-5"
          >
            <HistoryCard view={view} />
          </div>
        )}

        <footer className="pb-6 pt-2 text-center text-xs text-muted-foreground">
          Resultados de evaluación de un candidato provisional. No reemplazan el criterio del
          experto ni constituyen aprobación científica.
        </footer>
      </main>
    </div>
  );
}

function Encabezado({
  dept,
  onDept,
  period,
  periodos,
  onPeriod,
  munis,
  muniId,
  onMuni,
  view,
  muni,
  now,
}: {
  dept: Dept;
  onDept: (d: Dept) => void;
  period: string;
  periodos: string[];
  onPeriod: (valor: string) => void;
  munis: Muni[];
  muniId: string;
  onMuni: (id: string) => void;
  view: DashboardViewModel | null;
  muni: Muni | null;
  now: string;
}) {
  const sinDato = "—";
  const procedimientos =
    muni === null
      ? sinDato
      : `${muni.t1.procedureId ?? sinDato} / ${muni.t2.procedureId ?? sinDato}`;

  return (
    <>
      {(view?.demonstrativeValues ?? true) && (
        <div
          role="alert"
          className="sticky top-0 z-50 border-b border-warn-foreground/20 bg-warn px-4 py-1.5 text-center text-[11px] font-semibold uppercase tracking-[0.12em] text-warn-foreground"
        >
          Datos demostrativos · no usar para decisiones operativas
        </div>
      )}

      <header className="border-b border-border-strong">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h1 className="text-xl font-semibold tracking-tight lg:whitespace-nowrap">
                Alerta Temprana de Dengue
              </h1>
              <span className="cifra border border-border px-1.5 py-px text-[10px] uppercase tracking-wider text-muted-foreground">
                solo lectura
              </span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Vigilancia epidemiológica municipal · Tolima y Meta · Secretarías departamentales de
              salud
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-xs md:grid-cols-4 lg:text-right">
            {[
              ["Hora en Bogotá", now || sinDato],
              ["Datos actualizados", view?.dataUpdatedAt ?? sinDato],
              ["Resultado generado", view?.generatedAt ?? sinDato],
              ["Procedimiento", procedimientos],
            ].map(([rotulo, valor]) => (
              <div key={rotulo}>
                <dt className="rotulo">{rotulo}</dt>
                <dd className="cifra mt-0.5 text-foreground">{valor}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 pb-0">
          <div role="tablist" aria-label="Departamento" className="flex">
            {(Object.keys(DEPTS) as Dept[]).map((d) => (
              <button
                key={d}
                role="tab"
                aria-selected={dept === d}
                onClick={() => onDept(d)}
                className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                  dept === d
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {DEPTS[d]}
              </button>
            ))}
          </div>

          <div className="mb-2 ml-auto flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
            <label className="flex items-center gap-2">
              <span className="rotulo">Municipio</span>
              <select
                value={muniId}
                onChange={(e) => onMuni(e.target.value)}
                disabled={munis.length === 0}
                className="min-h-9 border border-input bg-background px-2 py-1 text-sm text-foreground disabled:opacity-50"
              >
                {munis.length === 0 ? (
                  <option value="">Sin municipios</option>
                ) : (
                  munis.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))
                )}
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="rotulo">Mes T</span>
              <select
                value={period}
                onChange={(event) => onPeriod(event.target.value)}
                disabled={periodos.length === 0}
                className="min-h-9 border border-input bg-background px-2 py-1 text-sm text-foreground disabled:opacity-50"
                aria-label="Periodo de referencia"
              >
                {periodos.length === 0 ? (
                  <option value={period}>{etiquetaPeriodo(period)}</option>
                ) : (
                  periodos.map((valor) => (
                    <option key={valor} value={valor}>
                      {etiquetaPeriodo(valor)}
                    </option>
                  ))
                )}
              </select>
            </label>
          </div>
        </div>
      </header>
    </>
  );
}

function DashboardState({ title, message }: { title: string; message: string }) {
  return (
    <section className="mx-auto max-w-lg border border-border bg-card p-8" role="status">
      <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
    </section>
  );
}

function DashboardError({
  error,
  onRetry,
  onReset,
}: {
  error: Error;
  onRetry: () => void;
  onReset: () => void;
}) {
  const clientError = error instanceof DashboardClientError ? error : null;
  const title =
    clientError?.status === 400
      ? "Parámetros inválidos"
      : clientError?.status === 404
        ? "No hay resultados para este departamento y periodo"
        : clientError?.status === 500
          ? "Error interno del API"
          : clientError?.kind === "contract"
            ? "Respuesta incompatible"
            : clientError?.kind === "config"
              ? "Configuración inválida"
              : "Error de red";
  return (
    <section
      className="mx-auto max-w-lg border-l-2 border-zone-alerta bg-card p-8 ring-1 ring-border"
      role="alert"
    >
      <p className="rotulo">No se pudo mostrar el resultado</p>
      <h2 className="mt-2 text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
      <p className="mt-4 text-sm text-muted-foreground">
        El departamento y el mes siguen disponibles arriba: puedes elegir otro sin recargar.
      </p>
      <div className="mt-5 flex flex-wrap gap-2">
        <Button onClick={onRetry}>
          <RefreshCw /> Reintentar
        </Button>
        <Button variant="secondary" onClick={onReset}>
          Volver al periodo con datos
        </Button>
      </div>
    </section>
  );
}

function ForecastCard({ f }: { f: Forecast }) {
  const [detail, setDetail] = useState(false);
  const [copyMessage, setCopyMessage] = useState("");
  const copyIdentifier = async () => {
    if (!f.resultId) return;
    try {
      await navigator.clipboard.writeText(f.resultId);
      setCopyMessage("Identificador copiado");
    } catch {
      setCopyMessage("No se pudo copiar el identificador");
    }
  };
  return (
    <Card
      title={`Pronóstico ${f.horizon}`}
      aside={
        <span className={detail ? "invisible" : ""} aria-hidden={detail}>
          <AlertBadge f={f} />
        </span>
      }
    >
      <span className="sr-only" role="status" aria-live="polite">
        {detail ? `Detalle del resultado ${f.horizon}` : `Resultado ${f.horizon}`}. {copyMessage}
      </span>
      <div className="grid">
        <div
          className={`col-start-1 row-start-1 transition-opacity duration-150 motion-reduce:transition-none ${detail ? "invisible opacity-0" : "visible opacity-100"}`}
          aria-hidden={detail}
          inert={detail}
        >
          <p className="text-sm text-muted-foreground">
            Mes objetivo: <b className="text-foreground">{f.targetMonth}</b>
          </p>
          {f.available && f.prob !== null && f.threshold !== null ? (
            <>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-5xl font-bold tabular-nums">{pct(f.prob)}</span>
                <span className="text-sm text-muted-foreground">probabilidad estimada</span>
              </div>
              <div className="mt-4 h-2 w-full bg-muted" aria-hidden>
                <div
                  className="relative h-2"
                  style={{
                    width: `${f.prob * 100}%`,
                    background:
                      f.alertStatus === "ALERT" ? "var(--zone-exceso)" : "var(--zone-exito)",
                  }}
                />
                <div
                  className="relative -mt-3 h-4 w-0.5 bg-foreground"
                  style={{ marginLeft: `${f.threshold * 100}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Umbral aplicado: <b className="text-foreground">{pct(f.threshold)}</b>{" "}
                <span>· Estado: {f.availabilityLabel}</span>
              </p>
            </>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">
              {f.availabilityLabel}. {f.availabilityReason}
            </p>
          )}
          <p className="mt-3 flex gap-1.5 rounded-md bg-muted/60 p-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            Estima la probabilidad de que el mes objetivo supere el P75 histórico. No representa el
            número esperado de casos.
          </p>
        </div>
        <div
          className={`col-start-1 row-start-1 min-w-0 transition-opacity duration-150 motion-reduce:transition-none ${detail ? "visible opacity-100" : "invisible opacity-0"}`}
          aria-hidden={!detail}
          inert={!detail}
        >
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Modelo utilizado</dt>
              <dd className="font-semibold">{f.modelLabel ?? "No disponible"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Horizonte</dt>
              <dd className="font-mono text-xs">{f.horizon}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Versión del modelo</dt>
              <dd className="font-mono text-xs">{f.modelVersion ?? "No disponible"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Versión de los datos</dt>
              <dd className="font-mono text-xs">{f.dataVersion}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">
                Identificador del resultado generado
              </dt>
              <dd className="flex min-w-0 items-center gap-2">
                <span className="min-w-0 break-all font-mono text-xs">
                  {f.resultId ?? "No disponible"}
                </span>
                {f.resultId && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="min-h-11 min-w-11 shrink-0"
                    aria-label="Copiar identificador del resultado"
                    title="Copiar identificador del resultado"
                    onClick={copyIdentifier}
                  >
                    {copyMessage === "Identificador copiado" ? <Check /> : <Copy />}
                  </Button>
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>
      <Button
        variant="secondary"
        size="sm"
        className="mt-4 min-h-11 border border-border"
        aria-expanded={detail}
        onClick={() => {
          setDetail(!detail);
          setCopyMessage("");
        }}
      >
        {detail && <ArrowLeft />} {detail ? "Volver al resultado" : "Detalle del resultado"}
      </Button>
    </Card>
  );
}

function ChannelChart({ muni, view }: { muni: Muni; view: DashboardViewModel }) {
  const T = view.periodMonthIndex;
  const data = muni.channel.map((p) => ({
    ...p,
    b1: p.p25,
    b2: p.median !== null && p.p25 !== null ? p.median - p.p25 : null,
    b3: p.p75 !== null && p.median !== null ? p.p75 - p.median : null,
  }));
  return (
    <Card
      title={`Canal endémico — ${muni.name}`}
      aside={
        <ul className="flex flex-wrap gap-3 text-xs" aria-label="Leyenda">
          {(["Éxito", "Seguridad", "Alerta"] as Zone[]).map((z) => (
            <li key={z} className="flex items-center gap-1.5">
              <span className="h-3 w-3" style={{ background: ZONE_STYLE[z].var, opacity: 0.85 }} />
              {z}
            </li>
          ))}
          <li className="flex items-center gap-1.5">
            <span className="h-0.5 w-4" style={{ background: "var(--zone-exceso)" }} />
            Exceso (sobre P75)
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-foreground" />
            Casos observados
          </li>
        </ul>
      }
    >
      <div
        className="h-80"
        role="img"
        aria-label={`Canal endémico ${muni.name} ${view.periodYear}. Mes T ${MONTHS_FULL[T]}: ${muni.observedT ?? "sin dato"} casos, zona ${muni.zoneT}.`}
      >
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="month" stroke="var(--muted-foreground)" fontSize={12} />
            <YAxis stroke="var(--muted-foreground)" fontSize={12} />
            <ReferenceLine
              x={MONTHS[T]!}
              stroke="var(--primary)"
              strokeWidth={2}
              strokeDasharray="4 3"
              label={{
                value: "Mes T",
                fill: "var(--primary)",
                fontSize: 11,
                position: "insideTopRight",
                offset: 8,
              }}
            />
            <Area
              stackId="z"
              dataKey="b1"
              name="Éxito (<P25)"
              fill="var(--zone-exito)"
              fillOpacity={0.18}
              stroke="var(--zone-exito)"
              strokeOpacity={0.55}
              strokeWidth={1}
            />
            <Area
              stackId="z"
              dataKey="b2"
              name="Seguridad (P25–Mediana)"
              fill="var(--zone-seguridad)"
              fillOpacity={0.16}
              stroke="var(--zone-seguridad)"
              strokeOpacity={0.55}
              strokeWidth={1}
            />
            <Area
              stackId="z"
              dataKey="b3"
              name="Alerta (Mediana–P75)"
              fill="var(--zone-alerta)"
              fillOpacity={0.14}
              stroke="var(--zone-exceso)"
              strokeOpacity={1}
              strokeWidth={2}
            />
            <Line
              dataKey="observed"
              name="Casos observados"
              stroke="var(--foreground)"
              strokeWidth={2.5}
              dot={(props: { cx?: number; cy?: number; index?: number; value?: number | null }) =>
                props.value == null ? (
                  <g key={props.index} />
                ) : (
                  <circle
                    key={props.index}
                    cx={props.cx}
                    cy={props.cy}
                    r={props.index === T ? 6 : 3}
                    fill={props.index === T ? "var(--primary)" : "var(--foreground)"}
                  />
                )
              }
              connectNulls={false}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]!.payload as (typeof data)[number];
                return (
                  <div className="rounded-md border border-border bg-popover p-2 text-xs text-popover-foreground shadow">
                    <p className="font-semibold">
                      {MONTHS_FULL[p.idx]}
                      {p.idx === T ? " (Mes T)" : ""}
                    </p>
                    <p>Observados: {p.observed ?? "sin dato"}</p>
                    <p>
                      P25 {p.p25} · Mediana {p.median} · P75 {p.p75}
                    </p>
                  </div>
                );
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function TerritoryMap({
  dept,
  munis,
  selected,
  onSelect,
}: {
  dept: Dept;
  munis: Muni[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const [h, setH] = useState<"t1" | "t2">("t1");
  return (
    <Card
      title={`Representación territorial — ${DEPTS[dept]}`}
      className="min-w-0 lg:col-span-3"
      aside={
        <div
          role="group"
          aria-label="Horizonte del mapa"
          className="flex rounded-md border border-border p-0.5 text-xs"
        >
          {(["t1", "t2"] as const).map((k) => (
            <Button
              key={k}
              variant="ghost"
              size="sm"
              aria-pressed={h === k}
              onClick={() => setH(k)}
              className={`h-auto rounded px-3 py-1 font-semibold ${h === k ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}
            >
              {k === "t1" ? "T+1" : "T+2"}
            </Button>
          ))}
        </div>
      }
    >
      <MunicipalMap
        key={dept}
        dept={dept}
        munis={munis}
        selected={selected}
        horizon={h}
        onSelect={onSelect}
      />
      <div className="mt-3 w-full overflow-x-auto">
        <table className="w-full text-left text-xs">
          <caption className="sr-only">
            Tabla equivalente al mapa: estado observado y riesgo T+1/T+2 por municipio
          </caption>
          <thead className="text-muted-foreground">
            <tr className="border-b border-border">
              <th className="py-2 pr-2">Municipio</th>
              <th className="pr-2">Casos T</th>
              <th className="pr-2">Estado observado</th>
              <th className="pr-2">T+1</th>
              <th>T+2</th>
            </tr>
          </thead>
          <tbody>
            {munis.map((m) => (
              <tr
                key={m.id}
                className={`border-b border-border/60 ${m.id === selected ? "bg-accent/50" : ""}`}
              >
                <td className="py-2 pr-2">
                  <button className="font-medium hover:text-primary" onClick={() => onSelect(m.id)}>
                    {m.name}
                  </button>
                </td>
                <td className="pr-2 tabular-nums">{m.observedT ?? "No disponible"}</td>
                <td className="pr-2">
                  <ZoneBadge zone={m.zoneT} />
                </td>
                <td className="pr-2">
                  <span className="mr-1 tabular-nums">{pct(m.t1.prob)}</span>
                  <AlertBadge f={m.t1} />
                </td>
                <td>
                  <span className="mr-1 tabular-nums">{pct(m.t2.prob)}</span>
                  <AlertBadge f={m.t2} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function HorizonChart({ muni }: { muni: Muni }) {
  const data = [muni.t1, muni.t2].map((f) => ({
    name: `${f.horizon} · ${f.targetMonth.split(" ")[0]}`,
    prob: f.prob,
    th: f.threshold,
    f,
  }));
  return (
    <Card title="Comparación de horizontes" className="min-w-0 lg:col-span-2">
      <p className="mb-2 text-xs text-muted-foreground">
        {muni.name}: probabilidad estimada de superar P75 frente al umbral de cada horizonte (línea
        punteada).
      </p>
      <div className="h-56">
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(v) => `${v * 100}%`}
              stroke="var(--muted-foreground)"
              fontSize={11}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={90}
              stroke="var(--muted-foreground)"
              fontSize={11}
            />
            <Bar dataKey="prob" barSize={26} radius={4}>
              {data.map((d) => (
                <Cell
                  key={d.name}
                  fill={
                    !d.f.available
                      ? "var(--muted)"
                      : d.f.alertStatus === "ALERT"
                        ? "var(--zone-exceso)"
                        : "var(--zone-exito)"
                  }
                />
              ))}
            </Bar>
            {muni.t1.threshold !== null && (
              <ReferenceLine
                x={muni.t1.threshold}
                stroke="var(--foreground)"
                strokeDasharray="4 3"
                label={{
                  value: `Umbral T+1 ${pct(muni.t1.threshold)}`,
                  fill: "var(--muted-foreground)",
                  fontSize: 10,
                  position: "insideTopLeft",
                }}
              />
            )}
            {muni.t2.threshold !== null && muni.t2.threshold !== muni.t1.threshold && (
              <ReferenceLine
                x={muni.t2.threshold}
                stroke="var(--muted-foreground)"
                strokeDasharray="2 3"
                label={{
                  value: `Umbral T+2 ${pct(muni.t2.threshold)}`,
                  fill: "var(--muted-foreground)",
                  fontSize: 10,
                  position: "insideBottomLeft",
                }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 space-y-1 text-xs">
        {[muni.t1, muni.t2].map((f) => (
          <li key={f.horizon} className="flex items-center justify-between gap-2">
            <span>
              {f.horizon}: {pct(f.prob)} vs umbral {pct(f.threshold)}
            </span>
            <AlertBadge f={f} />
          </li>
        ))}
      </ul>
    </Card>
  );
}

function HistoryCard({ view }: { view: DashboardViewModel }) {
  const rows = view.history;
  const [open, setOpen] = useState(false);
  return (
    <Card title="Contexto histórico del modelo">
      <p className="mb-4 text-xs text-muted-foreground">
        {rows[0]
          ? `Evaluación ${rows[0].periodStart} a ${rows[0].periodEnd} · ${rows[0].geography}`
          : "No evaluado"}
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {rows.map((r) => (
          <div key={r.horizon} className="rounded-lg border border-border bg-background/50 p-4">
            <p className="mb-3 font-semibold">Horizonte {r.horizon}</p>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Falsas alertas / alertas emitidas</dt>
                <dd className="font-mono text-lg">
                  {r.falseAlerts ?? "No evaluado"} / {r.alerts ?? "No evaluado"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">% falsas alertas</dt>
                <dd className="font-mono text-lg">{pct(r.falseAlertRatio)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">
                  Inicios detectados / inicios reales
                </dt>
                <dd className="font-mono text-lg">
                  {r.detected ?? "No evaluado"} / {r.onsets ?? "No evaluado"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Sensibilidad de detección</dt>
                <dd className="font-mono text-lg">{pct(r.onsetSensitivity)}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
      <p className="mt-4 flex gap-1.5 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        Estos indicadores describen el comportamiento histórico del procedimiento. No determinan si
        la alerta actual será verdadera o falsa.
      </p>
      <div className="mt-4 rounded-lg border border-border">
        <button
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold"
        >
          Detalles técnicos{" "}
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </button>
        {open && (
          <table className="w-full border-t border-border text-left text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Horizonte</th>
                <th>AUROC</th>
                <th>AP</th>
                <th>Brier</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {rows.map((r) => (
                <tr key={r.horizon} className="border-t border-border/60">
                  <td className="px-4 py-2">{r.horizon}</td>
                  <td>{r.auroc?.toFixed(2) ?? "No evaluado"}</td>
                  <td>{r.ap?.toFixed(2) ?? "No evaluado"}</td>
                  <td>{r.brier?.toFixed(2) ?? "No evaluado"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}
