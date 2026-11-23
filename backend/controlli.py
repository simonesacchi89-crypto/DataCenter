"""Controlli automatici sul lotto (Fase 3): criteri 3, 4, 5, 8, 9, 10, 11, 12 e aiuti per 6 e 7.

Regole (CLAUDE.md): ogni risultato porta fonte e data; se una fonte non risponde o non copre l'area
il criterio è 'grigio' (da verificare), mai verde. Soglie da SPEC §4 (ipotesi iniziali da tarare).
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from backend import catasto
from backend.geo import Lotto

UA = "prefattibilita-dc/0.1"

# Endpoint verificati (FONTI.md)
SITAP_WFS = {"sitap_ws_clone": "https://sitap.cultura.gov.it/geoserver/sitap_ws_clone/wfs",
             "sitap_wms_bounce": "https://sitap.cultura.gov.it/geoserver/sitap_wms_bounce/wfs"}
PCN_WFS = "http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/wfs/{m}.map"
PCN_WMS_SISMICA = "http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/Classificazione_sismica_2012.map"
IDROGEO = "https://idrogeo.isprambiente.it/api/pir/verifica_pericolosita_at_point"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
LOMB_CONTAMINATI = "https://www.dati.lombardia.it/resource/npku-858g.json"
LOMB_BONIFICATI = "https://www.dati.lombardia.it/resource/macq-ggfu.json"
CMM_SOGGIACENZA = "https://www.dati.lombardia.it/resource/u3wq-chcr.json"

GML = "{http://www.opengis.net/gml}"


def _adesso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get(url, params=None, data=None, timeout=90, tentativi=3):
    full = url + (("&" if "?" in url else "?") + urllib.parse.urlencode(params) if params else "")
    body = urllib.parse.urlencode(data).encode() if data else None
    err = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(full, data=body, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            err = f"{full.split('/')[2]} ha risposto {e.code}"
            if e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = f"{full.split('/')[2]} non raggiungibile ({e})"
        time.sleep(1.5 * (t + 1))
    raise catasto.ErroreFonte(err)


def esito(id_, criterio, stato, valore, fonte, url, data_fonte=None, nota="", dettagli=None, domanda=None):
    return {"id": id_, "criterio": criterio, "stato": stato, "valore": valore, "fonte": fonte, "url": url,
            "data_fonte": data_fonte, "consultato_il": _adesso(), "nota": nota,
            "dettagli": dettagli or [], "domanda": domanda}


def grigio(id_, criterio, fonte, url, motivo, domanda=None):
    return esito(id_, criterio, "grigio", "da verificare", fonte, url, nota=motivo, domanda=domanda)


def _m(d):
    return f"{d:,.0f} m".replace(",", ".") if d < 1000 else f"{d / 1000:.1f} km".replace(".", ",")


# ---------------- lettori di formati ----------------

def _gml31_features(raw: bytes) -> list:
    """GML 3.1 di MapServer (Geoportale Nazionale): coordinate lat lon. Ritorna [(proprietà, geometria GeoJSON)]."""
    root = ET.fromstring(raw)
    out = []
    for fm in root.iter(f"{GML}featureMember"):
        feat = list(fm)[0]
        props = {c.tag.split("}")[1]: (c.text or "").strip() for c in feat
                 if not c.tag.startswith(GML) and len(c) == 0}
        polys = []
        for pg in feat.iter(f"{GML}Polygon"):
            rings = []
            for pl in pg.iter(f"{GML}posList"):
                v = [float(x) for x in pl.text.split()]
                rings.append([[v[i + 1], v[i]] for i in range(0, len(v), 2)])
            if rings:
                polys.append(rings)
        if polys:
            out.append((props, {"type": "MultiPolygon", "coordinates": polys}))
    return out


def _pcn_wfs(mappa, tipo, s, w, n, e):
    raw = _get(PCN_WFS.format(m=mappa), {"service": "WFS", "version": "1.1.0", "request": "GetFeature",
                                         "typeName": tipo, "maxFeatures": 500,
                                         "bbox": f"{s:.5f},{w:.5f},{n:.5f},{e:.5f},urn:ogc:def:crs:EPSG::4326"})
    if b"ExceptionReport" in raw[:500]:
        raise catasto.ErroreFonte("Geoportale Nazionale: richiesta rifiutata")
    return _gml31_features(raw)


# ---------------- criterio 3: vincoli paesaggistici e culturali ----------------

REGIONE_PREFISSO = {"Lombardia": "lombardia", "Lazio": "lazio", "Piemonte": "piemonte", "Veneto": "veneto",
                    "Emilia-Romagna": "emiliaromagna", "Toscana": "toscana", "Liguria": "liguria",
                    "Friuli-Venezia Giulia": "fvg", "Marche": "marche", "Umbria": "umbria", "Abruzzo": "abruzzo",
                    "Campania": "campania", "Puglia": "puglia", "Basilicata": "basilicata", "Calabria": "calabria",
                    "Sardegna": "sardegna"}
STRATI_NAZIONALI = ["Beni_monumentali_art_10_tutela_indiretta", "geo_aree_archeol_vincolate",
                    "unesco_official_2026_polygon_core", "unesco_official_2026_polygon_buffer"]
ESCLUSI = re.compile(r"dtm|dem|tinitaly|fiumi_base|art_?135|ambiti|alberi|geositi|PCN", re.I)


def _strati_sitap() -> dict:
    def produci():
        out = {}
        for ws, url in SITAP_WFS.items():
            raw = _get(url, {"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}).decode("utf-8", "replace")
            for nome in re.findall(rf"<Name>{ws}:([^<]+)</Name>", raw):
                out[nome] = ws
        return out
    return catasto._cache_json("sitap/strati.json", 7, produci)


def _etichetta_vincolo(props, strato):
    for k in ("DESC_SITAP", "DESC_DECR2", "NOME_LG", "nome_gazze", "denominazi", "DENOMINAZ", "NOME", "nome", "name",
              "site_name", "Denominazione", "DENOMINAZIONE"):
        if props.get(k):
            return str(props[k])[:160]
    return strato


NON_DICHIARATA = "non dichiarata dalla fonte"


def c3_vincoli(lotto: Lotto, regione: str):
    crit = "Vincoli paesaggistici e culturali (entro 500 m)"
    fonte = "MiC – SITAP (WFS) + Geoportale Nazionale MASE – EUAP (aree protette, art. 142 lett. f)"
    try:
        strati = _strati_sitap()
    except catasto.ErroreFonte as e:
        return grigio(3, crit, fonte, SITAP_WFS["sitap_ws_clone"], f"SITAP non risponde: {e}")
    pref = REGIONE_PREFISSO.get(regione)
    regionali = [s for s in strati if pref and s.lower().startswith(pref) and not ESCLUSI.search(s)]
    da_interrogare = regionali + [s for s in STRATI_NAZIONALI if s in strati]
    s, w, n, e = lotto.riquadro(600)
    trovati, errori = [], []
    for strato in da_interrogare:
        try:
            raw = _get(SITAP_WFS[strati[strato]], {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                                   "typeNames": f"{strati[strato]}:{strato}", "outputFormat": "application/json",
                                                   "srsName": "EPSG:4326", "count": 200, "bbox": f"{w},{s},{e},{n},EPSG:4326"})
            for f in json.loads(raw).get("features", []):
                if f.get("geometry"):
                    d = lotto.distanza(f["geometry"], 600)
                    if d <= 500:
                        trovati.append((d, strato, _etichetta_vincolo(f["properties"], strato)))
        except (catasto.ErroreFonte, ValueError) as ex:
            errori.append(f"{strato}: {ex}")
    try:  # parchi e riserve (art. 142 lett. f), che SITAP non ha per tutte le regioni
        for props, g in _pcn_wfs("EUAP", "SP.SITIPROTETTI.EUAP", s, w, n, e):
            d = lotto.distanza(g, 600)
            if d <= 500:
                trovati.append((d, "EUAP", f"{props.get('nome_gazze', 'area protetta')} ({props.get('tipo', '')})"))
    except catasto.ErroreFonte as ex:
        errori.append(f"EUAP: {ex}")
    trovati.sort()
    det = [f"{'dentro il lotto' if d == 0 else 'a ' + _m(d)}: {t} [{st}]" for d, st, t in trovati]
    nota = (f"Strati SITAP controllati: {len(da_interrogare)} ({regione or 'regione sconosciuta'}). "
            "SITAP ha valore solo informativo; non comprende i vincoli dei piani paesaggistici regionali né i pareri "
            "della Soprintendenza (es. altezze e skyline).")
    domanda = "Chiedere alla Soprintendenza e al Comune se sul lotto o nell'intorno ci sono vincoli o prescrizioni paesaggistiche."
    if errori:
        return esito(3, crit, "grigio", "da verificare", fonte, SITAP_WFS["sitap_ws_clone"], NON_DICHIARATA, nota=nota + " Errori: " + "; ".join(errori[:3]),
                     dettagli=det, domanda=domanda)
    if not regionali:
        return esito(3, crit, "grigio", "SITAP non ha strati regionali per " + (regione or "questa regione"), fonte,
                     SITAP_WFS["sitap_ws_clone"], nota=nota, dettagli=det, domanda=domanda)
    if any(d == 0 for d, _, _ in trovati):
        return esito(3, crit, "rosso", "lotto dentro un'area vincolata", fonte, SITAP_WFS["sitap_ws_clone"], NON_DICHIARATA, nota=nota, dettagli=det, domanda=domanda)
    if trovati:
        return esito(3, crit, "giallo", f"bene tutelato a {_m(trovati[0][0])}", fonte, SITAP_WFS["sitap_ws_clone"], NON_DICHIARATA, nota=nota, dettagli=det, domanda=domanda)
    return esito(3, crit, "verde", "nessun vincolo entro 500 m nei dati SITAP/EUAP", fonte, SITAP_WFS["sitap_ws_clone"], NON_DICHIARATA, nota=nota,
                 domanda=domanda)


# ---------------- criteri 4 e 5: ISPRA IdroGEO ----------------

def c4_c5_idrogeo(lotto: Lotto):
    lon, lat = lotto.centro
    r = int(min(500, max(30, lotto.raggio)))
    fonte, url = "ISPRA – IdroGEO (mosaicature nazionali pericolosità)", IDROGEO
    try:
        d = json.loads(_get(IDROGEO, {"center_wkt": f"POINT({lon:.6f} {lat:.6f})", "radius_meter": r}))
    except (catasto.ErroreFonte, ValueError) as e:
        return [grigio(4, "Pericolosità idraulica", fonte, url, str(e)), grigio(5, "Frane", fonte, url, str(e))]
    area = f"cerchio di {r} m dal centro del lotto (comprende il lotto{'' if lotto.raggio <= 500 else ' solo in parte'})"
    # Caso Bornasco (23/11/2026): rogge che attraversano il sito, non presenti nella mosaicatura ISPRA.
    reticolo = (" La mosaicatura ISPRA non comprende il reticolo idrico minore (rogge, canali, fontanili): "
                "verificare lo studio del reticolo minore e la componente geologica del PGT.")
    estr = (d.get("extraction_on") or "")[:10]
    data = NON_DICHIARATA
    area += f"; estrazione ISPRA del {estr}" if estr else ""
    idr = sorted({str(x) for x in (d.get("pericolosita_idraulica") or [])})
    # codici 1/2/3 = scenari P1/P2/P3 (dedotto dai punti di controllo, FONTI.md §4)
    if not idr:
        e4 = esito(4, "Pericolosità idraulica", "verde", "nessuna area a pericolosità", fonte, url, data, f"Area controllata: {area}." + reticolo)
    else:
        top = max(int(x) for x in idr if x.isdigit())
        stato = {1: "verde", 2: "giallo", 3: "rosso"}.get(top, "grigio")
        e4 = esito(4, "Pericolosità idraulica", stato, "scenari presenti: " + ", ".join("P" + x for x in idr), fonte, url, data,
                   f"Area controllata: {area}. Codici ISPRA interpretati come P1 bassa, P2 media, P3 elevata." + reticolo,
                   domanda="Verificare sul PGRA/PAI dell'autorità di distretto la pericolosità esatta sul lotto." if top >= 2 else None)
    fr = d.get("pericolosita_frane")
    if not fr:
        e5 = esito(5, "Frane", "verde", "nessuna area a pericolosità da frana", fonte, url, data, f"Area controllata: {area}.")
    else:
        e5 = esito(5, "Frane", "grigio", "presenti aree a pericolosità (codici " + ", ".join(map(str, fr)) + ")", fonte, url, data,
                   "Il significato dei codici di classe non è documentato dall'API: da verificare.",
                   domanda="Verificare sul PAI la classe di pericolosità da frana (P1–P4) che interessa il lotto.")
    return [e4, e5]


# ---------------- criterio 11: Natura 2000 ----------------

def c11_natura2000(lotto: Lotto):
    crit, fonte = "Aree Natura 2000 (entro 5 km)", "Geoportale Nazionale MASE – SIC/ZSC/ZPS (WFS)"
    url = PCN_WFS.format(m="SIC_ZSC_ZPS")
    try:
        feats = _pcn_wfs("SIC_ZSC_ZPS", "SP.SITIPROTETTI.SIC_ZSC_ZPS", *lotto.riquadro(5000))
    except (catasto.ErroreFonte, ET.ParseError) as e:
        return grigio(11, crit, fonte, url, str(e))
    siti = sorted((lotto.distanza(g, 5000), p.get("site_code", ""), p.get("denominazi", ""), p.get("aggiorn", ""))
                  for p, g in feats)
    siti = [x for x in siti if x[0] <= 5000]
    det = [f"{'dentro il lotto' if d == 0 else _m(d)}: {c} {n} (aggiornamento {a[:4]}-{a[4:]})" for d, c, n, a in siti]
    agg = max((a for *_, a in siti), default=None)
    agg = f"{agg[:4]}-{agg[4:]} (aggiornamento più recente dei siti vicini)" if agg and len(agg) == 6 else agg
    if siti and siti[0][0] == 0:
        return esito(11, crit, "rosso", "lotto dentro un sito Natura 2000", fonte, url, agg, dettagli=det,
                     domanda="Serve la Valutazione di incidenza appropriata: chiedere all'ente gestore.")
    # Taratura del 23/11/2026 (CASI_TEST.md): a Magenta (3,4 km) e Liscate (3,8 km) lo screening di incidenza
    # è stato chiesto anche oltre 1 km. Soglia del giallo portata da 1 a 5 km (SPEC indicava 1 km).
    domanda = "Chiedere all'ente gestore se è richiesta la Valutazione di incidenza (screening)."
    if siti and siti[0][0] <= 1000:
        return esito(11, crit, "giallo", f"sito a {_m(siti[0][0])}", fonte, url, agg, "Entro 1 km: screening di incidenza quasi certo.",
                     det, domanda)
    if siti:
        return esito(11, crit, "giallo", f"sito a {_m(siti[0][0])} (entro 5 km)", fonte, url, agg,
                     "Tra 1 e 5 km lo screening di incidenza è spesso richiesto (casi Magenta 3,4 km e Liscate 3,8 km).", det, domanda)
    return esito(11, crit, "verde", "nessun sito entro 5 km", fonte, url, agg, "", det)


# ---------------- criterio 12: sismica ----------------

def c12_sismica(lotto: Lotto):
    lon, lat = lotto.centro
    crit, fonte = "Sismicità (classificazione comunale)", "Geoportale Nazionale MASE – Classificazione sismica dei comuni al 2012"
    d = 0.001
    try:
        t = _get(PCN_WMS_SISMICA, {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
                                   "LAYERS": "RN.ZONERISCHIO.CLASSIFICAZIONESISMICA", "QUERY_LAYERS": "RN.ZONERISCHIO.CLASSIFICAZIONESISMICA",
                                   "STYLES": "", "CRS": "EPSG:4326", "BBOX": f"{lat - d},{lon - d},{lat + d},{lon + d}",
                                   "WIDTH": 101, "HEIGHT": 101, "I": 50, "J": 50, "INFO_FORMAT": "text/plain"}).decode("utf-8", "replace")
    except catasto.ErroreFonte as e:
        return grigio(12, crit, fonte, PCN_WMS_SISMICA, str(e))
    m = re.search(r"classificazione = '([^']*)'", t)
    if not m:
        return grigio(12, crit, fonte, PCN_WMS_SISMICA, "Nessun dato per questo punto")
    cl = m.group(1)
    com = re.search(r"comune = '([^']*)'", t)
    delib = re.search(r"normativa = '([^']*)'.*?numero = '([^']*)'.*?data = '([^']*)'", t, re.S)
    z = int(cl[0]) if cl[:1].isdigit() else 0
    stato = {1: "rosso", 2: "giallo", 3: "verde", 4: "verde"}.get(z, "grigio")
    return esito(12, crit, stato, f"zona {cl}" + (f" ({com.group(1).title()})" if com else ""), fonte, PCN_WMS_SISMICA, "2012",
                 "Dato nazionale al 2012" + (f"; atto: {delib.group(1)} n. {delib.group(2)} del {delib.group(3)}" if delib else "")
                 + ". Alcune regioni hanno riclassificato dopo il 2012: verificare la delibera regionale vigente.",
                 domanda="Verificare la zona sismica vigente nella delibera regionale più recente.")


# ---------------- criteri 8 e 10: OpenStreetMap (Overpass) ----------------

def _overpass(q: str) -> dict:
    err = None
    for url in OVERPASS:
        try:
            return json.loads(_get(url, data={"data": q}, timeout=40, tentativi=1))
        except (catasto.ErroreFonte, ValueError) as e:
            err = e
    raise catasto.ErroreFonte(f"Overpass non raggiungibile ({err})")


def _osm_geom(el) -> dict | None:
    if el.get("type") == "node":
        return {"type": "Point", "coordinates": [el["lon"], el["lat"]]}
    if "geometry" in el:
        return {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in el["geometry"] if p]}
    if "members" in el:
        linee = [[[p["lon"], p["lat"]] for p in m["geometry"]] for m in el["members"] if m.get("geometry")]
        return {"type": "MultiLineString", "coordinates": linee} if linee else None
    if "center" in el:
        return {"type": "Point", "coordinates": [el["center"]["lon"], el["center"]["lat"]]}
    return None


def c8_c10_osm(lotto: Lotto):
    fonte, url = "OpenStreetMap (Overpass API) – © OpenStreetMap contributors, ODbL", OVERPASS[0]
    s, w, n, e = lotto.riquadro(10000)
    s5, w5, n5, e5 = lotto.riquadro(500)
    q = (f"[out:json][timeout:80];("
         f'way["power"="line"]["voltage"~"(1[3-9][0-9]|[2-9][0-9][0-9])[0-9]{{3}}"]({s},{w},{n},{e});'
         f'nwr["power"="substation"]["voltage"~"(1[3-9][0-9]|[2-9][0-9][0-9])[0-9]{{3}}"]({s},{w},{n},{e});'
         f'nwr["amenity"~"^(school|kindergarten|hospital)$"]({s5},{w5},{n5},{e5});'
         f'nwr["healthcare"="hospital"]({s5},{w5},{n5},{e5});'
         f'way["building"~"^(house|residential|apartments|detached|semidetached_house|terrace)$"]({s5},{w5},{n5},{e5});'
         f'way["landuse"="residential"]({s5},{w5},{n5},{e5});'
         f");out geom;")
    domanda8 = "Chiedere a Terna (richiesta formale) la soluzione di connessione e la distanza dalla stazione utile."
    try:
        d = _overpass(q)
    except catasto.ErroreFonte as ex:
        msg = (f"{ex}. Overpass non ha risposto (da questo ambiente cloud è bloccato o sovraccarico): "
               "riprovare più tardi o dal computer locale.")
        return [grigio(8, "Distanza dalla rete ad alta tensione", fonte, url, msg, domanda8),
                grigio(10, "Vicini sensibili", fonte, url, msg,
                       "Verificare con il Comune se entro 500 m ci sono abitazioni ed entro 200 m scuole o ospedali.")]
    data = (d.get("osm3s") or {}).get("timestamp_osm_base")
    linee, stazioni, sens, abit = [], [], [], []
    for el in d.get("elements", []):
        t, g = el.get("tags", {}), _osm_geom(el)
        if not g:
            continue
        if t.get("power") == "line":
            linee.append((lotto.distanza(g, 10000), t.get("voltage", ""), t.get("name") or t.get("operator") or "linea"))
        elif t.get("power") == "substation":
            stazioni.append((lotto.distanza(g, 10000), t.get("voltage", ""), t.get("name") or t.get("operator") or "stazione"))
        elif t.get("amenity") in ("school", "kindergarten", "hospital") or t.get("healthcare") == "hospital":
            sens.append((lotto.distanza(g, 500), t.get("amenity") or "hospital", t.get("name", "")))
        else:
            abit.append((lotto.distanza(g, 500), t.get("building") or "area residenziale"))
    kv = lambda v: "/".join(str(int(x) // 1000) for x in v.split(";") if x.isdigit()) + " kV"  # noqa: E731
    near = sorted(linee + stazioni)
    det8 = [f"{_m(dd)}: {'stazione' if (dd, v, nm) in stazioni else 'linea'} {kv(v)} {nm}" for dd, v, nm in near[:6]]
    if not near:
        e8 = esito(8, "Distanza dalla rete ad alta tensione", "rosso", "nessuna linea o stazione ≥132 kV entro 10 km", fonte, url, data,
                   "Mappatura OSM: può essere incompleta.", domanda=domanda8)
    else:
        dmin = near[0][0]
        stato = "verde" if dmin < 2000 else "giallo" if dmin <= 10000 else "rosso"
        e8 = esito(8, "Distanza dalla rete ad alta tensione", stato, f"{_m(dmin)} dall'elemento ≥132 kV più vicino", fonte, url, data,
                   "Mappatura OSM (non ufficiale Terna). La capacità disponibile la conosce solo Terna.", det8, domanda8)
    sens.sort(); abit.sort()
    det10 = [f"{_m(dd)}: {a} {nm}" for dd, a, nm in sens[:5]] + ([f"abitazioni a {_m(abit[0][0])}"] if abit else [])
    if any(dd < 200 for dd, *_ in sens):
        e10 = esito(10, "Vicini sensibili", "rosso", f"scuola o ospedale a {_m(sens[0][0])}", fonte, url, data, dettagli=det10,
                    domanda="Verificare con il Comune i vincoli di distanza da scuole e ospedali (rumore, generatori).")
    elif abit and abit[0][0] < 500:
        e10 = esito(10, "Vicini sensibili", "giallo", f"abitazioni a {_m(abit[0][0])}", fonte, url, data,
                    "Edifici residenziali OSM: copertura variabile.", det10,
                    domanda="Chiedere al Comune la classificazione acustica e i limiti per i generatori di emergenza.")
    else:
        e10 = esito(10, "Vicini sensibili", "verde", "nessuna abitazione entro 500 m nei dati OSM", fonte, url, data,
                    "Edifici residenziali OSM: copertura variabile.", det10)
    return [e8, e10]


# ---------------- criterio 9: capacità di connessione ----------------

def c9_terna():
    return esito(9, "Capacità di connessione", "giallo", "da chiedere a Terna", "Terna – richiesta formale di connessione",
                 "https://www.terna.it", None, "La capacità disponibile non è pubblica: si conosce solo con la richiesta a Terna.",
                 domanda="Presentare a Terna la richiesta di connessione (STMG) per la potenza prevista.")


# ---------------- aiuti per i criteri 6 e 7 (inserimento manuale) ----------------

def aiuto_c6_c7(lotto: Lotto, comune: dict | None):
    aiuti = {}
    lon, lat = lotto.centro
    if comune and comune.get("regione") == "Lombardia":
        w = {"$where": f"upper(comune) = '{comune['nome'].upper().replace(chr(39), chr(39) * 2)}'"}
        try:
            a = json.loads(_get(LOMB_CONTAMINATI, w)); b = json.loads(_get(LOMB_BONIFICATI, w))
            aiuti["c6"] = {"fonte": "Regione Lombardia – Elenco siti contaminati e bonificati (dati.lombardia.it, CC0), dati al 31/12/2023",
                           "url": LOMB_CONTAMINATI,
                           "contaminati": [f"{r.get('denominazione_sito')} – {r.get('indirizzo', '')} ({r.get('cod_agisco')})" for r in a],
                           "bonificati": [f"{r.get('denominazione_sito')} – {r.get('indirizzo', '')} ({r.get('cod_agisco')})" for r in b],
                           "nota": "Elenchi senza confini: confrontare gli indirizzi con il lotto. Scegliere il semaforo a mano."}
        except catasto.ErroreFonte as e:
            aiuti["c6"] = {"errore": str(e)}
        try:
            r = json.loads(_get(CMM_SOGGIACENZA, {"$where": f"intersects(the_geom, 'POINT ({lon:.6f} {lat:.6f})')",
                                                  "$select": "soggiacenz,classe"}))
            if r:
                cls = r[0]["classe"]
                nums = [float(x.replace(",", ".")) for x in re.findall(r"[\d,]+", cls)]
                lo = min(nums) if nums else None
                stato = "grigio" if lo is None else "rosso" if max(nums) <= 5 else "verde" if lo >= 8 else "giallo"
                aiuti["c7"] = {"fonte": "Città Metropolitana di Milano – Soggiacenza indicativa marzo 2022 (CC0)", "url": CMM_SOGGIACENZA,
                               "classe": cls, "stato_proposto": stato,
                               "nota": "Dato indicativo; le oscillazioni stagionali (circa 2 m) vanno verificate con piezometri."}
        except catasto.ErroreFonte:
            pass
    return aiuti


# ---------------- tutto insieme ----------------

def _chiave(geometrie, codice_comune) -> str:
    import hashlib
    return hashlib.sha1(json.dumps([geometrie, codice_comune], sort_keys=True).encode()).hexdigest()[:16]


def controlla(geometrie: list, codice_comune: str | None = None) -> dict:
    """Esegue i controlli. Gli esiti riusciti (non grigi) restano in cache un giorno; i grigi si riprovano."""
    from pathlib import Path
    path = catasto.CACHE_DIR / "controlli" / f"{_chiave(geometrie, codice_comune)}.json"
    vecchio = {}
    if path.exists() and time.time() - path.stat().st_mtime < 86400:
        vecchio = {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["criteri"] if c["stato"] != "grigio"}
    ris = _controlla(geometrie, codice_comune, vecchio)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ris, ensure_ascii=False), encoding="utf-8")
    return ris


def _controlla(geometrie: list, codice_comune: str | None, gia: dict) -> dict:
    lotto = Lotto(geometrie)
    comune = None
    if codice_comune:
        comune = next((c for c in catasto.elenco_comuni() if c["codice_catastale"] == codice_comune), None)
    regione = comune["regione"] if comune else None
    def gia_o(ids, fn, *a):
        if all(i in gia for i in ids):
            return (lambda: [gia[i] for i in ids] if len(ids) > 1 else gia[ids[0]])
        return lambda: fn(*a)
    lavori = {"c3": gia_o([3], c3_vincoli, lotto, regione), "c45": gia_o([4, 5], c4_c5_idrogeo, lotto),
              "c11": gia_o([11], c11_natura2000, lotto), "c12": gia_o([12], c12_sismica, lotto),
              "osm": gia_o([8, 10], c8_c10_osm, lotto), "aiuti": lambda: aiuto_c6_c7(lotto, comune)}
    with ThreadPoolExecutor(max_workers=6) as ex:
        fut = {k: ex.submit(f) for k, f in lavori.items()}
        ris = {k: f.result() for k, f in fut.items()}
    criteri = [ris["c3"], *ris["c45"], ris["osm"][0], c9_terna(), ris["osm"][1], ris["c11"], ris["c12"]]
    criteri.sort(key=lambda c: c["id"])
    return {"comune": comune, "centro": {"lon": lotto.centro[0], "lat": lotto.centro[1]}, "raggio_m": round(lotto.raggio),
            "criteri": criteri, "aiuti": ris["aiuti"], "consultato_il": _adesso()}
