import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CargaDemostracion } from "./carga-demostracion";
import {
  getInferenceStatus,
  requestRanking,
  type InferenceStatus,
  type Ranking,
} from "@/lib/demo-inference";

vi.mock("@/lib/demo-inference", async (original) => ({
  ...(await original<typeof import("@/lib/demo-inference")>()),
  getInferenceStatus: vi.fn(),
  requestRanking: vi.fn(),
}));

const status: InferenceStatus = {
  municipalities: ["73001", "50001"],
  model: {
    experiment_id: "EXP314",
    version: "v1",
    periods: ["2025-09", "2025-10"],
    history_mode: "retrospective",
  },
};
const result: Ranking = {
  experiment_id: "EXP314",
  model_version: "v1",
  reference_period: "2025-10",
  target_period: "2025-12",
  history_mode: "retrospective",
  sample: false,
  rows: [
    {
      code: "73001",
      name: "IBAGUÉ",
      probability: 0.6,
      cases: 0,
      zone: "EXITO",
      p75t2: 5,
      reason: null,
    },
    {
      code: "50001",
      name: "VILLAVICENCIO",
      probability: null,
      cases: 1,
      zone: null,
      p75t2: null,
      reason: "missing_climate",
    },
  ],
};
const load = vi.mocked(getInferenceStatus);
const predict = vi.mocked(requestRanking);

function uploadFile(name = "ejemplo.csv", month = "2025-10") {
  const input = new TextEncoder().encode(
    `municipality_code,INI_SIN,confirmados\n73001,${month}-01,0\n50001,${month}-02,1\n`,
  );
  fireEvent.change(screen.getByLabelText("Archivo CSV o Excel"), {
    target: { files: [{ name, size: input.byteLength, arrayBuffer: async () => input.buffer }] },
  });
}

function openDemo() {
  render(<CargaDemostracion />);
  fireEvent.click(screen.getByRole("button", { name: "Carga de demostración" }));
  return screen.getByRole("button", { name: "Calcular ranking T+2" });
}

beforeEach(() => {
  load.mockReset().mockResolvedValue(status);
  predict.mockReset().mockResolvedValue(result);
});

describe("interfaz de inferencia", () => {
  it("sigue revisando el archivo y permite reconectar si falta el modelo", async () => {
    load.mockRejectedValueOnce(Error("offline"));
    const calculate = openDemo();
    uploadFile();
    await screen.findByText(/Archivo validado/);
    expect(calculate).toBeDisabled();
    fireEvent.click(await screen.findByRole("button", { name: "Reintentar conexión" }));
    await waitFor(() => expect(calculate).toBeEnabled());
  });

  it("muestra el modelo, la etiqueta retrospectiva y las ausencias de clima en el ranking", async () => {
    const calculate = openDemo();
    uploadFile();
    await waitFor(() => expect(calculate).toBeEnabled());
    fireEvent.click(calculate);
    const ranking = await screen.findByRole("region", { name: "Ranking municipal T+2" });
    expect(screen.getByText(/Objetivo 2025-12 · Modelo EXP314/)).toBeVisible();
    expect(screen.getByText("Demo retrospectiva con datos consolidados posteriores")).toBeVisible();
    const city = within(ranking).getByRole("button", { name: /IBAGUÉ/ });
    fireEvent.click(city);
    expect(city).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Meta", exact: true }));
    expect(within(ranking).getByText("Clima incompleto en el mes de referencia")).toBeVisible();
    expect(screen.getByLabelText("Mapa T+2 meta")).toBeVisible();
  });

  it("descarta resultados antiguos y bloquea meses fuera de cobertura", async () => {
    let resolveResult!: (value: Ranking) => void;
    predict.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveResult = resolve;
      }),
    );
    const calculate = openDemo();
    uploadFile();
    await waitFor(() => expect(calculate).toBeEnabled());
    fireEvent.click(calculate);
    uploadFile("otro.csv", "2026-01");
    await act(() => resolveResult(result));
    expect(await screen.findByText(/Mes fuera de cobertura/)).toBeVisible();
    expect(screen.queryByRole("region", { name: "Ranking municipal T+2" })).not.toBeInTheDocument();
    expect(calculate).toBeDisabled();
  });
});
