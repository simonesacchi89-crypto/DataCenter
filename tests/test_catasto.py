"""Test del connettore Catasto.

- Test senza rete: calcolo della superficie e lettura del GML.
- Test con rete (connettore reale, come chiede CLAUDE.md): una particella nota, Magenta foglio 4 particella 211,
  e il lotto ex Novaceta (15 particelle) che deve tornare con i 215.300 m² dello SIA (dic. 2025).
Avvio: python3 -m pytest tests/test_catasto.py
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend import catasto as C  # noqa: E402

NOVACETA = "37,42,166,206,207,210,211,212,213,214,218,219,237,242,243".split(",")


def test_area_quadrato_100m():
    # quadrato di circa 100 m × 100 m a Magenta: area attesa ~10.000 m²
    lat, lon = 45.467, 8.874
    dlat, dlon = 100 / 111_150, 100 / (111_320 * 0.70155)
    g = {"type": "Polygon", "coordinates": [[[lon, lat], [lon + dlon, lat], [lon + dlon, lat + dlat],
                                             [lon, lat + dlat], [lon, lat]]]}
    assert abs(C.area_m2(g) - 10_000) < 50


def test_area_con_buco():
    g = {"type": "Polygon", "coordinates": [
        [[0, 45], [0.01, 45], [0.01, 45.01], [0, 45.01], [0, 45]],
        [[0.004, 45.004], [0.006, 45.004], [0.006, 45.006], [0.004, 45.006], [0.004, 45.004]]]}
    pieno = C.area_m2({"type": "Polygon", "coordinates": [g["coordinates"][0]]})
    assert abs(C.area_m2(g) - pieno * 0.96) < 1


def test_lettura_gml_lat_lon_invertiti():
    xml = ('<p xmlns:gml="http://www.opengis.net/gml/3.2"><gml:Polygon><gml:exterior><gml:LinearRing>'
           '<gml:posList>45.0 8.0 45.0 8.1 45.1 8.1 45.0 8.0</gml:posList>'
           '</gml:LinearRing></gml:exterior></gml:Polygon></p>')
    g = C._geometria(ET.fromstring(xml))
    assert g["type"] == "Polygon" and g["coordinates"][0][1] == [8.1, 45.0]  # GeoJSON: lon, lat


def test_scomponi_riferimento():
    d = C._scomponi("E801_000400.211")
    assert (d["codice_comune"], d["foglio"], d["allegato"], d["particella"]) == ("E801", 4, "0", "211")


@pytest.fixture
def cache_temporanea(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CACHE_DIR", tmp_path)  # forza chiamate reali


def test_rete_particella_da_punto(cache_temporanea):
    r = C.particella_da_punto(45.4670, 8.8736)
    p = r["particelle"][0]
    assert p["riferimento"] == "E801_000400.211"
    assert abs(p["superficie_m2"] - 66_262) < 700  # ±1%
    assert r["licenza"].startswith("CC BY 4.0") and r["consultato_il"]


def test_rete_lotto_novaceta_come_sia(cache_temporanea):
    r = C.cerca_particelle("Magenta", 4, NOVACETA, "MI")
    assert r["comune"]["codice_catastale"] == "E801"
    assert r["non_trovate"] == []
    tot = sum(p["superficie_m2"] for p in r["particelle"])
    assert abs(tot - 215_300) / 215_300 < 0.01  # SIA dic. 2025: circa 215.300 m²


def test_rete_particella_inesistente(cache_temporanea):
    r = C.cerca_particelle("Magenta", 4, ["999999"], "MI")
    assert r["particelle"] == [] and r["non_trovate"] == ["999999"]


def test_comuni_omonimi_e_trento(cache_temporanea):
    with pytest.raises(C.NonTrovato, match="provincia"):
        C.trova_comune("San Teodoro")
    assert C.trova_comune("San Teodoro", "SS")["codice_catastale"] == "I329"
    with pytest.raises(C.ErroreFonte, match="Trento"):
        C.trova_comune("Trento")
