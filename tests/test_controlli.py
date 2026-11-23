"""Test dei controlli automatici (Fase 3).

Senza rete: distanze geometriche e logica dei criteri 8 e 10 con una risposta Overpass di prova.
Con rete: lotto ex Novaceta (Magenta) e punti di controllo dove la risposta deve essere 'positiva'.
Avvio: python3 -m pytest tests/test_controlli.py
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend import controlli as K  # noqa: E402
from backend.geo import Lotto  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def quadrato(lon, lat, lato_m):
    dlat, dlon = lato_m / 111_150, lato_m / (111_320 * 0.7)
    return {"type": "Polygon", "coordinates": [[[lon, lat], [lon + dlon, lat], [lon + dlon, lat + dlat],
                                                [lon, lat + dlat], [lon, lat]]]}


def test_distanze():
    lotto = Lotto([quadrato(9.0, 45.0, 100)])
    # punto 200 m a est del bordo
    p = {"type": "Point", "coordinates": [9.0 + 300 / (111_320 * 0.7071), 45.0 + 50 / 111_150]}
    assert 180 < lotto.distanza(p) < 220
    assert lotto.distanza(quadrato(9.0003, 45.0003, 50)) == 0          # dentro il lotto
    assert lotto.distanza(quadrato(8.99, 44.99, 5000)) == 0            # il lotto è dentro l'oggetto
    linea = {"type": "LineString", "coordinates": [[8.99, 45.0 + 600 / 111_150], [9.01, 45.0 + 600 / 111_150]]}
    assert 480 < lotto.distanza(linea) < 520                           # linea 500 m a nord


def test_osm_logica(monkeypatch):
    lotto = Lotto([quadrato(9.0, 45.0, 100)])
    lon_e = lambda m: 9.0 + (100 + m) / (111_320 * 0.7071)  # noqa: E731  punto m metri a est del lotto
    finta = {"osm3s": {"timestamp_osm_base": "2026-11-20T10:00:00Z"}, "elements": [
        {"type": "way", "tags": {"power": "line", "voltage": "380000"},
         "geometry": [{"lat": 44.9, "lon": lon_e(1500)}, {"lat": 45.1, "lon": lon_e(1500)}]},
        {"type": "node", "tags": {"amenity": "school", "name": "Scuola prova"}, "lat": 45.0, "lon": lon_e(350)},
        {"type": "way", "tags": {"building": "house"}, "geometry": [{"lat": 45.0, "lon": lon_e(420)}, {"lat": 45.0001, "lon": lon_e(430)}]},
    ]}
    monkeypatch.setattr(K, "_overpass", lambda q: finta)
    e8, e10 = K.c8_c10_osm(lotto)
    assert e8["stato"] == "verde" and "1,5 km" in e8["valore"]
    assert e10["stato"] == "giallo"            # abitazioni < 500 m, scuola oltre 200 m
    finta["elements"][1]["lon"] = lon_e(150)   # scuola a 150 m → rosso
    assert K.c8_c10_osm(lotto)[1]["stato"] == "rosso"


def test_osm_non_raggiungibile_da_grigio(monkeypatch):
    def rotto(q):
        raise K.catasto.ErroreFonte("prova")
    monkeypatch.setattr(K, "_overpass", rotto)
    e8, e10 = K.c8_c10_osm(Lotto([quadrato(9.0, 45.0, 100)]))
    assert e8["stato"] == e10["stato"] == "grigio"


# ----------------- con rete -----------------

@pytest.fixture
def cache_temporanea(tmp_path, monkeypatch):
    monkeypatch.setattr(K.catasto, "CACHE_DIR", tmp_path)


def _novaceta():
    p = FIX / "novaceta_particelle.json"
    return json.loads(p.read_text())


def test_rete_novaceta(cache_temporanea, monkeypatch):
    monkeypatch.setattr(K, "_overpass", lambda q: (_ for _ in ()).throw(K.catasto.ErroreFonte("non provato qui")))
    r = K.controlla(_novaceta(), "E801")
    c = {x["id"]: x for x in r["criteri"]}
    assert r["comune"]["nome"] == "Magenta"
    assert c[4]["stato"] == "verde" and c[5]["stato"] == "verde"
    # dopo la taratura del 23/11/2026: siti tra 1 e 5 km → giallo (se il Geoportale risponde)
    assert c[11]["stato"] in ("giallo", "grigio")
    if c[11]["stato"] == "giallo":
        assert "Boschi della Fagiana" in c[11]["dettagli"][0]
    assert c[12]["stato"] == "verde" and "zona 4" in c[12]["valore"]
    assert c[3]["stato"] in ("verde", "giallo")
    assert c[8]["stato"] == "grigio" and c[9]["stato"] == "giallo"
    assert r["aiuti"]["c7"]["stato_proposto"] == "giallo"
    assert any("NOVACETA" in x for x in r["aiuti"]["c6"]["bonificati"])
    assert all(x["fonte"] and x["consultato_il"] for x in r["criteri"])


def test_rete_controlli_positivi(cache_temporanea):
    # riva del Lago di Como a Bellagio: fascia di rispetto dei laghi (art. 142 lett. b)
    assert K.c3_vincoli(Lotto([quadrato(9.2605, 45.9868, 60)]), "Lombardia")["stato"] in ("rosso", "giallo")
    # dentro il sito Natura 2000 Valle del Ticino / Boschi del Ticino
    assert K.c11_natura2000(Lotto([quadrato(8.795, 45.47, 80)]))["stato"] == "rosso"
    # alveo del Po: pericolosità idraulica elevata
    assert K.c4_c5_idrogeo(Lotto([quadrato(10.005, 45.114, 60)]))[0]["stato"] == "rosso"
    # L'Aquila: zona sismica 2
    assert K.c12_sismica(Lotto([quadrato(13.398, 42.3498, 60)]))["stato"] == "giallo"


def test_rete_ortofoto(cache_temporanea):
    from backend import ortofoto
    r = ortofoto.ortofoto(45.4660, 8.8710, 45.4680, 8.8740, 2012, 400)
    assert r["immagine"].startswith("data:image/jpeg;base64,/9j/")
    assert "2012" in (r["date_volo"] or "") and r["altezza"] > 100
    assert "2007" in (ortofoto.ortofoto(45.4660, 8.8710, 45.4680, 8.8740, 2006, 400)["date_volo"] or "")
