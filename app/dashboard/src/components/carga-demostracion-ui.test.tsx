import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CargaDemostracion } from "./carga-demostracion";
vi.mock("@/lib/demo-inference", () => ({
  parseFile: vi.fn(() => ({
    total: 2,
    confirmed: 2,
    rejected: 0,
    last: "2025-10",
    counts: new Map([["73001:2025-10", 1]]),
  })),
  loadPackage: vi.fn(async () => ({})),
  rank: vi.fn(() => [
    { code: "73001", name: "IBAGUÉ", probability: 0.6 },
    { code: "50001", name: "VILLAVICENCIO", probability: 0.4 },
  ]),
}));
describe("interfaz de carga", () => {
  it("valida archivos, habilita cálculo y limpia selección y resultados", async () => {
    render(<CargaDemostracion />);
    fireEvent.click(screen.getByRole("button", { name: "Carga de demostración" }));
    const calculate = screen.getByRole("button", { name: "Calcular ranking T+2" });
    expect(calculate).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Archivo CSV o Excel"), {
      target: { files: [{ name: "ejemplo.xlsx", arrayBuffer: async () => new ArrayBuffer(0) }] },
    });
    fireEvent.change(screen.getByLabelText("Paquete sintético local"), {
      target: { files: [{ name: "package.json" }] },
    });
    await waitFor(() => expect(calculate).toBeEnabled());
    expect(screen.getByText(/Archivo validado/)).toHaveTextContent("ejemplo.xlsx");
    fireEvent.click(calculate);
    const ranking = screen.getByRole("region", { name: "Ranking municipal T+2" });
    const city = within(ranking).getByRole("button", { name: /IBAGUÉ/ });
    fireEvent.click(city);
    expect(city).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: /^Meta$/ }));
    expect(within(ranking).getByRole("button", { name: /VILLAVICENCIO/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    fireEvent.change(screen.getByLabelText("Archivo CSV o Excel"), {
      target: { files: [{ name: "otro.csv", arrayBuffer: async () => new ArrayBuffer(0) }] },
    });
    expect(screen.queryByRole("region", { name: "Ranking municipal T+2" })).not.toBeInTheDocument();
    await waitFor(() => expect(calculate).toBeEnabled());
  });
});
