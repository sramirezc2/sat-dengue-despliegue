import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Dashboard } from "@/routes/index";
import { buildDashboardUrl, fetchDashboard } from "@/lib/dashboard-client";
import { dashboardResponseSchema, type DashboardResponse } from "@/lib/dashboard-contract";
import { adaptDashboardResponse, DEFAULT_PERIODS } from "@/lib/dashboard-view-model";
import { parseApiBaseUrl } from "@/lib/dashboard-config";

const repoRoot = resolve(import.meta.dirname, "../../../..");

// Dos fuentes distintas y a proposito.
//
// `fixture` son respuestas de prueba que ejercitan todos los estados del
// contrato, incluidos los que una corrida real no suele traer (sin historia,
// no elegible, dato faltante) y mas de una familia de modelo. Viven aqui para
// que las pruebas de contenido no dependan de que corrida este publicada.
//
// `resultadoPublicado` es lo que el despliegue sirve de verdad. Sobre eso se
// verifica forma y alcance, nunca valores concretos.
const fixture = (name: "tolima" | "meta"): unknown =>
  JSON.parse(readFileSync(resolve(import.meta.dirname, `fixtures/respuesta_${name}.json`), "utf8"));

const resultadosPublicados = (): string[] =>
  readdirSync(resolve(repoRoot, "datos/resultados")).filter((f) => f.endsWith(".json"));

const resultadoPublicado = (archivo: string): unknown =>
  JSON.parse(readFileSync(resolve(repoRoot, `datos/resultados/${archivo}`), "utf8"));
const response = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

afterEach(() => vi.unstubAllGlobals());

describe("Stage 7 dashboard contract and adapter", () => {
  it("accepts both real contract fixtures and exposes all 76 municipalities", () => {
    const tolima = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("tolima")));
    const meta = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("meta")));

    expect(tolima.municipalities).toHaveLength(47);
    expect(meta.municipalities).toHaveLength(29);
    expect(
      new Set([...tolima.municipalities, ...meta.municipalities].map((item) => item.geometryId))
        .size,
    ).toBe(76);
  });

  it("todos los resultados publicados cumplen el contrato", () => {
    const archivos = resultadosPublicados();
    expect(archivos.length).toBeGreaterThan(0);
    for (const archivo of archivos) {
      const parsed = dashboardResponseSchema.safeParse(resultadoPublicado(archivo));
      expect(parsed.success, `${archivo} no cumple el contrato`).toBe(true);
    }
  });

  it("rejects an incompatible response", () => {
    const invalid = structuredClone(fixture("tolima")) as Record<string, unknown>;
    delete invalid["governance"];
    expect(dashboardResponseSchema.safeParse(invalid).success).toBe(false);
  });

  it("passes API alerts, absences, endemic series, and individual result IDs through unchanged", () => {
    const parsed = dashboardResponseSchema.parse(fixture("tolima"));
    const view = adaptDashboardResponse(parsed);
    const ibague = view.municipalities.find(({ id }) => id === "73001")!;
    const unavailable = view.municipalities.find(
      ({ t1 }) => t1.availabilityStatus === "MISSING_DATA",
    )!;

    expect(ibague.t1.alertStatus).toBe(parsed.municipalities[0]!.results[0]!.alert_status);
    expect(ibague.t1.resultId).toBe(parsed.municipalities[0]!.results[0]!.result_id);
    expect(ibague.channel.map(({ observed }) => observed)).toEqual(
      parsed.municipalities[0]!.endemic_channel_series.map(({ cases }) => cases),
    );
    expect(unavailable.t1.prob).toBeNull();
    expect(unavailable.t1.threshold).toBeNull();
    expect(unavailable.t1.resultId).toBeNull();

    const adapterOnly = structuredClone(parsed) as DashboardResponse;
    adapterOnly.municipalities[0]!.results[0]!.alert_status = "NO_ALERT";
    expect(adaptDashboardResponse(adapterOnly).municipalities[0]!.t1.alertStatus).toBe("NO_ALERT");
  });

  it("represents all five availability states", () => {
    const views = ["tolima", "meta"].map((name) =>
      adaptDashboardResponse(dashboardResponseSchema.parse(fixture(name as "tolima" | "meta"))),
    );
    const states = new Set(
      views.flatMap(({ municipalities }) =>
        municipalities.flatMap(({ t1, t2 }) => [t1.availabilityStatus, t2.availabilityStatus]),
      ),
    );
    expect(states).toEqual(
      new Set([
        "AVAILABLE",
        "INELIGIBLE",
        "INSUFFICIENT_HISTORY",
        "MISSING_DATA",
        "NOT_CALCULATED",
      ]),
    );
    const labels = new Map(
      views.flatMap(({ municipalities }) =>
        municipalities
          .flatMap(({ t1, t2 }) => [t1, t2])
          .map((result) => [result.availabilityStatus, result.availabilityLabel]),
      ),
    );
    expect(labels).toEqual(
      new Map([
        ["AVAILABLE", "Disponible"],
        ["INELIGIBLE", "No elegible"],
        ["INSUFFICIENT_HISTORY", "Historia insuficiente"],
        ["MISSING_DATA", "Datos faltantes"],
        ["NOT_CALCULATED", "No calculado"],
      ]),
    );
  });

  it("formats known model names without replacing the contracted family", () => {
    const view = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("tolima")));
    expect(view.municipalities[0]!.t1).toMatchObject({ model: "xgboost", modelLabel: "XGBoost" });
    expect(view.municipalities[0]!.t2).toMatchObject({ model: "lightgbm", modelLabel: "LightGBM" });
  });

  it("does not convert an unavailable probability to zero", () => {
    const view = adaptDashboardResponse(dashboardResponseSchema.parse(fixture("tolima")));
    const unavailable = view.municipalities.find(({ t1 }) => !t1.available)!;
    expect(unavailable.t1.prob).toBeNull();
  });
});

