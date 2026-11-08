# EXP002 — conclusiones de aceptación técnica

Resultado científico: `NOT_APPLICABLE`. Tipo: `synthetic_fixture`.
Ejecución `b27dd78427ca486984c67b2b9b64d97f`: `COMPLETED`.
Evidencia: [docs/evidence/experiments/EXP002/b27dd78427ca486984c67b2b9b64d97f/inventory.json](../../evidence/experiments/EXP002/b27dd78427ca486984c67b2b9b64d97f/inventory.json).
Métricas y decisiones completas en [metrics.json](../../evidence/experiments/EXP002/b27dd78427ca486984c67b2b9b64d97f/metrics.json).

## Hipótesis

EXP002-H0: la fábrica puede ejecutar esta receta aprobada sin sobrescribir otra
identidad experimental, reutilizando los controles y el cálculo de V3.

## Resultado

Aceptación técnica satisfactoria: fuente artificial→canónico certificado por contenido→
cinco roles→modelo→calibración/umbral→evaluación, con evidencia exclusiva verificable.
El resultado es NOT_APPLICABLE a hipótesis científicas de dengue.

## Métricas principales

- T+2: AP=0.095238; Brier=0.086187; sensibilidad=1.000000; FAR=0.904762.

Son agregados de dos municipios ficticios. No constituyen rendimiento científico
ni justifican operación; el FAR sintético máximo 1.0 estaba predeclarado.

## Comparación

El AP del candidato coincide con la referencia de prevalencia de entrenamiento;
la persistencia no detecta inicios en este fixture. No se busca mejorar ni reajustar
esta receta después de observar evaluación. EXP001 y EXP002 conviven con diferente
configuración; compartir algunas métricas no implica compartir identidad ni evidencia.
T16 usa otro propósito y datos: no corresponde comparar sus métricas como si
fueran un ensayo científico emparejado.

## Limitaciones

Solo dos municipios artificiales, un candidato y pocos ajustes CPU. La entrada
certifica los 33 predictores completos aunque EXP002 modele un subconjunto.
Estas pruebas no validan generalización, desempeño real ni nuevos adaptadores.
El estado dirty de EXP002 refleja la evidencia/estado de EXP001 aún sin commit;
el Git SHA y los hashes de código/configuración se conservan por ejecución.

## Decisión científica

NOT_APPLICABLE: ningún campeón seleccionado, ninguna aprobación científica u
operativa y ningún cambio a resultados históricos. No hay uso científico de 2025.

## Qué se aprendió

Cambiar horizontes, semilla, predictores o rondas no requiere duplicar el motor.
La identidad distingue recetas aunque produzcan métricas iguales; conservar
resultados sin mejora evita convertir la infraestructura en selección implícita.

## Próximo paso

Conservar este fixture como regresión técnica. Una investigación real requiere
nuevo ID, protocolo/configuración congelados y aprobación explícita; no está
autorizada por este resultado. La revisión independiente posterior sigue pendiente.
