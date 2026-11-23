"""Backend locale del Passaporto Acqua e Calore.

Avvio:  uvicorn backend.app:app --reload    (dalla cartella del progetto)
Poi apri http://127.0.0.1:8000

Funzioni:
- GET /api/clima?lat=..&lon=..  anno meteorologico tipo orario PVGIS del punto, con cache su disco.
- serve la pagina del calcolatore (frontend/) e i file del motore (engine.js, dati.js, casi.js).
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache" / "pvgis"

# Endpoint verificato in Fase 0 (vedi FONTI.md §3). Le chiamate dal browser sono vietate da PVGIS:
# per questo passano da qui.
PVGIS_TMY_URL = "https://re.jrc.ec.europa.eu/api/v5_3/tmy"
PVGIS_SERIES_URL = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
PVGIS_FONTE = ("PVGIS 5.3 – Commissione europea, JRC: temperature orarie 2005–2023 (seriescalc) "
               "e umidità dall'anno meteorologico tipo (TMY)")
ANNO_INIZIO, ANNO_FINE = 2005, 2023  # periodo coperto da PVGIS 5.3 (ERA5)
USER_AGENT = "prefattibilita-dc/0.1"
TIMEOUT_S = 90

app = FastAPI(title="Passaporto Acqua e Calore")


def _cache_path(lat: float, lon: float, tipo: str = "tmy") -> Path:
    return CACHE_DIR / f"{tipo}_{lat:.3f}_{lon:.3f}.json"


def _chiama_pvgis(base_url: str, params: dict) -> dict:
    """Chiama PVGIS e restituisce il JSON originale. Solleva RuntimeError se il servizio non risponde."""
    url = base_url + "?" + urllib.parse.urlencode(dict(params, outputformat="json"))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # PVGIS risponde 400 con un messaggio quando il punto è fuori copertura (es. in mare)
        dettaglio = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"PVGIS ha risposto {e.code}: {dettaglio}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"PVGIS non raggiungibile: {e}") from e


def scarica_tmy(lat: float, lon: float) -> dict:
    return _chiama_pvgis(PVGIS_TMY_URL, {"lat": f"{lat:.4f}", "lon": f"{lon:.4f}"})


def anni_reali(lat: float, lon: float) -> dict:
    """Temperature orarie vere 2005–2023: {anno: [8760 valori]} (29 febbraio escluso), con cache."""
    lat, lon = round(lat, 3), round(lon, 3)
    path = _cache_path(lat, lon, "serie")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raw = _chiama_pvgis(PVGIS_SERIES_URL, {"lat": f"{lat:.4f}", "lon": f"{lon:.4f}",
                                           "startyear": ANNO_INIZIO, "endyear": ANNO_FINE})
    anni: dict[str, list] = {}
    for h in raw["outputs"]["hourly"]:
        t = h["time"]  # AAAAMMGG:hhmm in UTC
        if t[4:8] == "0229":
            continue
        anni.setdefault(t[:4], []).append(round(h["T2m"], 2))
    incompleti = [a for a, v in anni.items() if len(v) != 8760]
    if incompleti or len(anni) != ANNO_FINE - ANNO_INIZIO + 1:
        raise RuntimeError(f"Serie PVGIS incompleta (anni con ore mancanti: {incompleti})")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(anni), encoding="utf-8")
    return anni


def clima_tmy(lat: float, lon: float) -> dict:
    """Anno tipo PVGIS del punto (arrotondato a ~100 m), dalla cache se già scaricato."""
    lat, lon = round(lat, 3), round(lon, 3)
    path = _cache_path(lat, lon)
    if path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec["da_cache"] = True
        return rec
    raw = scarica_tmy(lat, lon)
    ore = raw["outputs"]["tmy_hourly"]
    if len(ore) != 8760:
        raise RuntimeError(f"PVGIS ha restituito {len(ore)} ore invece di 8760")
    meteo = raw["inputs"]["meteo_data"]
    rec = {
        "fonte": PVGIS_FONTE,
        "url": PVGIS_TMY_URL,
        "licenza": "uso libero, senza registrazione (manuale PVGIS); citare © European Union",
        "scaricato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "punto": {"lat": lat, "lon": lon, "quota_m": raw["inputs"]["location"].get("elevation")},
        "dati_meteo": f"{meteo.get('meteo_db')} {meteo.get('year_min')}–{meteo.get('year_max')}",
        "mesi_scelti": raw["outputs"].get("months_selected"),
        # solo i campi usati dal motore, con i nomi originali PVGIS
        "ore": [{"time(UTC)": h["time(UTC)"], "T2m": h["T2m"], "RH": h["RH"]} for h in ore],
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    rec["da_cache"] = False
    return rec


def clima_pvgis(lat: float, lon: float) -> dict:
    """Anno tipo (per l'umidità) + 19 anni di temperature reali."""
    rec = clima_tmy(lat, lon)
    rec["anni"] = anni_reali(lat, lon)
    rec["fonte"] = PVGIS_FONTE
    rec["url"] = f"{PVGIS_SERIES_URL} ; {PVGIS_TMY_URL}"
    return rec


@app.get("/api/clima")
def api_clima(lat: float = Query(..., ge=-60, le=70), lon: float = Query(..., ge=-180, le=180)):
    try:
        return clima_pvgis(lat, lon)
    except RuntimeError as e:
        # Il calcolatore mostra il messaggio e torna al clima sintetico ("da verificare")
        raise HTTPException(status_code=502, detail=str(e)) from e


# ---- file statici: pagina e motore di calcolo ----
@app.get("/")
def pagina():
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/{nome}.js")
def script(nome: str):
    if nome not in {"engine", "dati", "casi"}:
        raise HTTPException(status_code=404)
    return FileResponse(ROOT / f"{nome}.js", media_type="text/javascript")


# ---- Catasto: particelle (Fase 2) ----
from backend import catasto  # noqa: E402


def _catasto(fn, *args):
    try:
        return fn(*args)
    except catasto.NonTrovato as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except catasto.ErroreFonte as e:
        raise HTTPException(status_code=502, detail=f"{e} – criterio da verificare") from e


@app.get("/api/particella/punto")
def api_particella_punto(lat: float = Query(..., ge=35, le=48), lon: float = Query(..., ge=6, le=19)):
    return _catasto(catasto.particella_da_punto, lat, lon)


@app.get("/api/particelle/cerca")
def api_particelle_cerca(comune: str = Query(..., min_length=2), foglio: int = Query(..., ge=1, le=9999),
                         particelle: str = Query(..., description="numeri separati da virgola"),
                         provincia: str | None = Query(None, min_length=2, max_length=2)):
    lista = [p for p in (x.strip() for x in particelle.replace(";", ",").split(",")) if p]
    if not lista or len(lista) > 50:
        raise HTTPException(status_code=400, detail="Indica da 1 a 50 particelle")
    return _catasto(catasto.cerca_particelle, comune, foglio, lista, provincia)


@app.get("/api/particelle/riquadro")
def api_particelle_riquadro(s: float, w: float, n: float, e: float):
    return _catasto(catasto.particelle_in_riquadro, s, w, n, e)
