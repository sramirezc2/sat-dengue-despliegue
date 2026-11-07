#!/usr/bin/env bash
# Pruebas basicas del despliegue. Es lo mismo que haria el jurado al abrir el
# enlace, en forma de comandos, para poder ensayarlo antes de la revision.
#
#   ./scripts/verificar_despliegue.sh http://localhost:8080
set -euo pipefail

BASE="${1:-http://localhost}"
fallos=0

comprobar () {
  local descripcion="$1" esperado="$2" ruta="$3"
  local codigo
  codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${BASE}${ruta}" || echo 000)
  if [[ "$codigo" == "$esperado" ]]; then
    printf '  OK    %-52s %s\n' "$descripcion" "$codigo"
  else
    printf '  FALLA %-52s %s (se esperaba %s)\n' "$descripcion" "$codigo" "$esperado"
    fallos=$((fallos + 1))
  fi
}

comprobar_resultados () {
  local salud="$1"
  if printf '%s' "$salud" | python3 -c '
import json
import sys

datos = json.load(sys.stdin)
periodos = datos.get("periodos_por_departamento", {})
if datos.get("resultados_cargados", 0) <= 0 or not periodos.get("50") or not periodos.get("73"):
    raise SystemExit(1)
'; then
    printf '  OK    %-52s %s\n' "resultados iniciales de Meta y Tolima" "disponibles"
  else
    printf '  FALLA %-52s %s\n' "resultados iniciales de Meta y Tolima" "ausentes"
    fallos=$((fallos + 1))
  fi
}

echo "Verificando ${BASE}"
comprobar "salud del servicio"                 200 "/api/salud"
comprobar "tablero"                            200 "/"
comprobar "Tolima, periodo publicado"          200 "/api/dashboard?department_code=73&period=2025-10"
comprobar "Meta, periodo publicado"            200 "/api/dashboard?department_code=50&period=2025-10"
comprobar "periodo sin resultado"              404 "/api/dashboard?department_code=73&period=2020-01"
comprobar "departamento no admitido"           400 "/api/dashboard?department_code=11&period=2026-09"
comprobar "periodo mal formado"                400 "/api/dashboard?department_code=73&period=septiembre"
comprobar "ruta inexistente"                   404 "/api/no-existe"
comprobar "descriptor del servicio"            200 "/"
comprobar "esquema OpenAPI"                    200 "/api/openapi.json"

echo
echo "Resultados cargados:"
salud=$(curl -s --max-time 15 "${BASE}/api/salud" || true)
comprobar_resultados "$salud"
printf '%s' "$salud" | python3 -m json.tool 2>/dev/null || echo "  no se pudo leer la salud"

echo
if [[ $fallos -eq 0 ]]; then
  echo "Todo en orden."
else
  echo "${fallos} comprobacion(es) fallaron."
  exit 1
fi
