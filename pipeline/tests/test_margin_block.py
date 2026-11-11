"""Bloque de margen: valores, ausencia de fuga y las guardas del contrato.

Estas pruebas existen para fallar. El proyecto ya tuvo dos pruebas vacuas —una
que afirmaba la ausencia de un mensaje de error sin llegar nunca a la guarda, y
un `assert` que comparaba dos expresiones idénticas por construcción— así que
cada afirmación de aquí construye el caso que la discrimina: un valor exacto
calculado a mano, un recorte del futuro que no debe mover nada, una receta que
declara el bloque mal y debe ser rechazada.
"""

from pathlib import Path

import pandas as pd
import pytest

from sat_dengue_pipeline.domain.margin import (
    MARGIN_COLUMNS,
    MARGIN_SOURCES,
    margin_features,
)
from sat_dengue_pipeline.models.adapters import validate_features


def historia() -> pd.DataFrame:
    """Dos municipios, seis meses, con un P75 en cero a propósito."""
    filas = []
    for municipio, casos in (("73001", [10, 20, 40, 30, 50, 60]), ("50001", [0, 1, 2, 3, 4, 5])):
        for i, valor in enumerate(casos):
            filas.append(
                {
                    "municipality_code": municipio,
                    "year_month": f"2020-{i + 1:02d}",
                    "total_notifications_count": float(valor),
                    "dengue_notifications_count": float(valor) - 1.0 if valor else 0.0,
                    "p75_h5_t1": 20.0 if municipio == "73001" else 0.0,
                    "p25_canal_t": 5.0 if municipio == "73001" else 0.0,
                    "p75_canal_t": 15.0 if municipio == "73001" else 0.0,
                }
            )
    return pd.DataFrame(filas)


def test_los_valores_son_los_de_la_definicion() -> None:
    """Margen, posición en banda, velocidad y aceleración, calculados a mano."""
    bloque = margin_features(historia(), 1)
    fila = bloque.loc[("73001", "2020-03")]
    # casos 40, P75 objetivo 20 -> (40-20)/21; P75 curso 15 -> (40-15)/16
    assert fila.margen_objetivo == pytest.approx((40 - 20) / 21)
    assert fila.margen_curso == pytest.approx((40 - 15) / 16)
    # banda 5..15 -> (40-5)/(15-5+1)
    assert fila.pos_banda == pytest.approx((40 - 5) / 11)
    anterior = bloque.loc[("73001", "2020-02")]
    assert fila.margen_curso_vel == pytest.approx(fila.margen_curso - anterior.margen_curso)
    assert fila.margen_curso_acel == pytest.approx(
        fila.margen_curso_vel - anterior.margen_curso_vel
    )


def test_el_percentil_cero_no_produce_infinitos() -> None:
    """Los 153 de 912 municipios-mes con P75 = 0 ya degeneraron una regla antes."""
    bloque = margin_features(historia(), 1)
    cero = bloque.loc["50001"]
    assert cero.notna().any().any()
    # Las velocidades del primer mes son NA por definición; lo que se exige es
    # que ningún valor presente sea infinito.
    presentes = cero[MARGIN_COLUMNS].to_numpy(dtype=float).ravel()
    assert all(abs(v) < 1e9 for v in presentes if v == v)


def test_la_primera_observacion_no_inventa_velocidad() -> None:
    """Sin mes anterior no hay diferencia; nunca se rellena con cero."""
    bloque = margin_features(historia(), 1)
    assert pd.isna(bloque.loc[("73001", "2020-01")].margen_curso_vel)
    assert pd.isna(bloque.loc[("73001", "2020-02")].margen_curso_acel)


def test_recortar_el_futuro_no_cambia_el_pasado() -> None:
    """La prueba anti-fuga: el valor del mes t no depende de que exista t+1.

    Si alguna de las seis mirara hacia adelante —por ejemplo con un shift(-1)
    en vez de shift(1)— esta comparación fallaría.
    """
    completo = margin_features(historia(), 1)
    recortado = margin_features(historia().query("year_month <= '2020-03'"), 1)
    comun = recortado.index
    pd.testing.assert_frame_equal(completo.loc[comun], recortado.loc[comun])


