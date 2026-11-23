"""Connettore Catasto (Agenzia delle Entrate, WFS) + elenco comuni ISTAT + riquadro comune (Nominatim).

Endpoint verificati in Fase 0 e Fase 2 (vedi FONTI.md):
- WFS catasto: parametri in minuscolo, bbox in ordine lat,lon (EPSG:6706), GML 3.2.
  Non accetta filtri per codice: per cercare foglio e particella si passa da riquadri.
- Elenco comuni ISTAT (CSV, Latin-1, separatore ';'): nome -> codice catastale (es. Magenta -> E801).
- Nominatim (OpenStreetMap): riquadro del comune. Massimo 1 richiesta al secondo, con cache.
Nessun dato sui proprietari: il servizio non li contiene e qui non vengono mai cercati.
"""
import csv
import io
import json
import math
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"

WFS_URL = "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php"
ISTAT_URL = "https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "prefattibilita-dc/0.1"
TIMEOUT_S = 120

FONTE_CATASTO = "Agenzia delle Entrate – Cartografia catastale (WFS INSPIRE)"
LICENZA_CATASTO = "CC BY 4.0 – © Agenzia delle Entrate"
NOTA_SUPERFICIE = ("Superficie grafica calcolata dal confine della mappa catastale: "
                   "può differire dalla superficie catastale ufficiale.")
CACHE_GIORNI = 7          # il catasto si aggiorna ogni sei mesi; una settimana di cache basta
LATO_MAX_GRADI = 0.02     # riquadro massimo per le particelle visibili (~2 km)

NS = {"gml": "http://www.opengis.net/gml/3.2", "CP": "http://mapserver.gis.umn.edu/mapserver",
      "wfs": "http://www.opengis.net/wfs/2.0"}


class ErroreFonte(RuntimeError):
    """La fonte non risponde o non copre l'area: il criterio diventa 'da verificare'."""


class NonTrovato(LookupError):
    """La richiesta è valida ma non c'è un risultato (es. particella inesistente)."""


# ---------------- utilità di rete e cache ----------------

def _get(url: str, params: dict, timeout: int = TIMEOUT_S) -> bytes:
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise ErroreFonte(f"{url.split('/')[2]} ha risposto {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise ErroreFonte(f"{url.split('/')[2]} non raggiungibile: {e}") from e


def _cache_json(nome: str, giorni: float, produci):
    path = CACHE_DIR / nome
    if path.exists() and time.time() - path.stat().st_mtime < giorni * 86400:
        return json.loads(path.read_text(encoding="utf-8"))
    val = produci()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(val, ensure_ascii=False), encoding="utf-8")
    return val


def _adesso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------- geometria ----------------

def _anello(pos_list: str) -> list:
    v = [float(x) for x in pos_list.split()]
    return [[v[i + 1], v[i]] for i in range(0, len(v), 2)]  # GML lat,lon -> GeoJSON lon,lat


def _area_anello(coords: list, lat0: float) -> float:
    """Area in m² su piano tangente locale con raggi dell'ellissoide WGS84 (errore trascurabile per un lotto)."""
    a, e2 = 6378137.0, 6.69437999014e-3
    s = math.sin(math.radians(lat0))
    n = a / math.sqrt(1 - e2 * s * s)                 # raggio di curvatura primo verticale
    m = a * (1 - e2) / (1 - e2 * s * s) ** 1.5        # raggio di curvatura del meridiano
    kx, ky = math.radians(1) * n * math.cos(math.radians(lat0)), math.radians(1) * m
    xy = [(lon * kx, lat * ky) for lon, lat in coords]
    return abs(sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1))) / 2


def area_m2(geom: dict) -> float:
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    lat0 = polys[0][0][0][1]
    return sum(_area_anello(p[0], lat0) - sum(_area_anello(h, lat0) for h in p[1:]) for p in polys)


def _dentro(lon: float, lat: float, geom: dict) -> bool:
    def in_anello(r):
        c = False
        for i in range(len(r) - 1):
            (x1, y1), (x2, y2) = r[i], r[i + 1]
            if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                c = not c
        return c
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return any(in_anello(p[0]) and not any(in_anello(h) for h in p[1:]) for p in polys)


