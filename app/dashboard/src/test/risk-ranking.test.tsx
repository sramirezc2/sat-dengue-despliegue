import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RiskDashboard } from "@/components/risk-dashboard";
import { RISK_LEGEND, riskRankingSchema, riskViewSchema } from "@/lib/risk-contract";

const fixture = () =>
  JSON.parse(
    readFileSync(
      resolve(import.meta.dirname, "../../../../contracts/fixtures/risk-ranking.json"),
      "utf8",
    ),
  );
const view = (ranking = fixture()) => ({
  ranking,
  department_filter: null,
  visible_municipality_codes: ranking.municipalities.map(
    (r: { municipality_code: string }) => r.municipality_code,
  ),
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Contrato público de prioridades", () => {
  it.each([
    [1.0, true],
    ["1", false],
    [true, false],
    [1.5, false],
  ])("valida número JSON %s", (value, valid) => {
    const d = fixture();
    d.municipalities[0].risk_rank = value;
    expect(riskRankingSchema.safeParse(d).success).toBe(valid);
  });
  it("acepta el fixture compartido por JSON Schema y Pydantic", () => {
    expect(riskRankingSchema.safeParse(fixture()).success).toBe(true);
    expect(riskViewSchema.safeParse(view()).success).toBe(true);
  });
  it.each(["probability", "threshold", "y_true", "TP", "false_alerts"])("rechaza %s", (field) => {
    const d = fixture();
    d.municipalities[0][field] = 0;
    expect(riskRankingSchema.safeParse(d).success).toBe(false);
  });
  it.each(["calendar", "rank", "selection", "department", "version"])(
    "rechaza %s incompatible",
    (kind) => {
      const d = fixture();
      if (kind === "calendar") d.reference_period = "2025-12";
      if (kind === "rank") d.municipalities[0].risk_rank = 2;
      if (kind === "selection") d.municipalities[0].selected_for_attention = false;
      if (kind === "department") d.municipalities[0].department_code = "73";
      if (kind === "version") d.schema_version = "wrong";
      expect(riskRankingSchema.safeParse(d).success).toBe(false);
    },
  );
});

describe("Vista 2025", () => {
  it.skipIf(!process.env.SATD_RISK_E2E_RESPONSE)(
    "renderiza la respuesta E2E de las cinco fuentes",
    async () => {
      const payload = JSON.parse(readFileSync(process.env.SATD_RISK_E2E_RESPONSE!, "utf8"));
      const published = riskViewSchema.parse(payload).ranking;
      vi.stubGlobal(
        "fetch",
        vi.fn(
          async (url: string | URL) =>
            new Response(
              JSON.stringify(String(url).includes("/periodos") ? ["2025-01"] : payload),
              { status: 200 },
            ),
        ),
      );
      const { container } = render(
        <QueryClientProvider client={new QueryClient()}>
          <RiskDashboard />
        </QueryClientProvider>,
      );
      const list = await screen.findByRole("list", { name: "Municipios seleccionados" });
      expect(within(list).getAllByRole("listitem")).toHaveLength(8);
      const selected = published.municipalities.filter((r) => r.selected_for_attention);
      for (const row of selected) {
        expect(
          within(list).getByText(`${row.municipality_name} · ${row.department_name}`),
        ).toBeVisible();
      }
      expect(screen.getByRole("tab", { selected: true })).toHaveTextContent("T+2");
      expect(screen.getByText(RISK_LEGEND)).toBeVisible();
      expect(container.innerHTML).not.toMatch(
        /\b(probability|threshold|y_true|acierto|fallo|sensibilidad|FAR)\b|[0-9]+%/i,
      );
      expect(container.textContent).toContain(published.trace.artifact_sha256);
      fireEvent.change(screen.getByLabelText("Departamento"), { target: { value: "73" } });
      const filtered = selected.filter((r) => r.department_code === "73");
      expect(within(list).queryAllByRole("listitem")).toHaveLength(filtered.length);
      for (const row of filtered) {
        expect(within(list).getByText(`Posición global ${row.risk_rank}`)).toBeVisible();
      }
    },
  );
  it("abre T+2 con ocho prioridades y filtra sin reasignar cupos o posiciones", async () => {
    const requests: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL) => {
        requests.push(String(url));
        return new Response(
          JSON.stringify(String(url).includes("/periodos") ? ["2025-01"] : view()),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }),
    );
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { container } = render(
      <QueryClientProvider client={client}>
        <RiskDashboard />
      </QueryClientProvider>,
    );
    const list = await screen.findByRole("list", { name: "Municipios seleccionados" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(8);
    expect(screen.getByRole("tab", { name: "T+2 · principal" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText(RISK_LEGEND)).toBeVisible();
    expect(within(list).getByText("Posición global 1")).toBeVisible();
    fireEvent.change(screen.getByLabelText("Departamento"), { target: { value: "73" } });
    expect(within(list).queryAllByRole("listitem")).toHaveLength(0);
    expect(
      screen.getByText("Ningún municipio priorizado coincide con estos filtros."),
    ).toBeVisible();
    expect(within(screen.getByRole("table", { hidden: true })).getByText("30")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Departamento"), { target: { value: "" } });
    expect(within(list).getAllByRole("listitem")).toHaveLength(8);
    const firstName = fixture().municipalities[0].municipality_name;
    fireEvent.change(screen.getByLabelText("Buscar municipio"), { target: { value: firstName } });
    expect(within(list).getAllByRole("listitem")).toHaveLength(1);
    expect(within(list).getByText("Posición global 1")).toBeVisible();
    expect(requests).toHaveLength(2);
    expect(requests.every((p) => p.includes("/api/prioridades/v1"))).toBe(true);
    expect(requests[1]).toContain("horizon=T2");
    expect(container.innerHTML).not.toMatch(
      /\b(probability|threshold|y_true|acierto|fallo|sensibilidad|FAR)\b|[0-9]+%/i,
    );
    expect(container.textContent).toContain(fixture().trace.artifact_sha256);
  });
  it("rechaza un payload con desenlaces antes de renderizar municipios", async () => {
    const d = view();
    d.ranking.municipalities[0].y_true = 1;
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (url: string | URL) =>
          new Response(JSON.stringify(String(url).includes("/periodos") ? ["2025-01"] : d), {
            status: 200,
          }),
      ),
    );
    render(
      <QueryClientProvider client={new QueryClient()}>
        <RiskDashboard />
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo validar");
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
