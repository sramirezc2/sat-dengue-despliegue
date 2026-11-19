import { useRef, useState } from "react";
import { Upload as UploadIcon, FlaskConical, ArrowRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  getInferenceStatus,
  MAX_BYTES,
  MODEL_UNAVAILABLE,
  parseFile,
  requestRanking,
  type InferenceStatus,
  type Ranking,
  type Upload,
} from "@/lib/demo-inference";
import boundaries from "@/lib/municipal-boundaries.json";

const normalizedName = (name: string) =>
  name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
const probability = (value: number | null | undefined) =>
  value == null ? "Sin predicción" : `${(value * 100).toFixed(1)} %`;
const retrospectiveLabel = "Demo retrospectiva con datos consolidados posteriores";
const missingReason = {
  missing_upload: "Municipio sin filas en la carga",
  missing_dengue: "Falta dato de dengue",
  missing_grave: "Falta dato de dengue grave",
  missing_climate: "Clima incompleto en el mes de referencia",
  missing_history: "Historia insuficiente",
  excess_at_origin: "Exceso observado en el mes de referencia",
};

export function CargaDemostracion() {
  const [open, setOpen] = useState(false);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [status, setStatus] = useState<InferenceStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [sample, setSample] = useState(false);
  const [search, setSearch] = useState("");
  const [zone, setZone] = useState("");
  const [selected, setSelected] = useState("");
  const [department, setDepartment] = useState<"tolima" | "meta">("tolima");
  const [dataName, setDataName] = useState("");
  const [dataError, setDataError] = useState("");
  const [error, setError] = useState("");
  const [dataBusy, setDataBusy] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const dataInput = useRef<HTMLInputElement>(null);
  const dataRequest = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  function clearResults() {
    setRanking(null);
    setSelected("");
    setError("");
  }
  async function checkAvailability() {
    setChecking(true);
    try {
      setStatus(await getInferenceStatus());
    } catch {
      setStatus(null);
    } finally {
      setChecking(false);
    }
  }
  async function fileLoad(file: File, isSample = false) {
    const request = ++dataRequest.current;
    inFlight.current?.abort();
    clearResults();
    setUpload(null);
    setDataName(file.name);
    setSample(isSample);
    setDataError("");
    setDataBusy(true);
    setCalculating(false);
    try {
      if (file.size > MAX_BYTES) throw Error("El archivo admite hasta 5 MB.");
      const data = parseFile(
        await file.arrayBuffer(),
        file.name,
        status ? new Set(status.municipalities) : undefined,
      );
      if (request === dataRequest.current) {
        setUpload(data);
        if (!data.period) setDataError("El archivo no contiene filas válidas para calcular T+2.");
        else if (data.rejected) setDataError("Corrige las filas rechazadas antes de calcular.");
      }
    } catch (e) {
      if (request === dataRequest.current)
        setDataError(e instanceof Error ? e.message : "Archivo inválido");
    } finally {
      if (request === dataRequest.current) setDataBusy(false);
    }
  }
  async function calculate() {
    if (!upload || !monthSupported || invalidCatalogue || upload.rejected || calculating) return;
    const request = dataRequest.current;
    const controller = new AbortController();
    inFlight.current = controller;
    clearResults();
    setCalculating(true);
    try {
      const result = await requestRanking(upload, sample, controller.signal);
      if (request === dataRequest.current) setRanking(result);
    } catch (e) {
      if (request === dataRequest.current)
        setError(e instanceof Error ? e.message : "No se pudo calcular el ranking.");
    } finally {
      if (request === dataRequest.current) setCalculating(false);
    }
  }
  const monthSupported = Boolean(upload?.period && status?.model?.periods.includes(upload.period));
  const invalidCatalogue = Boolean(
    status && upload?.rows.some((row) => !status.municipalities.includes(row.code)),
  );
  const visible = (ranking?.rows ?? []).filter((r) =>
    r.code.startsWith(department === "tolima" ? "73" : "50"),
  );
  const filtered = visible.filter(
    (r) => normalizedName(r.name).includes(normalizedName(search)) && (!zone || r.zone === zone),
  );
  const active = visible.find((r) => r.code === selected);
  return (
    <section className="border border-border bg-card" aria-label="Carga de demostración">
      <header className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div>
          <h2 className="rotulo">Demostración T+2</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Carga datos y explora la priorización municipal.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            if (!open && !checking) void checkAvailability();
            setOpen(!open);
          }}
          aria-expanded={open}
          aria-controls="demo-content"
        >
          Carga de demostración
          <ChevronDown aria-hidden className={`ml-2 h-4 w-4 ${open ? "rotate-180" : ""}`} />
        </Button>
      </header>
      {open && (
        <div id="demo-content" className="space-y-5 border-t border-border p-4 sm:p-5">
          <p className="text-sm text-muted-foreground">
            El navegador valida el archivo y envía conteos por municipio. El modelo usa el clima del
            mes de referencia y el historial del consolidado.
          </p>
          {checking && (
            <p role="status" className="text-sm">
              Comprobando el modelo T+2…
            </p>
          )}
          {!checking && !status?.model && (
            <div className="flex flex-wrap items-center gap-3">
              <p role="status" className="text-sm">
                {MODEL_UNAVAILABLE} Puedes revisar el archivo.
              </p>
              <Button variant="outline" onClick={() => void checkAvailability()}>
                Reintentar conexión
              </Button>
            </div>
          )}
          {!ranking && status?.model && <p className="text-sm font-medium">{retrospectiveLabel}</p>}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="min-w-0 space-y-2">
              <input
                hidden
                ref={dataInput}
                type="file"
                aria-label="Archivo CSV o Excel"
                accept=".csv,.xlsx"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  if (file) void fileLoad(file);
                }}
              />
              <Button variant="outline" onClick={() => dataInput.current?.click()}>
                <UploadIcon aria-hidden className="mr-2 h-4 w-4" />
                Cargar archivo
              </Button>
              <p className="break-all text-xs text-muted-foreground" role="status">
                {dataBusy ? "Validando archivo…" : upload ? "Archivo validado · " : ""}
                {dataName || "CSV o Excel (.xlsx)"}
              </p>
              {dataError && (
                <p role="alert" className="text-sm text-destructive">
                  {dataError}
                </p>
              )}
            </div>
            <div>
              <Button
                variant="ghost"
                onClick={() => {
                  const periods = status?.model?.periods ?? [];
                  const period = periods.includes("2025-10")
                    ? "2025-10"
                    : (periods.at(-1) ?? "2025-10");
                  void fileLoad(
                    new File(
                      [
                        `municipality_code,INI_SIN,confirmados,COD_EVE\n50001,${period}-01,1,210\n50001,${period}-02,0,220\n73001,${period}-01,1,210\n73001,${period}-02,0,220\n`,
                      ],
                      "muestra-dummy.csv",
                      { type: "text/csv" },
                    ),
                    true,
                  );
                }}
              >
                <FlaskConical aria-hidden className="mr-2 h-4 w-4" />
                Cargar muestra dummy
              </Button>
            </div>
          </div>
          {upload && (
            <dl
              className="grid grid-cols-2 gap-4 border border-border bg-muted/30 p-4 text-sm sm:grid-cols-5"
              aria-label="Resumen de carga"
            >
              {[
                ["Filas", upload.total],
                ["Confirmados", upload.confirmed],
                ["Filas con cero", upload.zeros],
                ["Rechazados", upload.rejected],
                ["Fuera de Meta y Tolima", upload.excluded],
                ["Municipios", upload.rows.length],
                ["Mes de referencia", upload.period || "—"],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-muted-foreground">{label}</dt>
                  <dd className="mt-1 font-mono text-lg font-semibold">{value}</dd>
                </div>
              ))}
            </dl>
          )}
          {upload && Object.keys(upload.reasons).length > 0 && (
            <ul className="list-disc pl-5 text-sm" aria-label="Motivos de rechazo">
              {Object.entries(upload.reasons).map(([reason, count]) => (
                <li key={reason}>
                  {reason}: {count}
                </li>
              ))}
            </ul>
          )}
          {upload?.period && status?.model && !monthSupported && (
            <div className="space-y-1 text-sm">
              <p role="alert" className="text-destructive">
                Mes fuera de cobertura.
              </p>
              <details>
                <summary className="cursor-pointer">Ver meses disponibles</summary>
                <p className="mt-1 text-muted-foreground">{status.model.periods.join(", ")}</p>
              </details>
            </div>
          )}
          {invalidCatalogue && (
            <p role="alert" className="text-sm text-destructive">
              La carga tiene códigos DIVIPOLA desconocidos.
            </p>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <Button
              disabled={
                !monthSupported ||
                invalidCatalogue ||
                !!upload?.rejected ||
                dataBusy ||
                calculating ||
                checking
              }
              onClick={() => void calculate()}
            >
              Calcular ranking T+2
              <ArrowRight aria-hidden className="ml-2 h-4 w-4" />
            </Button>
            {calculating && (
              <span role="status" className="text-xs text-muted-foreground">
                Preparando el ranking con el modelo logístico T+2…
              </span>
            )}
          </div>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          {ranking && (
            <div className="space-y-4 border-t border-border pt-5">
              <p className="text-sm font-medium">{retrospectiveLabel}</p>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex gap-2" aria-label="Departamento de demostración">
                  {(["tolima", "meta"] as const).map((d) => (
                    <Button
                      key={d}
                      variant={department === d ? "default" : "outline"}
                      aria-pressed={department === d}
                      onClick={() => {
                        setDepartment(d);
                        setSelected("");
                      }}
                    >
                      {d === "tolima" ? "Tolima" : "Meta"}
                    </Button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Referencia {ranking.reference_period} · Objetivo {ranking.target_period} · Modelo{" "}
                  {ranking.experiment_id}
                  {ranking.sample && " · Entrada de muestra artificial"}
                </p>
              </div>
              <div className="grid items-start gap-5 lg:grid-cols-2">
                <section
                  className="min-w-0 border border-border bg-card"
                  aria-label="Ranking municipal T+2"
                >
                  <header className="flex items-center justify-between border-b border-border px-5 py-3">
                    <h3 className="rotulo">Ranking municipal</h3>
                    <span className="text-xs text-muted-foreground">
                      {visible.length} municipios
                    </span>
                  </header>
                  <div className="flex flex-wrap gap-2 border-b border-border bg-muted/50 p-3">
                    <input
                      type="search"
                      aria-label="Buscar municipio"
                      placeholder="Buscar municipio…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="min-w-0 flex-1 border border-border bg-input px-2 py-1.5 text-sm"
                    />
                    <select
                      aria-label="Filtrar por zona"
                      value={zone}
                      onChange={(e) => setZone(e.target.value)}
                      className="border border-border bg-input px-2 py-1.5 text-sm"
                    >
                      <option value="">Todas las zonas</option>
                      {["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"].map((z) => (
                        <option key={z} value={z}>
                          {z}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="max-h-[28rem] overflow-auto">
                    <table className="w-full min-w-[35rem] text-left text-sm">
                      <thead className="sticky top-0 z-10 bg-muted text-xs text-muted-foreground">
                        <tr>
                          <th scope="col" className="px-3 py-3">
                            #
                          </th>
                          <th scope="col" className="px-3 py-3">
                            Municipio
                          </th>
                          <th scope="col" className="px-3 py-3">
                            Casos en T
                          </th>
                          <th scope="col" className="px-3 py-3">
                            Zona en T
                          </th>
                          <th scope="col" className="px-3 py-3">
                            P75 de T+2
                          </th>
                          <th scope="col" className="px-3 py-3 text-right">
                            Probabilidad T+2
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((r, i) => (
                          <tr
                            key={r.code}
                            className={`border-t border-border hover:bg-muted/50 ${selected === r.code ? "bg-primary/10" : ""}`}
                            onClick={() => setSelected(r.code)}
                          >
                            <td className="px-3 py-3 font-mono text-muted-foreground">
                              {r.probability == null ? "—" : i + 1}
                            </td>
                            <td className="px-3 py-3">
                              <button
                                className="text-left font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                                aria-pressed={selected === r.code}
                                onClick={() => setSelected(r.code)}
                              >
                                {r.name}
                                <span className="block font-mono text-xs text-muted-foreground">
                                  {r.code}
                                </span>
                              </button>
                            </td>
                            <td className="px-3 py-3">{r.cases ?? "No disponible"}</td>
                            <td className="px-3 py-3">{r.zone ?? "No disponible"}</td>
                            <td className="px-3 py-3">
                              {r.p75t2 == null
                                ? "No disponible"
                                : r.p75t2.toLocaleString("es-CO", { maximumFractionDigits: 2 })}
                            </td>
                            <td className="px-3 py-3 text-right font-mono">
                              {probability(r.probability)}
                              {r.reason && (
                                <span className="block text-xs text-muted-foreground">
                                  {missingReason[r.reason]}
                                </span>
                              )}
                              {r.probability != null && (
                                <span className="mt-1 block h-1.5 w-20 bg-muted" aria-hidden>
                                  <span
                                    className="block h-full bg-primary"
                                    style={{ width: `${r.probability * 100}%` }}
                                  />
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="border-t border-border p-3 text-xs text-muted-foreground">
                    P75 de T+2: percentil histórico en casos. Probabilidad T+2: estimación de inicio
                    de exceso.
                  </p>
                </section>
                <section
                  className="min-w-0 border border-border bg-card"
                  aria-label="Mapa de priorización T+2"
                >
                  <header className="border-b border-border px-5 py-3">
                    <h3 className="rotulo">Distribución municipal</h3>
                  </header>
                  <div className="space-y-4 p-4">
                    <svg
                      viewBox="0 0 1000 400"
                      className="h-64 w-full bg-muted/30 sm:h-80"
                      aria-label={`Mapa T+2 ${department}`}
                    >
                      {boundaries[department].map((area) => {
                        const item = visible.find(
                          (r) => normalizedName(r.name) === normalizedName(area.name),
                        );
                        return (
                          <path
                            key={area.id}
                            d={area.path}
                            fillRule="evenodd"
                            className="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                            style={{
                              fill:
                                item?.probability == null
                                  ? "var(--muted)"
                                  : `color-mix(in srgb, var(--primary) ${20 + item.probability * 80}%, var(--background))`,
                            }}
                            stroke={
                              selected === item?.code ? "var(--foreground)" : "var(--background)"
                            }
                            strokeWidth={selected === item?.code ? 3 : 1}
                            role={item ? "button" : "img"}
                            aria-label={`${area.name}: ${probability(item?.probability)}`}
                            aria-pressed={item ? selected === item.code : undefined}
                            tabIndex={item ? 0 : -1}
                            onKeyDown={(e) => {
                              if (item && (e.key === "Enter" || e.key === " ")) {
                                e.preventDefault();
                                setSelected(item.code);
                              }
                            }}
                            onClick={() => item && setSelected(item.code)}
                          >
                            <title>
                              {area.name}: {probability(item?.probability)}
                            </title>
                          </path>
                        );
                      })}
                    </svg>
                    <div
                      className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground"
                      aria-label="Leyenda de probabilidad"
                    >
                      <span>0 %</span>
                      <span
                        className="h-2 w-24 bg-gradient-to-r from-primary/20 to-primary"
                        aria-hidden
                      />
                      <span>100 %</span>
                      <span className="inline-flex items-center gap-1">
                        <i className="h-3 w-3 border border-border bg-muted" aria-hidden />
                        Sin predicción
                      </span>
                    </div>
                    <p className="min-h-10 border-t border-border pt-3 text-sm" role="status">
                      {active
                        ? `${active.name} · ${probability(active.probability)}`
                        : "Selecciona un municipio en la tabla o el mapa."}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Límites municipales · geoBoundaries / DANE (2020), CC BY 4.0. La intensidad
                      representa probabilidad, no una alerta.
                    </p>
                  </div>
                </section>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
