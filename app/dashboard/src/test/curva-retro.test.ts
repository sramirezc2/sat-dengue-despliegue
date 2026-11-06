import { describe, expect, it } from "vitest";

import { enVolumen } from "@/lib/curva-retro";
import type { PuntoCurva } from "@/lib/dashboard-view-model";

/**
 * La curva no puede extrapolar, y esta prueba existe porque ya extrapolo.
 *
 * Una version anterior leia la curva con una interpolacion que, fuera del
 * rango medido, devuelve el valor del extremo en silencio. El resultado fue
 * una tabla donde tres volumenes de alerta distintos imprimian el mismo
 * numero, presentado como tres mediciones. Lo encontro una auditoria
 * independiente, no la relectura del propio trabajo.
 *
 * La prueba fija el comportamiento correcto: dentro del rango interpola,
 * fuera del rango dice que no sabe.
 */

const serie = (puntos: Array<[number, number]>): PuntoCurva[] =>
  puntos.map(([alerts, detected]) => ({
    horizon: "T+1" as const,
    candidate: "endemic_channel_gated",
    alerts,
    detected,
  }));

describe("enVolumen", () => {
  const curva = serie([
    [800, 300],
    [1000, 360],
    [2400, 460],
  ]);

  it("interpola linealmente dentro del rango medido", () => {
    expect(enVolumen(curva, 900)).toBe(330);
    expect(enVolumen(curva, 800)).toBe(300);
    expect(enVolumen(curva, 2400)).toBe(460);
  });

  it("devuelve null por debajo del rango en vez de clavar el extremo", () => {
    expect(enVolumen(curva, 500)).toBeNull();
    expect(enVolumen(curva, 799)).toBeNull();
  });

  it("devuelve null por encima del techo de la regla", () => {
    // El canal condicionado no puede emitir mas alertas que filas deja pasar
    // su compuerta: preguntarle por un volumen mayor no tiene respuesta.
    expect(enVolumen(curva, 2401)).toBeNull();
    expect(enVolumen(curva, 4000)).toBeNull();
  });

  it("no inventa una respuesta con menos de dos puntos", () => {
    expect(enVolumen(serie([[1000, 360]]), 1000)).toBeNull();
    expect(enVolumen([], 1000)).toBeNull();
  });

  it("ordena la serie antes de leerla", () => {
    const desordenada = serie([
      [2400, 460],
      [800, 300],
      [1000, 360],
    ]);
    expect(enVolumen(desordenada, 900)).toBe(330);
  });
});
