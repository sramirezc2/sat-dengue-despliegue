"""Paridad de inicio, calendarios, ausencias y compuerta previa a etiquetas."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fixtures.canonical_fixture import canonical_bytes, frame_payload, make_panel
from fixtures.onset_fixture import make_states
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner

from sat_dengue_pipeline import preparation
from sat_dengue_pipeline.domain.canonical import KEYS, PREDICTORS, build_table
from sat_dengue_pipeline.domain.onset import (
    build_labels,
    operational_eligibility,
    validate_label_metadata,
)
from sat_dengue_pipeline.domain.temporal import (
    TemporalPolicy,
    guard_development,
    select_origins,
)
from sat_dengue_pipeline.pipeline_registry import register_pipelines
from sat_dengue_pipeline.pipelines.preparation import create_pipeline
from sat_dengue_pipeline.pipelines.preparation.nodes import prepare_onset
from sat_dengue_pipeline.preparation import (
    PREDICTOR_AVAILABILITY,
    prepare_horizon,
    project_predictors,
)

FIXTURES = Path(__file__).parent / "fixtures"


def one_origin(period: str) -> pd.DataFrame:
    """Construir una solicitud artificial con una clave explícita."""
    return pd.DataFrame({"municipality_code": ["50998"], "year_month": [period]})


def test_onset_exact_v2_reference() -> None:
    """Comparar valores, nulos, tipos y digest contra ejecución fijada de V2."""
    states = make_states()
    original = states.copy(deep=True)
    payload = {}
    for horizon in (1, 2):
        result = build_labels(states, states[KEYS], horizon)
        projected = result.rename(
            columns={
                f"target_period_t{horizon}": "target_month",
                f"y_t{horizon}": "onset_target",
            }
        )[
            KEYS
            + ["eligible_at_t", "target_month", "excess_target", "onset_target", "earlier_onset_t1"]
        ]
        payload[f"t{horizon}"] = frame_payload(projected)
    expected = (FIXTURES / "onset_expected.json").read_bytes()
    receipt = json.loads((FIXTURES / "onset_receipt.json").read_bytes())
    assert canonical_bytes(payload) == expected
    assert hashlib.sha256(expected).hexdigest() == receipt["output_sha256"]
    assert (
        hashlib.sha256(canonical_bytes(frame_payload(states))).hexdigest()
        == (receipt["input_sha256"])
    )
    pd.testing.assert_frame_equal(states, original)


@pytest.mark.parametrize(
    "values,horizon,expected,eligible,earlier",
    [
        ([0, 1, 1], 1, 1, True, True),
        ([0, 0, 1], 2, 1, True, False),
        ([0, 1, 1], 2, 0, True, True),
        ([1, 1, 1], 1, 0, False, False),
        ([1, 0, 1], 2, 1, False, False),
        ([0, 0, 0], 1, 0, True, False),
        ([pd.NA, 0, 1], 2, 1, False, False),
        ([0, pd.NA, 1], 2, None, True, False),
        ([0, 0, pd.NA], 2, None, True, False),
        ([0, pd.NA, pd.NA], 2, None, True, False),
    ],
)
def test_onset_semantics(
    values: list[Any], horizon: int, expected: int | None, eligible: bool, earlier: bool
) -> None:
    """Preservar inicio, persistencia, elegibilidad en T y ausencias explícitas."""
    states = pd.DataFrame(
        {
            "municipality_code": ["50998"] * 3,
            "year_month": ["2023-12", "2024-01", "2024-02"],
            "excess": pd.array(values, dtype="Int64"),
        }
    )
    result = build_labels(states, one_origin("2023-12"), horizon).iloc[0]
    value = result[f"y_t{horizon}"]
    assert pd.isna(value) if expected is None else value == expected
    assert bool(result.eligible_at_t) == eligible
    assert bool(result.earlier_onset_t1) == earlier
    assert bool(result[f"y_evaluable_t{horizon}"]) == (expected is not None)
    assert result[f"target_period_t{horizon}"] == ("2024-01" if horizon == 1 else "2024-02")
    if expected is None:
        assert result[f"y_status_t{horizon}"].startswith("missing_")


def test_missing_month_is_never_bridged() -> None:
    """T+2 no usa el origen como anterior si falta T+1."""
    states = make_states().loc[lambda f: f.year_month.ne("2024-01")].reset_index(drop=True)
    result = build_labels(states, one_origin("2023-12"), 2).iloc[0]
    assert pd.isna(result.y_t2)
    assert result.y_status_t2 == "missing_previous"
    assert result.eligible_at_t
    first = build_labels(states, one_origin("2023-12"), 1).iloc[0]
    assert pd.isna(first.y_t1) and first.y_status_t1 == "missing_target"


def test_eligibility_reads_only_current_and_preserves_zero() -> None:
    """Cambios retrospectivos de resultados no cambian la decisión al origen."""
    current = pd.Series([0, 1, pd.NA], dtype="Int64")
    assert operational_eligibility(current).tolist() == [True, False, False]
    with pytest.raises(ValueError, match="binario"):
        operational_eligibility(pd.Series([2]))
    states = make_states()
    first = build_labels(states, one_origin("2023-12"), 2)
    states.loc[states.year_month.gt("2023-12"), "excess"] = pd.NA
    changed = build_labels(states, one_origin("2023-12"), 2)
    pd.testing.assert_series_equal(first.eligible_at_t, changed.eligible_at_t)
    assert pd.isna(changed.y_t2.iloc[0])


@pytest.mark.parametrize("origin,horizon", [("2024-12", 1), ("2024-11", 2), ("2025-01", 1)])
def test_reserved_target_rejected_before_labels(origin: str, horizon: int) -> None:
    """Rechazar cruces a 2025 sin leer la columna de estados o etiquetas."""

    class UnreadLabels(pd.DataFrame):
        """Centinela: cualquier lectura científica de la fila sería un fallo."""

        def __getitem__(self, key: Any) -> Any:
            """Permitir exclusivamente acceso a claves antes del rechazo."""
            names = [key] if isinstance(key, str) else key if isinstance(key, list) else []
            assert not set(names) & {"excess", "y_t1", "y_t2"}, "Etiqueta reservada leída"
            return super().__getitem__(key)

    states = UnreadLabels(one_origin(origin).assign(excess="NO_LEER", y_t1="NO_LEER"))
    with pytest.raises(ValueError, match="reservado"):
        build_labels(states, one_origin(origin), horizon)


def test_october_t2_allowed_and_policy_configurable() -> None:
    """2024 no se reserva rígidamente y octubre puede apuntar a diciembre."""
    states = pd.DataFrame(
        {
            "municipality_code": ["50998"] * 3,
            "year_month": ["2024-10", "2024-11", "2024-12"],
            "excess": [0, 0, 1],
        }
    )
    result = build_labels(states, one_origin("2024-10"), 2).iloc[0]
    assert result.target_period_t2 == "2024-12" and result.y_t2 == 1
    with pytest.raises(ValueError, match="reservado"):
        build_labels(states, one_origin("2024-10"), 2, TemporalPolicy("2024-12"))
    with pytest.raises(ValueError):
        TemporalPolicy("2026-01")


@pytest.mark.parametrize("fault", ["duplicate", "period", "target", "binary", "horizon"])
def test_malformed_states_rejected(fault: str) -> None:
    """Rechazar entradas ambiguas o alteradas sin repararlas."""
    states, origins, horizon = make_states(), one_origin("2023-12"), 1
    if fault == "duplicate":
        states = pd.concat([states, states.iloc[[0]]], ignore_index=True)
    elif fault == "period":
        states.loc[0, "year_month"] = "2023-13"
    elif fault == "target":
        origins["target_period_t1"] = "2024-02"
    elif fault == "binary":
        states.loc[0, "excess"] = 2
    else:
        horizon = 3
    with pytest.raises(ValueError):
        build_labels(states, origins, horizon)


@pytest.mark.parametrize(
    "fault", ["binary", "coercion", "evaluable", "target", "status", "unknown_status"]
)
def test_label_metadata_rejected(fault: str) -> None:
    """Una ausencia no se admite por coerción de etiqueta o evaluabilidad."""
    labels = build_labels(make_states(), make_states()[KEYS], 2)
    if fault == "binary":
        labels.loc[0, "y_t2"] = 2
    elif fault == "coercion":
        labels.loc[labels.y_t2.isna(), "y_t2"] = 0
    elif fault == "evaluable":
        labels["y_evaluable_t2"] = False
    elif fault == "target":
        labels.loc[0, "target_period_t2"] = "2024-03"
    elif fault == "status":
        labels.loc[0, "y_status_t2"] = "missing_target"
    else:
        labels.loc[labels.y_t2.isna(), "y_status_t2"] = "inventado"
    with pytest.raises(ValueError):
        validate_label_metadata(labels, 2)


def test_windows_select_targets_and_embargo_origins() -> None:
    """Selecciones fijas no cruzan el fin objetivo ni el rol temporal anterior."""
    states = make_states()
    first = select_origins(states, "2024-01", "2024-02", 2)
    second = select_origins(states, "2024-03", "2024-05", 2, previous_end="2024-02")
    assert first.year_month.tolist() == ["2023-12"]
    assert second.year_month.tolist() == ["2024-02", "2024-03"]
    with pytest.raises(ValueError, match="solapadas"):
        select_origins(states, "2024-02", "2024-05", 2, previous_end="2024-02")
    with pytest.raises(ValueError, match="reservada"):
        select_origins(states, "2024-01", "2025-01", 2)


def test_preparation_separates_roles_and_is_deterministic() -> None:
    """Producir salidas alineadas sin mutación y conservar auditoría de ausencias."""
    table, schema = build_table(make_panel())
    origins = table.loc[table.year_month.between("2023-01", "2024-10"), KEYS]
    before, schema_before, origins_before = (
        table.copy(deep=True),
        copy.deepcopy(schema),
        origins.copy(),
    )
    outputs = []
    for _ in range(2):
        outputs.append(prepare_onset(table, schema, origins, PREDICTOR_AVAILABILITY, "2025-01"))
    for h in (1, 2):
        pd.testing.assert_frame_equal(outputs[0][f"labels_t{h}"], outputs[1][f"labels_t{h}"])
        control = outputs[0]["controls"][f"t{h}"]
        assert f"y_t{h}" not in control
        prepared = outputs[0][f"eligible_t{h}"]
        assert len(prepared.X) == len(prepared.y) == len(prepared.keys) > 0
        assert list(prepared.X) == PREDICTORS
        assert prepared.X.notna().all().all() and prepared.y.isin([0, 1]).all()
        assert prepared.y.name == f"y_t{h}"
        assert outputs[0]["audit"][f"t{h}"]["last_target"] < "2025-01"
    pd.testing.assert_frame_equal(table, before)
    pd.testing.assert_frame_equal(origins, origins_before)
    assert schema == schema_before


def test_preparation_uses_keys_independently_of_dataframe_index() -> None:
    """Orden e índices de pandas no alteran la alineación municipio-mes de X/y."""
    table, schema = build_table(make_panel())
    origins = table.loc[table.year_month.eq("2024-10"), KEYS]
    expected = prepare_horizon(table, schema, origins, 2, PREDICTOR_AVAILABILITY)
    shuffled = table.sample(frac=1, random_state=7)
    shuffled.index = [0] * len(shuffled)
    actual = prepare_horizon(shuffled, schema, origins.iloc[::-1], 2, PREDICTOR_AVAILABILITY)
    pd.testing.assert_frame_equal(expected[0], actual[0])
    pd.testing.assert_frame_equal(expected[1], actual[1])
    pd.testing.assert_frame_equal(expected[2].X, actual[2].X)
    pd.testing.assert_series_equal(expected[2].y, actual[2].y)


def test_november_t1_remains_allowed() -> None:
    """La función por horizonte permite noviembre T+1, con objetivo diciembre."""
    table, schema = build_table(make_panel())
    origins = table.loc[table.year_month.eq("2024-11"), KEYS]
    controls, _, _, audit = prepare_horizon(table, schema, origins, 1, PREDICTOR_AVAILABILITY)
    assert controls.target_period_t1.eq("2024-12").all()
    assert audit["last_target"] == "2024-12"


@pytest.mark.parametrize(
    "forbidden",
    [
        "y_t1",
        "target_period_t1",
        "onset_target",
        "eligible_at_t",
        "p75_t1",
        "excess_target",
        "dengue_count_t1",
        "future_available",
    ],
)
def test_closed_predictors_reject_future_roles(forbidden: str) -> None:
    """Ni una allowlist editada puede introducir etiquetas o controles en X."""
    panel = make_panel()
    panel[forbidden] = 1
    table, schema = build_table(panel)
    tampered = copy.deepcopy(schema)
    role = "target" if forbidden == "y_t1" else "control"
    tampered["column_roles"][role].remove(forbidden)
    tampered["column_roles"]["feature"].append(forbidden)
    with pytest.raises(ValueError, match="Roles"):
        project_predictors(table, tampered, PREDICTOR_AVAILABILITY)


def test_future_availability_and_existing_labels_rejected() -> None:
    """Validar disponibilidad y metadatos ya existentes, sin reutilizarlos a ciegas."""
    panel = make_panel()
    table, schema = build_table(panel)
    origins = table.loc[table.year_month.eq("2024-10"), KEYS]
    future = {**PREDICTOR_AVAILABILITY, "p75_h5_t1": 1}
    with pytest.raises(ValueError, match="Disponibilidad futura"):
        prepare_horizon(table, schema, origins, 2, future)
    panel["y_t2"] = 2
    table, schema = build_table(panel)
    with pytest.raises(ValueError, match="Metadato objetivo"):
        prepare_horizon(table, schema, origins, 2, PREDICTOR_AVAILABILITY)


def memory_catalog(
    table: pd.DataFrame, schema: dict[str, Any], origins: pd.DataFrame
) -> DataCatalog:
    """Construir entradas explícitas sin I/O, proveedor o release supuesto."""
    return DataCatalog(
        {
            name: MemoryDataset(data=value, copy_mode="assign")
            for name, value in {
                "canonical_table": table,
                "canonical_schema": schema,
                "onset_origins": origins,
                "params:onset.reserved_start": "2025-01",
                "params:onset.availability": PREDICTOR_AVAILABILITY,
            }.items()
        }
    )


def test_preparation_kedro_memory_integration() -> None:
    """Ejecutar ambas etapas con MemoryDataset y seis salidas separadas."""
    table, schema = build_table(make_panel())
    origins = table.loc[table.year_month.between("2023-01", "2024-10"), KEYS]
    results = SequentialRunner().run(create_pipeline(), memory_catalog(table, schema, origins))
    assert set(results) == {
        "controls",
        "labels_t1",
        "labels_t2",
        "audit",
        "eligible_t1",
        "eligible_t2",
    }
    assert results["audit"].load()["t2"]["last_target"] == "2024-12"
    assert "preparation" not in register_pipelines()


@pytest.mark.parametrize("case", ["t1_crossing", "t2_crossing", "origin_2025", "observation_2025"])
def test_sentinel_2025_before_consumer(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Centinela Kedro: cero lecturas de etiquetas y cero llamadas al consumidor."""
    table, schema = build_table(make_panel())
    origin = {
        "t1_crossing": "2024-12",
        "t2_crossing": "2024-11",
        "origin_2025": "2025-01",
        "observation_2025": "2024-10",
    }[case]
    origins = one_origin(origin)
    if case in {"origin_2025", "observation_2025"}:
        # Solo clave centinela, sin observación ni etiqueta científica de 2025.
        table = pd.concat([table, one_origin("2025-01")], ignore_index=True)
    calls = {"labels": 0, "consumer": 0}

    def forbidden_label_read(*args: Any, **kwargs: Any) -> None:
        """Detectar cualquier intento prematuro de construir o leer etiquetas."""
        calls["labels"] += 1
        pytest.fail("Se consultaron etiquetas antes del rechazo")

    def consumer(*args: Any) -> None:
        """Representar cualquier etapa futura de desarrollo sin implementar modelos."""
        calls["consumer"] += 1
        pytest.fail("Se entregaron filas reservadas a una etapa posterior")

    monkeypatch.setattr(preparation, "build_labels", forbidden_label_read)
    graph = create_pipeline() + Pipeline(
        [node(consumer, ["eligible_t1", "eligible_t2"], "consumed")]
    )
    with pytest.raises(ValueError, match="reservado"):
        SequentialRunner().run(graph, memory_catalog(table, schema, origins))
    assert calls == {"labels": 0, "consumer": 0}
    # La entrada directa queda protegida aunque se omita el grafo Kedro.
    with pytest.raises(ValueError, match="reservado"):
        prepare_onset(table, schema, origins, PREDICTOR_AVAILABILITY, "2025-01")
    assert calls == {"labels": 0, "consumer": 0}


def test_guard_does_not_read_labels_for_reserved_target() -> None:
    """La compuerta solo necesita claves; no requiere que exista una etiqueta."""
    with pytest.raises(ValueError, match="reservado"):
        guard_development(one_origin("2024-12"), one_origin("2024-12"), (1,), TemporalPolicy())
