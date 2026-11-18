Trazabilidad del resultado de la reserva 2023-2024 en T+2 (tanda 58; la lectura por presupuesto está en la tanda 60)
Logística con clima (receta log_conclima), presupuesto del 10 %: el canal anticipa 57 y el modelo 70 de 147 inicios, +8.8 pp, IC por bloques de mes de 1.4 a 16.3.

ARCHIVOS
- predicciones_log_conclima.csv: las predicciones originales de log_conclima (8124 filas, T+1 y T+2, orígenes 2018-2024). Salen de pipeline/tools/noche/correr.py con conf/retroanalisis/noche/log_conclima.yml sobre la base común. Para la reserva no se reentrenó nada.
- predicciones_t58_todas.csv (62 MB, no se sube al repo; se comparte aparte): el archivo completo que leyó el evaluador en la corrida original. Tiene todas las recetas con 8124 filas.
- veredicto_anios.py: copia de pipeline/tools/noche/veredicto.py de main, que ya trae la semilla por celda del PR #10, con una sola línea agregada (la línea 71). Esa línea deja solo los años objetivo indicados en la variable ANIOS:
      anios = tuple(a for a in anios if str(a) in os.environ["ANIOS"].split(","))
  El resto del evaluador es idéntico.
- reserva.csv y reserva.log: la salida original al 10 %.
- reserva_curva.csv: la misma lectura al 5, 10, 15, 20 y 30 %.

CÓMO SE APLICÓ EL PRESUPUESTO (después de filtrar a 2023-2024)
- Objetivo de alertas = 10 % x 76 municipios x 23 meses de origen = 175 alertas.
- Se evalúa el canal condicionado (casos > f·P75 del mes objetivo, solo en municipios fuera de exceso en el origen) para cada f de la grilla, y se toma el f cuyo total de alertas queda más cerca del objetivo: f = 0.95, con 200 alertas (8.7 por mes).
- El modelo emite el mismo número de alertas que el canal en cada mes de origen (va.emparejar) y las asigna a los puntajes más altos de la misma cohorte evaluable.
- Se cuentan, para el canal y para el modelo, cuántos de los 147 inicios evaluables quedan con alerta.

INTERVALO
- La diferencia de inicios por fila se suma por mes de origen.
- Esos bloques se remuestrean con reemplazo, 2000 réplicas, y se toman los percentiles 2.5 y 97.5. El resultado se divide entre los 147 inicios.
- La semilla sale del hash de la celda (receta, horizonte, presupuesto), así que el intervalo no depende de qué otras recetas se evalúen en la misma llamada.
- En el CSV, ic_mes_pp es el intervalo que se reporta e ic_mun_pp (remuestreo por municipio) es solo de referencia.

COMANDOS (desde pipeline/, con PYTHONPATH=src y el panel certificado de49b11b... en data/noche_panel/)
1) Armado de las predicciones de la tanda 58:
   - se concatenaron los predicciones*.csv de data/noche/{todas,t52,d2s,t56,rezagos,rocio,depto27,sin2020,nac,transf};
   - se excluyeron los ensambles (ens_) y las referencias (ref_);
   - se quitaron los duplicados por receta, municipio, origen y horizonte;
   - se dejaron solo las recetas con 8124 filas.
2) Evaluación (el evaluador lee todos los predicciones*.csv de la carpeta que recibe):
   ANIOS=2023,2024 FRACS=0.10 SALIDA=reserva.csv python veredicto_anios.py data/noche/t58 log_conclima
   - La corrida original incluyó además logc_mes y las cinco semillas de xgb_d2_sinclima. Por la semilla por celda, eso no cambia el resultado de log_conclima.
   - Para la curva: FRACS=0.05,0.10,0.15,0.20,0.30 SALIDA=reserva_curva.csv

VERIFICACIÓN
El 16 de noviembre se volvió a correr el comando 2 y dio exactamente las mismas cifras (57, 70, +8.8, IC de 1.4 a 16.3).