def _geometria(elem) -> dict | None:
    polys = []
    for pg in elem.iter(f"{{{NS['gml']}}}Polygon"):
        ext = pg.find("gml:exterior//gml:posList", NS)
        if ext is None:
            continue
        rings = [_anello(ext.text)] + [_anello(i.text) for i in pg.findall("gml:interior//gml:posList", NS)]
        polys.append(rings)
    if not polys:
        return None
    return {"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1 else \
        {"type": "MultiPolygon", "coordinates": polys}


# ---------------- WFS catasto ----------------

COUNT_WFS = 1000     # in prova (23/11/2026) count=5000 viene rifiutato ("Richiesta non valida"), 4999 no
LATO_WFS_MAX = 0.05  # gradi. Limite trovato in prova (23/11/2026): oltre ~0,07° il WFS risponde
                     # numberMatched="unknown" e 0 oggetti, senza errore. Si lavora a tessere più piccole.


def _wfs(tipo: str, s: float, w: float, n: float, e: float, profondita: int = 0) -> list:
    """Tutti gli oggetti del tipo nel riquadro. Divide il riquadro se è troppo grande o se il servizio
    restituisce meno oggetti di quelli trovati (o risponde 'unknown')."""
    if n - s > LATO_WFS_MAX or e - w > LATO_WFS_MAX:
        ny, nx = math.ceil((n - s) / LATO_WFS_MAX), math.ceil((e - w) / LATO_WFS_MAX)
        dy, dx = (n - s) / ny, (e - w) / nx
        out, visti = [], set()
        for i in range(ny):
            for j in range(nx):
                for f in _wfs(tipo, s + i * dy, w + j * dx, s + (i + 1) * dy, w + (j + 1) * dx, profondita):
                    if f["id"] not in visti:
                        visti.add(f["id"]); out.append(f)
        return out
    params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
              "typeNames": tipo, "count": COUNT_WFS, "bbox": f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"}
    # In prova il servizio a volte risponde "Richiesta non valida" a una richiesta corretta,
    # che ripetuta poco dopo funziona: 4 tentativi con pause crescenti, poi riquadri più piccoli.
    root = None
    for tentativo in range(4):
        try:
            r = ET.fromstring(_get(WFS_URL, params))
            if not r.tag.endswith("ServiceExceptionReport"):
                root = r
                break
            errore = "Il catasto ha rifiutato la richiesta: " + "".join(r.itertext()).strip()[:200]
        except (ErroreFonte, ET.ParseError) as ex:
            errore = f"Il catasto non ha risposto correttamente: {ex}"
        if tentativo < 3:
            time.sleep(2 ** tentativo)
    if root is None and profondita >= 3:
        raise ErroreFonte(errore + " (da verificare)")
    if root is None:
        matched, n_ret, da_dividere = "", 0, True
    else:
        matched, returned = root.get("numberMatched") or "", root.get("numberReturned") or "0"
        n_ret = int(returned) if returned.isdigit() else 0
        da_dividere = (matched == "unknown" and n_ret == 0) or n_ret >= COUNT_WFS or \
                      (matched.isdigit() and int(matched) > n_ret)
    if da_dividere and profondita >= 4:
        raise ErroreFonte("Il catasto non restituisce tutti gli oggetti di quest'area: da verificare.")
    if da_dividere:
        cl, cw = (s + n) / 2, (w + e) / 2
        out, visti = [], set()
        for q in [(s, w, cl, cw), (s, cw, cl, e), (cl, w, n, cw), (cl, cw, n, e)]:
            for f in _wfs(tipo, *q, profondita=profondita + 1):
                if f["id"] not in visti:
                    visti.add(f["id"]); out.append(f)
        return out
    out = []
    for mem in root.findall("wfs:member", NS):
        feat = list(mem)[0]
        props = {c.tag.split("}")[1]: (c.text or "") for c in feat if c.tag.startswith(f"{{{NS['CP']}}}")
                 and c.tag.split("}")[1] != "msGeometry"}
        geom = _geometria(feat)
        ref = props.get("NATIONALCADASTRALREFERENCE") or props.get("NATIONALCADASTRALZONINGREFERENCE")
        if geom and ref:
            out.append({"id": ref, "props": props, "geometry": geom})
    return out


def _scomponi(ref: str) -> dict:
    """'E801_000400.211' -> comune E801, foglio 4, allegato '0', sviluppo '0', particella '211'."""
    m = re.fullmatch(r"([A-Z]\d{3})_(\d{4})(\w)(\w)(?:\.(.+))?", ref)
    if not m:
        return {"riferimento": ref}
    return {"riferimento": ref, "codice_comune": m.group(1), "foglio": int(m.group(2)),
            "allegato": m.group(3), "sviluppo": m.group(4), "particella": m.group(5)}


def _particella(f: dict, foglio_aggiornato: str | None = None) -> dict:
    d = _scomponi(f["id"])
    d.update({"geometry": f["geometry"], "superficie_m2": round(area_m2(f["geometry"]), 1),
              "foglio_aggiornato_al": foglio_aggiornato})
    return d


def _meta() -> dict:
    return {"fonte": FONTE_CATASTO, "url": WFS_URL, "licenza": LICENZA_CATASTO,
            "consultato_il": _adesso(), "nota": NOTA_SUPERFICIE}


def _fogli_attorno(lat: float, lon: float) -> dict:
    d = 0.0002
    return {f["id"]: f["props"].get("BEGINLIFESPANVERSION") for f in _wfs("CP:CadastralZoning", lat - d, lon - d, lat + d, lon + d)}


def particella_da_punto(lat: float, lon: float) -> dict:
    def produci():
        d = 0.0003
        feats = _wfs("CP:CadastralParcel", lat - d, lon - d, lat + d, lon + d)
        scelte = [f for f in feats if _dentro(lon, lat, f["geometry"])]
        if not scelte:
            return None
        fogli = _fogli_attorno(lat, lon)
        f = scelte[0]
        return _particella(f, fogli.get(f["id"].split(".")[0]))
    p = _cache_json(f"catasto/punto_{lat:.6f}_{lon:.6f}.json", CACHE_GIORNI, produci)
    if p is None:
        raise NonTrovato("Nessuna particella in questo punto (strada, acqua, fuori copertura, oppure Trento e Bolzano, "
                         "dove il catasto è gestito dalle Province autonome).")
    return {**_meta(), "particelle": [p]}


def particelle_in_riquadro(s: float, w: float, n: float, e: float) -> dict:
    if n - s > LATO_MAX_GRADI or e - w > LATO_MAX_GRADI or n <= s or e <= w:
        raise ValueError("Riquadro troppo grande: avvicina la mappa (lato massimo circa 2 km).")
    key = f"catasto/riquadro_{s:.4f}_{w:.4f}_{n:.4f}_{e:.4f}.json"
    feats = _cache_json(key, CACHE_GIORNI, lambda: [_particella(f) for f in _wfs("CP:CadastralParcel", s, w, n, e)])
    return {**_meta(), "particelle": feats}


# ---------------- comuni (ISTAT) e riquadro comune (Nominatim) ----------------

def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def elenco_comuni() -> list:
    def produci():
        testo = _get(ISTAT_URL, {}).decode("latin-1")
        righe = list(csv.reader(io.StringIO(testo), delimiter=";"))
        h = [x.replace("\n", " ").strip() for x in righe[0]]
        i_nome, i_sigla = h.index("Denominazione in italiano"), h.index("Sigla automobilistica")
        i_cat, i_istat, i_reg = h.index("Codice Catastale del comune"), h.index("Codice Comune formato alfanumerico"), \
            h.index("Denominazione Regione")
        return [{"nome": r[i_nome], "sigla": r[i_sigla], "codice_catastale": r[i_cat], "istat": r[i_istat],
                 "regione": r[i_reg]} for r in righe[1:] if len(r) > i_cat and r[i_cat]]
    return _cache_json("istat/comuni.json", 30, produci)


def trova_comune(nome: str, provincia: str | None = None) -> dict:
    n = _norm(nome)
    cand = [c for c in elenco_comuni() if _norm(c["nome"]) == n]
    if provincia:
        cand = [c for c in cand if c["sigla"].upper() == provincia.strip().upper()]
    if not cand:
        raise NonTrovato(f"Comune '{nome}' non trovato nell'elenco ISTAT" + (f" in provincia {provincia}" if provincia else ""))
    if len(cand) > 1:
        raise NonTrovato(f"Ci sono più comuni chiamati '{nome}': indica la provincia ("
                         + ", ".join(c["sigla"] for c in cand) + ")")
    c = cand[0]
    if c["regione"].startswith("Trentino"):
        sig = c["sigla"]
        if sig in ("TN", "BZ"):
            raise ErroreFonte("Nelle Province di Trento e Bolzano il catasto non è dell'Agenzia delle Entrate: da verificare.")
    return c


_ultima_nominatim = [0.0]


def riquadro_comune(c: dict) -> list:
    def produci():
        attesa = 1.1 - (time.time() - _ultima_nominatim[0])  # regola d'uso: max 1 richiesta al secondo
        if attesa > 0:
            time.sleep(attesa)
        _ultima_nominatim[0] = time.time()
        raw = _get(NOMINATIM_URL, {"q": f"{c['nome']}, {c['sigla']}, Italia", "format": "json", "limit": 5,
                                   "featureType": "settlement"}, timeout=30)
        res = [r for r in json.loads(raw) if r.get("osm_type") == "relation"] or json.loads(raw)
        if not res:
            raise ErroreFonte(f"Confini del comune {c['nome']} non trovati su OpenStreetMap")
        s, n, w, e = (float(x) for x in res[0]["boundingbox"])
        return [s, w, n, e]
    return _cache_json(f"nominatim/{c['codice_catastale']}.json", 180, produci)


def _fogli_del_comune(c: dict) -> list:
    def produci():
        s, w, n, e = riquadro_comune(c)
        m = 0.01  # margine: il riquadro OSM può essere più stretto dei fogli catastali
        fogli = [f for f in _wfs("CP:CadastralZoning", s - m, w - m, n + m, e + m)
                 if f["id"].startswith(c["codice_catastale"] + "_")]
        return [{"id": f["id"], "aggiornato": f["props"].get("BEGINLIFESPANVERSION"), "geometry": f["geometry"]}
                for f in fogli]
    return _cache_json(f"catasto/fogli_{c['codice_catastale']}.json", CACHE_GIORNI, produci)


def _bbox(geom: dict) -> tuple:
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    pts = [p for poly in polys for p in poly[0]]
    return (min(p[1] for p in pts), min(p[0] for p in pts), max(p[1] for p in pts), max(p[0] for p in pts))


def cerca_particelle(comune: str, foglio: int, particelle: list, provincia: str | None = None) -> dict:
    c = trova_comune(comune, provincia)
    fogli = [f for f in _fogli_del_comune(c) if _scomponi(f["id"]).get("foglio") == foglio]
    if not fogli:
        raise NonTrovato(f"Foglio {foglio} non trovato nel comune di {c['nome']} ({c['codice_catastale']})")
    cercate = {str(p).strip().upper() for p in particelle}
    trovate = {}
    for fg in fogli:
        s, w, n, e = _bbox(fg["geometry"])
        key = f"catasto/foglio_{fg['id']}.json"
        feats = _cache_json(key, CACHE_GIORNI, lambda: [_particella(f, fg["aggiornato"])
                                                         for f in _wfs("CP:CadastralParcel", s, w, n, e)
                                                         if f["id"].startswith(fg["id"] + ".")])
        for p in feats:
            if p.get("particella", "").upper() in cercate:
                trovate[p["riferimento"]] = p
    mancanti = sorted(cercate - {p["particella"].upper() for p in trovate.values()})
    return {**_meta(), "comune": c, "fogli": [f["id"] for f in fogli],
            "particelle": list(trovate.values()), "non_trovate": mancanti}
