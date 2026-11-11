#!/bin/bash
# Corre cada receta por separado (una falla no tumba a las demás) y junta sus predicciones.
# Uso: tools/noche/cola.sh <lote> <parametros.yml> <receta.yml> [...]   (desde pipeline/)
lote=$1; params=$2; shift 2
export PYTHONPATH=src PYTHONIOENCODING=utf-8
PY=/c/Users/nilara/wt-pr2/pipeline/.venv/Scripts/python.exe
mkdir -p data/noche/$lote; L=data/noche/$lote/cola.log
for r in "$@"; do
  n=$(basename $r .yml); echo "$(date +%H:%M:%S) inicio $n" >> $L
  $PY tools/noche/correr.py $params "configuraciones=[$r]" "salida=data/noche/$lote/_$n" >> $L 2>&1
  e=$?; echo "$(date +%H:%M:%S) fin $n exit $e" >> $L
  [ $e -eq 0 ] && cp data/noche/$lote/_$n/predicciones.csv data/noche/$lote/predicciones_$n.csv && cp data/noche/$lote/_$n/conjunto.csv data/noche/$lote/conjunto_$n.csv
done
echo "$(date +%H:%M:%S) FIN" >> $L
