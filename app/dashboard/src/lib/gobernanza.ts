/**
 * Texto de presentación del estado de gobernanza.
 *
 * La respuesta de la API trae un campo `limitation` que el contrato exige y
 * que queda como registro legible por máquina del resultado publicado. La copia
 * que lee una persona se escribe aquí, en el tablero, por dos razones: el texto
 * para humanos no pertenece al payload de un resultado, y así se puede corregir
 * la redacción sin regenerar los archivos publicados ni resincronizar el
 * almacenamiento de la instancia.
 */
import type { DashboardViewModel } from "./dashboard-view-model";

export interface EnlaceDeEvidencia {
  readonly rotulo: string;
  readonly href: string;
  readonly descripcion: string;
}

export function textoDeGobernanza(
  estado: DashboardViewModel["governanceStatus"],
  champion: DashboardViewModel["championStatus"],
  anio?: number,
): string {
  if (estado === "APPROVED" && champion === "SELECTED") {
    return "Los resultados corresponden al modelo autorizado para operar.";
  }
  const periodo = anio
    ? `sobre ${anio}, el último año con datos completos`
    : "sobre un periodo ya cerrado";
  return (
    `Resultados de un modelo en prueba ${periodo}. ` +
    "Ningún modelo fue autorizado para uso operativo."
  );
}

/**
 * Dónde está la evidencia detrás del estado que muestra el banner. Sin estos
 * enlaces el tablero declara que el modelo no está aprobado y no dice dónde
 * consta por qué, que fue una observación del evaluador del informe de avance.
 */
export function enlacesDeEvidencia(repositorio: string): readonly EnlaceDeEvidencia[] {
  const docs = `${repositorio}/blob/main/docs`;
  return [
    {
      rotulo: "Bitácora experimental",
      href: `${docs}/bitacora-experimental.md`,
      descripcion: "Registro de los experimentos, métricas y decisiones",
    },
    {
      rotulo: "Propuesta de política v2",
      href: `${docs}/politica-de-decision-v2.md`,
      descripcion: "Revisión propuesta de los criterios de la compuerta",
    },
  ];
}