describe("typed dashboard client", () => {
  it("accepts same-origin configuration and rejects unsafe base URLs", () => {
    expect(parseApiBaseUrl("")).toBe("");
    expect(parseApiBaseUrl("https://api.example.test/")).toBe("https://api.example.test");
    expect(() => parseApiBaseUrl("javascript:alert(1)")).toThrow(/HTTP y HTTPS/);
    expect(() => parseApiBaseUrl("https://user:secret@api.example.test")).toThrow(/credenciales/);
  });

  it("builds and encodes the exact endpoint query", () => {
    expect(
      buildDashboardUrl({ apiBaseUrl: "https://api.example.test/base" }, "73 &", "2026-09"),
    ).toBe("https://api.example.test/api/dashboard?department_code=73+%26&period=2026-09");
  });

  it.each([
    [400, "INVALID_PERIOD_FORMAT"],
    [404, "DASHBOARD_DATA_NOT_FOUND"],
    [500, "INTERNAL_ERROR"],
  ])("classifies contracted HTTP %i responses", async (status, errorCode) => {
    await expect(
      fetchDashboard("73", "bad", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () =>
          response({ error_code: errorCode, message: "contracted" }, status),
        ),
      }),
    ).rejects.toMatchObject({ kind: "http", status, errorCode });
  });

  it("distinguishes network and contract failures", async () => {
    await expect(
      fetchDashboard("73", "2026-09", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () => {
          throw new TypeError("offline");
        }),
      }),
    ).rejects.toMatchObject({ kind: "network" });
    await expect(
      fetchDashboard("73", "2026-09", undefined, {
        config: { apiBaseUrl: "" },
        fetcher: vi.fn(async () => response({ unexpected: true })),
      }),
    ).rejects.toMatchObject({ kind: "contract" });
  });
});

