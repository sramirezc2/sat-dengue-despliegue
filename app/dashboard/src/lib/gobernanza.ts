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
): string {
  if (estado === "APPROVED" && champion === "SELECTED") {
    return (
      "El modelo superó la compuerta G5 y tiene champion seleccionado. " +
      "Los resultados publicados corresponden a ese modelo."
    );
  }
  return (
    "Los resultados provienen de un candidato provisional evaluado sobre el bloque " +
    "congelado de 2025. El champion no está seleccionado y estas alertas no están " +
    "autorizadas para decisiones operativas."
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
