"""Reconciliar exclusivamente agregados T+2 publicados con su presentación inmutable."""

import csv
import hashlib
import json
from copy import deepcopy

import pytest
import respaldo_cientifico as support
from configuracion import ROOT


def test_published_counts_rates_and_intervals():
    """Una sola fila autorizada sustenta todos los numeradores, denominadores e IC."""
    result = support.load_support()
    source = ROOT / result["source"]["path"]
    original = source.read_bytes()
    assert hashlib.sha256(original).hexdigest() == result["source"]["sha256"]
    with source.open() as stream:
        rows = [row for row in csv.DictReader(stream) if row["receta"] == "log_conclima"
                and row["horizonte"] == "2" and float(row["presupuesto"]) == .1]
    assert len(rows) == 1
    row = rows[0]
    assert result["counts"] == dict(zip(
        ["alerts_per_method", "evaluable_onsets", "evaluable_municipality_months",
         "model_anticipated", "channel_anticipated"],
        [int(row[key]) for key in ["alertas", "inicios", "filas_evaluadas", "modelo", "canal"]],
        strict=True,
    ))
    intervals = result["intervals"]
    first = intervals["sensitivity_difference_pp"]
    second = intervals["false_alerts_difference_per100"]
    assert first == {"estimate": float(row["dif_pp"]), "low": 1.4, "high": 16.3}
    assert [first["low"], first["high"]] == [float(v) for v in row["ic_mes_pp"].split(" a ")]
    assert second == {"estimate": float(row["dif_carga"]), "low": -2.87, "high": -.24}
    assert [second["low"], second["high"]] == [float(v) for v in row["ic_carga"].split(" a ")]
    assert result["origin_months"] == 23 and result["horizon"] == 2
    assert result["period"]["end"] == "2024-12"
    assert support.descriptive_metrics(result) == pytest.approx({
        "sensitivity": 70 / 147, "precision": 70 / 200,
        "f1": 140 / 347, "false_per_hit": 130 / 70,
    })
    sensitivity, burden = support.chart_data(result)
    assert sensitivity.Valor.tolist() == pytest.approx([7000 / 147, 5700 / 147])
    assert burden.Valor.tolist() == pytest.approx([13000 / 836, 14300 / 836])
    assert sensitivity.Etiqueta.tolist() == ["47,6 % · 70/147", "38,8 % · 57/147"]
    assert burden.Etiqueta.tolist() == ["15,6 · 130/836", "17,1 · 143/836"]
    for data, maximum in [(sensitivity, 100), (burden, 25)]:
        spec = support.comparison_chart(data, "Indicador", maximum).to_dict()
        assert [layer["mark"]["type"] for layer in spec["layer"]] == ["bar", "text"]
        assert spec["layer"][0]["encoding"]["x"]["scale"]["domain"] == [0, maximum]
        assert spec["layer"][1]["encoding"]["text"]["field"] == "Etiqueta"
        assert data["Método"].tolist() == list(support.METHODS)
        assert list(data) == ["Método", "Valor", "Etiqueta"]
    assert source.read_bytes() == original


@pytest.mark.parametrize("raw", [None, b"{", b"{}"])
def test_missing_or_changed_support(tmp_path, raw):
    """Bytes distintos o ausentes no se presentan como evidencia verificada."""
    path = tmp_path / "support.json"
    if raw is not None:
        path.write_bytes(raw)
    with pytest.raises(ValueError, match="respaldo científico"):
        support.load_support(path)


@pytest.mark.parametrize("change", [
    {"extra": True}, {"horizon": 1}, {"period": {"end": "2025-12"}},
    {"counts": {"alerts_per_method": 0}},
    {"intervals": {"confidence": .9}},
    {"source": {"sha256": "0" * 64}},
])
def test_schema_and_values_are_checked(tmp_path, monkeypatch, change):
    """Aun con un pin de prueba coherente se rechaza esquema, identidad o valores ajenos."""
    value = deepcopy(support.load_support())
    for key, replacement in change.items():
        if isinstance(replacement, dict):
            value[key].update(replacement)
        else:
            value[key] = replacement
    raw = json.dumps(value).encode()
    path = tmp_path / "support.json"
    path.write_bytes(raw)
    monkeypatch.setattr(support, "SUPPORT_SHA256", hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        support.load_support(path)


@pytest.mark.parametrize(("dark", "color"), [(True, "#fafafa"), (False, "#31333f")])
def test_numeric_labels_follow_theme(dark, color):
    """Las etiquetas numéricas conservan contraste con ambos temas de Streamlit."""
    data, _ = support.chart_data(support.load_support())
    spec = support.comparison_chart(data, "Indicador", 100, dark=dark).to_dict()
    assert spec["layer"][1]["mark"]["color"] == color