describe("dashboard query integration", () => {
  function renderDashboard() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <QueryClientProvider client={client}>
        <Dashboard />
      </QueryClientProvider>,
    );
  }

  it("loads Tolima, switches municipality coherently, then loads Meta", async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) =>
      response(String(input).includes("department_code=50") ? fixture("meta") : fixture("tolima")),
    );
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();

    expect(await screen.findByRole("region", { name: /Detalle de Ibagué/ })).toBeInTheDocument();
    const municipalitySelector = screen.getByLabelText("Municipio") as HTMLSelectElement;
    expect(municipalitySelector.options).toHaveLength(47);
    expect(screen.getAllByText("Disponible", { exact: false }).length).toBeGreaterThan(0);
    // La politica del proyecto exige que el tablero declare que el modelo no
    // esta autorizado. Lo que se verifica es esa declaracion, no la redaccion:
    // el codigo tecnico G5 salio de la vista por ilegible, pero la garantia
    // sigue siendo que un visitante no pueda confundir esto con alertas reales.
    const gobernanza = screen.getByRole("region", { name: "Estado de gobernanza del modelo" });
    expect(gobernanza).toHaveTextContent(/Ejercicio de evaluación/i);
    expect(gobernanza).toHaveTextContent(/Ningún modelo fue autorizado para uso operativo/i);
    expect(screen.getByRole("img", { name: /Canal endémico Ibagué/ })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: /Tabla equivalente al mapa/ })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Municipio"), { target: { value: "73024" } });
    expect(await screen.findByRole("region", { name: /Detalle de Alpujarra/ })).toBeInTheDocument();
    expect(screen.getAllByText("Historia insuficiente", { exact: false }).length).toBeGreaterThan(
      0,
    );
    fireEvent.change(screen.getByLabelText("Municipio"), { target: { value: "73026" } });
    expect(screen.getAllByText("No elegible", { exact: false }).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Municipio"), { target: { value: "73349" } });
    expect(screen.getAllByText("Datos faltantes", { exact: false }).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Municipio"), { target: { value: "73030" } });
    expect(screen.getAllByText("No calculado", { exact: false }).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("tab", { name: "Meta" }));
    expect(
      await screen.findByRole("region", { name: /Detalle de Villavicencio/ }),
    ).toBeInTheDocument();
    expect((screen.getByLabelText("Municipio") as HTMLSelectElement).options).toHaveLength(29);
    fireEvent.click(screen.getByRole("button", { name: "T+2" }));
    expect(screen.getByLabelText("Mapa municipal de Meta, T+2")).toBeInTheDocument();
  });

  it("keeps the result reverse limited to the five authorized fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response(fixture("tolima"))),
    );
    renderDashboard();

    expect(await screen.findByRole("region", { name: /Detalle de Ibagué/ })).toBeInTheDocument();
    const detailButton = screen.getAllByRole("button", { name: "Detalle del resultado" })[0]!;
    fireEvent.click(detailButton);
    const card = detailButton.closest("section")!;
    expect(within(card).getByText("XGBoost")).toBeInTheDocument();
    expect(within(card).getByText("Versión del modelo")).toBeInTheDocument();
    expect(within(card).getByText("Versión de los datos")).toBeInTheDocument();
    expect(within(card).getByText("Identificador del resultado generado")).toBeInTheDocument();
    expect(within(card).queryByText("Rol del modelo")).not.toBeInTheDocument();
  });

  it.each([
    [400, "INVALID_PERIOD_FORMAT", "Parámetros inválidos"],
    [404, "DASHBOARD_DATA_NOT_FOUND", "No hay resultados para este departamento y periodo"],
    [500, "INTERNAL_ERROR", "Error interno del API"],
  ])("renders the %i API state without prior results", async (status, errorCode, title) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response({ error_code: errorCode, message: "Falla controlada" }, status)),
    );
    renderDashboard();
    expect(await screen.findByText(title)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /Detalle de Ibagué/ })).not.toBeInTheDocument();
  });

  it.each([
    [
      "network",
      vi.fn(async () => {
        throw new TypeError("offline");
      }),
      "Error de red",
    ],
    ["contract", vi.fn(async () => response({ unexpected: true })), "Respuesta incompatible"],
  ])("renders a %s failure explicitly", async (_kind, fetcher, title) => {
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();
    expect(await screen.findByText(title)).toBeInTheDocument();
  });

  it("hides prior data on error and retries manually", async () => {
    // El tablero pide tambien /api/salud para poblar el selector de periodos,
    // asi que el doble de fetch responde por ruta y no por orden de llamada.
    let intentosDashboard = 0;
    const fetcher = vi.fn<typeof fetch>(async (input) => {
      const url = String(input);
      if (url.includes("/api/salud")) {
        return response({
          periodos_por_departamento: {
            "73": [DEFAULT_PERIODS.tolima],
            "50": [DEFAULT_PERIODS.meta],
          },
        });
      }
      intentosDashboard += 1;
      return intentosDashboard === 1
        ? response({ error_code: "INTERNAL_ERROR", message: "Falla controlada" }, 500)
        : response(fixture("tolima"));
    });
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();

    expect(await screen.findByText("Error interno del API")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /Detalle de Ibagué/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Reintentar/i }));
    await waitFor(() =>
      expect(screen.getByRole("region", { name: /Detalle de Ibagué/ })).toBeInTheDocument(),
    );
    expect(intentosDashboard).toBe(2);
  });

  it("conserva los controles de departamento y mes cuando no hay resultados", async () => {
    // Antes la tarjeta de error reemplazaba la pantalla entera y dejaba al
    // usuario sin forma de elegir otro departamento o periodo.
    const fetcher = vi.fn<typeof fetch>(async (input) =>
      String(input).includes("/api/salud")
        ? response({
            periodos_por_departamento: {
              "73": [DEFAULT_PERIODS.tolima],
              "50": [DEFAULT_PERIODS.meta],
            },
          })
        : response({ error_code: "DASHBOARD_DATA_NOT_FOUND", message: "Sin resultados." }, 404),
    );
    vi.stubGlobal("fetch", fetcher);
    renderDashboard();

    await screen.findByText("No hay resultados para este departamento y periodo");
    expect(screen.getByRole("tab", { name: "Tolima" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Meta" })).toBeInTheDocument();
    expect(screen.getByLabelText("Periodo de referencia")).toBeInTheDocument();
  });

  it("publica el retroanálisis separado de la corrida congelada, con su procedencia", async () => {
    // Las dos evaluaciones miden cosas distintas -doce meses contra siete
    // años- y juntarlas sugeriría que sus cifras son comparables. La prueba
    // fija que viven en regiones separadas y que la procedencia se dice en
    // pantalla en vez de quedar implícita.
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) =>
        response(
          String(input).includes("department_code=50") ? fixture("meta") : fixture("tolima"),
        ),
      ),
    );
    renderDashboard();
    await screen.findByRole("region", { name: /Detalle de Ibagué/ });

    fireEvent.click(screen.getByRole("tab", { name: /Qué tan bien acierta/ }));

    const retro = await screen.findByRole("region", { name: /Retroanálisis/ });
    const congelada = screen.getByRole("region", { name: /Comparación del modelo/ });
    expect(retro).not.toContainElement(congelada);

    expect(within(retro).getByText(/647 brotes que empezaron/)).toBeInTheDocument();
    expect(within(retro).getAllByText(/467 de 647/).length).toBeGreaterThan(0);
    expect(within(retro).getAllByText(/181 de 647/).length).toBeGreaterThan(0);
    expect(within(retro).getByText(/no la tubería científica/)).toBeInTheDocument();
    // El bloque congelado de 2025 no entra en esta evaluación.
    expect(within(retro).getByText(/termina en 2024/)).toBeInTheDocument();
  });

  it("omite el retroanálisis cuando el resultado no lo trae", async () => {
    // Los resultados publicados antes de noviembre de 2026 no lo traen y el
    // tablero tiene que seguir leyéndolos.
    const sinRetro = (nombre: "tolima" | "meta") => {
      const d = structuredClone(fixture(nombre)) as DashboardResponse;
      delete (d.evaluation_context as { development_backtest?: unknown }).development_backtest;
      return d;
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) =>
        response(
          String(input).includes("department_code=50") ? sinRetro("meta") : sinRetro("tolima"),
        ),
      ),
    );
    renderDashboard();
    await screen.findByRole("region", { name: /Detalle de Ibagué/ });

    fireEvent.click(screen.getByRole("tab", { name: /Qué tan bien acierta/ }));

    await screen.findByRole("region", { name: /Comparación del modelo/ });
    expect(screen.queryByRole("region", { name: /Retroanálisis/ })).not.toBeInTheDocument();
  });
});