def test_la_fuente_de_casos_cambia_el_resultado_y_se_declara() -> None:
    """Las dos fuentes dan valores distintos; una fuente no declarada se rechaza."""
    total = margin_features(historia(), 1, MARGIN_SOURCES[0])
    dengue = margin_features(historia(), 1, MARGIN_SOURCES[1])
    assert not total.margen_curso.equals(dengue.margen_curso)
    with pytest.raises(ValueError):
        margin_features(historia(), 1, "total_notifications_count_x")


def test_un_insumo_ausente_falla_con_su_nombre() -> None:
    """Quien lo lea tiene que saber qué columna falta, no recibir un KeyError."""
    with pytest.raises(ValueError, match="p75_canal_t"):
        margin_features(historia().drop(columns=["p75_canal_t"]), 1)


def test_las_derivadas_no_pueden_colarse_sin_declararse() -> None:
    """`validate_features` acepta el bloque solo cuando la receta lo declara."""
    X = pd.DataFrame({"month_of_year": [1.0, 2.0], "margen_curso": [0.5, 0.6]})
    with pytest.raises(ValueError):
        validate_features(X, predictors=("month_of_year",))
    validate_features(X, predictors=("month_of_year",), derived=("margen_curso",))


def test_una_derivada_canonica_se_rechaza() -> None:
    """Nada del contrato canónico puede entrar disfrazado de derivada."""
    X = pd.DataFrame({"month_of_year": [1.0, 2.0]})
    with pytest.raises(ValueError):
        validate_features(X, predictors=("month_of_year",), derived=("month_of_year",))


def test_el_orden_del_bloque_es_fijo() -> None:
    """Invertirlo cambia la matriz interna y el modelo entrenado; se rechaza."""
    columnas = ["month_of_year", *reversed(MARGIN_COLUMNS)]
    X = pd.DataFrame({c: [1.0, 2.0] for c in columnas})
    with pytest.raises(ValueError):
        validate_features(X, predictors=("month_of_year",), derived=tuple(reversed(MARGIN_COLUMNS)))


def test_el_orden_de_las_filas_de_entrada_no_cambia_el_resultado() -> None:
    """Los rezagos exigen la serie ordenada; una entrada barajada da lo mismo.

    Sin el ordenamiento previo, `shift(1)` toma como "mes anterior" la fila que
    venga antes en el archivo, que no tiene por qué ser el mes anterior. El
    panel real llega ordenado, así que este caso es el único que discrimina.
    """
    ordenado = margin_features(historia(), 1)
    barajado = margin_features(
        historia().sample(frac=1.0, random_state=7).reset_index(drop=True), 1
    )
    pd.testing.assert_frame_equal(ordenado, barajado.loc[ordenado.index])


def test_el_piso_de_entrenamiento_sigue_a_la_cobertura_del_release() -> None:
    """2012-01 es el primer objetivo entrenable, no 2018-01.

    El piso anterior venía del release histórico (2011-06) y dejaba fuera seis
    años de historia que el release operacional sí trae. Esta prueba fija el
    piso nuevo por los dos lados: lo que antes se rechazaba ahora se acepta, y
    lo que está por debajo de la cobertura se sigue rechazando.
    """
    from sat_dengue_pipeline.experiments.rolling import TRAIN_FLOOR, ExperimentSpec

    assert TRAIN_FLOOR == "2012-01"
    ExperimentSpec(
        horizon=1, train_target_start="2012-01", first_origin="2018-01", last_target="2018-02"
    )
    with pytest.raises(ValueError):
        ExperimentSpec(
            horizon=1, train_target_start="2011-12", first_origin="2018-01", last_target="2018-02"
        )
    with pytest.raises(ValueError):
        # Sin un solo mes de entrenamiento antes del primer origen.
        ExperimentSpec(
            horizon=1, train_target_start="2018-01", first_origin="2018-01", last_target="2018-02"
        )


