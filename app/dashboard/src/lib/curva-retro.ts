import type { PuntoCurva } from "@/lib/dashboard-view-model";

/**
 * Inicios anticipados al volumen de alertas pedido, o `null` si cae fuera de
 * lo que esa regla alcanza a medir.
 *
 * Vive aparte del componente a proposito, y nunca extrapola, porque ya
 * extrapolo: una version anterior leia la curva con una interpolacion que
 * fuera del rango devuelve el valor del extremo en silencio, y la tabla
 * publicada termino imprimiendo el mismo punto bajo tres volumenes distintos
 * como si fueran tres mediciones. Lo encontro una revision independiente.
 *
 * Fuera del rango no hay medicion, y decirlo es parte de la respuesta: el
 * canal condicionado, por ejemplo, no puede emitir mas alertas que filas deja
 * pasar su compuerta, de modo que preguntarle por un volumen mayor no tiene
 * respuesta y no debe tener una inventada.
 */
export function enVolumen(pts: PuntoCurva[], alertas: number): number | null {
  if (pts.length < 2) return null;
  const o = [...pts].sort((a, b) => a.alerts - b.alerts);
  if (alertas < o[0]!.alerts || alertas > o[o.length - 1]!.alerts) return null;
  for (let i = 1; i < o.length; i += 1) {
    const a = o[i - 1]!;
    const b = o[i]!;
    if (alertas <= b.alerts) {
      const t = b.alerts === a.alerts ? 0 : (alertas - a.alerts) / (b.alerts - a.alerts);
      return Math.round(a.detected + t * (b.detected - a.detected));
    }
  }
  return null;
}
