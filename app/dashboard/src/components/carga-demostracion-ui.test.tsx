import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CargaDemostracion } from "./carga-demostracion";
import { loadDefaultPackage, rank } from "@/lib/demo-inference";
vi.mock("@/lib/demo-inference", () => ({
  parseFile: vi.fn(() => ({
    total: 2,
    confirmed: 2,
    rejected: 0,
    last: "2025-10",
    counts: new Map([["73001:2025-10", 1]]),
  })),
  loadDefaultPackage: vi.fn(),
  rank: vi.fn(() => [
    { code: "73001", name: "IBAGUÉ", probability: 0.6 },
    { code: "50001", name: "VILLAVICENCIO", probability: 0.4 },
  ]),
}));
const model = {} as Awaited<ReturnType<typeof loadDefaultPackage>>;
const loadModel = vi.mocked(loadDefaultPackage);

function uploadFile(name: string) {
  fireEvent.change(screen.getByLabelText("Archivo CSV o Excel"), {
    target: { files: [{ name, arrayBuffer: async () => new ArrayBuffer(0) }] },
  });
}

function openDemo() {
  render(<CargaDemostracion />);
  fireEvent.click(screen.getByRole("button", { name: "Carga de demostración" }));
  return screen.getByRole("button", { name: "Calcular ranking T+2" });
}

beforeEach(() => {
  vi.clearAllMocks();
  loadModel.mockReset().mockResolvedValue(model);
});

describe("interfaz de carga", () => {
  it("calcula con el modelo por defecto y limpia selección y resultados al cambiar el archivo", async () => {
    const calculate = openDemo();
    expect(calculate).toBeDisabled();
    expect(screen.queryByText("Cargar paquete sintético")).not.toBeInTheDocument();
    uploadFile("ejemplo.xlsx");
    await waitFor(() => expect(calculate).toBeEnabled());
    expect(screen.getByText(/Archivo validado/)).toHaveTextContent("ejemplo.xlsx");
    expect(loadModel).not.toHaveBeenCalled();
    fireEvent.click(calculate);
    const ranking = await screen.findByRole("region", { name: "Ranking municipal T+2" });
    expect(loadModel).toHaveBeenCalledTimes(1);
    expect(rank).toHaveBeenCalledWith(model, expect.objectContaining({ last: "2025-10" }));
    const city = within(ranking).getByRole("button", { name: /IBAGUÉ/ });
    fireEvent.click(city);
    expect(city).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: /^Meta$/ }));
    expect(within(ranking).getByRole("button", { name: /VILLAVICENCIO/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    uploadFile("otro.csv");
    expect(screen.queryByRole("region", { name: "Ranking municipal T+2" })).not.toBeInTheDocument();
    await waitFor(() => expect(calculate).toBeEnabled());
  });

  it("descarta el cálculo pendiente cuando el usuario cambia de archivo", async () => {
    let resolveModel!: (value: typeof model) => void;
    const pending = new Promise<typeof model>((resolve) => {
      resolveModel = resolve;
    });
    loadModel.mockReturnValueOnce(pending);
    const calculate = openDemo();
    uploadFile("primero.csv");
    await waitFor(() => expect(calculate).toBeEnabled());
    fireEvent.click(calculate);
    expect(screen.getByText(/Preparando el ranking/)).toBeInTheDocument();
    uploadFile("segundo.xlsx");
    await act(() => resolveModel(model));
    expect(rank).not.toHaveBeenCalled();
    expect(screen.queryByRole("region", { name: "Ranking municipal T+2" })).not.toBeInTheDocument();
    await waitFor(() => expect(calculate).toBeEnabled());
  });

  it("permite reintentar cuando el modelo no está disponible", async () => {
    loadModel.mockRejectedValueOnce(new Error("No se pudo cargar el modelo logístico T+2."));
    const calculate = openDemo();
    uploadFile("ejemplo.csv");
    await waitFor(() => expect(calculate).toBeEnabled());
    fireEvent.click(calculate);
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar el modelo");
    fireEvent.click(calculate);
    expect(
      await screen.findByRole("region", { name: "Ranking municipal T+2" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