def test_la_velocidad_usa_el_mes_anterior_y_no_la_fila_anterior() -> None:
    """Con un hueco de calendario no hay velocidad; nunca una resta contra t-2.

    El panel canónico es una rejilla completa, así que este caso no aparece en
    producción, pero `shift(1)` lo habría resuelto restando contra dos meses
    atrás sin avisar. La ausencia es la respuesta correcta.
    """
    con_hueco = historia().query("not (municipality_code == '73001' and year_month == '2020-03')")
    bloque = margin_features(con_hueco, 1)
    completo = margin_features(historia(), 1)
    # El mes siguiente al hueco no tiene mes anterior: velocidad ausente.
    assert pd.isna(bloque.loc[("73001", "2020-04")].margen_curso_vel)
    # Y sin el hueco sí la tiene, así que la prueba discrimina.
    assert not pd.isna(completo.loc[("73001", "2020-04")].margen_curso_vel)
    # Los meses anteriores al hueco no cambian.
    assert bloque.loc[("73001", "2020-02")].margen_curso_vel == pytest.approx(
        completo.loc[("73001", "2020-02")].margen_curso_vel
    )


def test_el_adaptador_xgboost_tambien_se_construye_con_el_bloque() -> None:
    """La fábrica declara G sobre XGBoost; construir el adaptador no puede fallar.

    Ninguna receta versionada enciende `variables_g`, así que las ramas del
    adaptador que leen el bloque no se ejecutaban nunca y un nombre sin importar
    habría pasado inadvertido hasta la primera corrida con G.
    """
    import yaml

    from sat_dengue_pipeline.factory.configuration import adapter_spec
    from sat_dengue_pipeline.models.xgboost import XGBoostOnsetAdapter

    ruta = Path(__file__).resolve().parents[1] / "conf/experiments/EXP001.yml"
    config = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    assert config["preparation"]["variables_g"] is False
    config["preparation"]["variables_g"] = True
    config["preparation"]["matrix_columns"] = [
        *config["preparation"]["matrix_columns"],
        *MARGIN_COLUMNS,
    ]
    adaptador = XGBoostOnsetAdapter(adapter_spec(config))
    assert adaptador.derived == tuple(MARGIN_COLUMNS)


def _datos_con_bloque(horizonte: int = 1):
    """Muestra artificial del arnés con las seis columnas del bloque al final."""
    from fixtures.experiment_fixture import make_experiment

    from sat_dengue_pipeline.experiments.rolling import ExperimentData

    datos = make_experiment(horizonte)
    X = datos.X.copy()
    for i, nombre in enumerate(MARGIN_COLUMNS):
        # Márgenes con signo, como los reales; no se parecen a ningún canónico.
        X[nombre] = [((j + i) % 9 - 4) / 3.0 for j in range(len(X))]
    return ExperimentData(datos.keys, X, datos.y, datos.controls, derived=tuple(MARGIN_COLUMNS))


def test_el_bloque_llega_hasta_el_modelo_a_traves_del_arnes() -> None:
    """De punta a punta por `run_candidate`, con el adaptador real de la receta G.

    Esta es la prueba que faltaba. El envoltorio `CheckedAdapter` valida la
    matriz por su cuenta, aparte del adaptador, así que el bloque puede estar
    bien construido, bien declarado y bien proyectado y aun así ser rechazado
    en la frontera. Pasaba: los 82 orígenes de la primera corrida con G se
    omitieron con «Esquema de características inválido», y ninguna prueba que
    parara antes del arnés podía verlo.
    """
    import yaml

    from sat_dengue_pipeline.experiments.rolling import ExperimentSpec
    from sat_dengue_pipeline.factory.configuration import adapter_spec
    from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
    from sat_dengue_pipeline.models.familias import ADAPTERS

    receta = Path(__file__).resolve().parents[1] / "conf/retroanalisis/logistica_g.yml"
    config = yaml.safe_load(receta.read_text(encoding="utf-8"))
    spec = adapter_spec(config)
    registry = ModelRegistry()
    registry.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    datos = _datos_con_bloque()
    protocolo = ExperimentSpec(
        1,
        seed=config["seed"],
        last_target="2019-04",
        label_delay_months=config["label_delay_months"],
    )
    frame, auditoria = run_candidate(datos, protocolo, spec, registry)
    assert not frame.empty and frame.raw_probability.between(0, 1).all()
    # La procedencia tiene que declarar lo que el modelo vio de verdad.
    assert all(fila["features"][-6:] == MARGIN_COLUMNS for fila in auditoria["adapters"])


