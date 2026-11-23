"""Test del backend. Il test di PVGIS fa una chiamata reale (connettore: un punto noto per fonte).

Avvio: python3 -m pytest tests/
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend import app as backend  # noqa: E402

client = TestClient(backend.app)


def test_pvgis_magenta(tmp_path, monkeypatch):
    # cache in una cartella temporanea: forza una chiamata reale a PVGIS
    monkeypatch.setattr(backend, "CACHE_DIR", tmp_path)
    r = client.get("/api/clima", params={"lat": 45.4670, "lon": 8.8736})
    assert r.status_code == 200
    d = r.json()
    assert len(d["ore"]) == 8760
    assert {"time(UTC)", "T2m", "RH"} <= set(d["ore"][0])
    assert d["fonte"].startswith("PVGIS") and d["scaricato_il"]
    assert d["da_cache"] is False
    assert sorted(d["anni"]) == [str(a) for a in range(2005, 2024)]
    assert all(len(v) == 8760 for v in d["anni"].values())
    # seconda chiamata: dalla cache
    assert client.get("/api/clima", params={"lat": 45.4670, "lon": 8.8736}).json()["da_cache"] is True


def test_pvgis_punto_in_mare_da_errore_chiaro(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "CACHE_DIR", tmp_path)
    r = client.get("/api/clima", params={"lat": 40.0, "lon": -30.0})  # Atlantico
    assert r.status_code == 502
    assert "PVGIS" in r.json()["detail"]


def test_coordinate_non_valide():
    assert client.get("/api/clima", params={"lat": 95, "lon": 9}).status_code == 422


def test_file_statici():
    assert client.get("/engine.js").status_code == 200
    assert client.get("/segreto.js").status_code == 404