def test_receta_y_preparacion_tienen_que_declarar_lo_mismo() -> None:
    """Una receta sin G contra datos con el bloque se rechaza, y al revés."""
    import yaml

    from sat_dengue_pipeline.experiments.rolling import ExperimentData, ExperimentSpec
    from sat_dengue_pipeline.factory.configuration import adapter_spec
    from sat_dengue_pipeline.models.adapters import ModelRegistry, run_candidate
    from sat_dengue_pipeline.models.familias import ADAPTERS

    base = Path(__file__).resolve().parents[1] / "conf/retroanalisis/logistica_sin_clima.yml"
    config = yaml.safe_load(base.read_text(encoding="utf-8"))
    spec = adapter_spec(config)
    registry = ModelRegistry()
    registry.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    protocolo = ExperimentSpec(
        1,
        seed=config["seed"],
        last_target="2019-04",
        label_delay_months=config["label_delay_months"],
    )
    with pytest.raises(ValueError, match="derivadas"):
        run_candidate(_datos_con_bloque(), protocolo, spec, registry)
    # Y los datos sin bloque con esa misma receta sí corren, para que la prueba
    # distinga el desajuste de un rechazo general.
    from fixtures.experiment_fixture import make_experiment

    datos = make_experiment(1)
    registry_limpio = ModelRegistry()
    registry_limpio.register(spec.family, spec.version, ADAPTERS[(spec.family, spec.version)])
    frame, _ = run_candidate(
        ExperimentData(datos.keys, datos.X, datos.y, datos.controls),
        protocolo,
        spec,
        registry_limpio,
    )
    assert not frame.empty


def test_una_receta_con_subconjunto_y_bloque_acepta_la_entrada_canonica() -> None:
    """XGBoost con menos predictores que el canon, más el bloque, sobre X completa.

    El retroanálisis entrega siempre el contrato canónico completo más las
    derivadas; la fábrica entrega el subconjunto declarado más las derivadas.
    Las dos formas tienen que proyectar la misma matriz. Sin esto, una receta
    que quite columnas y encienda G rechaza sus 82 orígenes con «Esquema de
    características inválido», que es lo que pasó al medir la línea U.
    """
    import numpy as np
    import yaml

    from sat_dengue_pipeline.domain.canonical import PREDICTORS
    from sat_dengue_pipeline.factory.configuration import adapter_spec
    from sat_dengue_pipeline.models.xgboost import XGBoostOnsetAdapter

    ruta = (
        Path(__file__).resolve().parents[1] / "conf/retroanalisis/xgboost_banco_sin_umbrales_g.yml"
    )
    config = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    declarados = config["predictors"]
    assert len(declarados) < len(PREDICTORS), "la receta tiene que ser un subconjunto"
    adaptador = XGBoostOnsetAdapter(adapter_spec(config))

    def entrada(columnas):
        """Matriz mínima con las columnas pedidas, en ese orden."""
        X = pd.DataFrame({c: np.linspace(1.0, 4.0, 4) for c in columnas})
        if "zona_canal_t" in columnas:
            X["zona_canal_t"] = ["EXITO", "ALERTA", "EXITO", "SEGURIDAD"]
        return X[list(columnas)]

    canonica = adaptador.matrix(entrada([*PREDICTORS, *MARGIN_COLUMNS]))
    recortada = adaptador.matrix(entrada([*declarados, *MARGIN_COLUMNS]))
    assert canonica.shape == recortada.shape
    assert np.array_equal(canonica, recortada), "las dos formas proyectan la misma matriz"
    assert canonica.shape[1] == len(config["preparation"]["matrix_columns"])
