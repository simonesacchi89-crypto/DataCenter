"""Fase 0 - Verifica delle fonti dati.

Per ogni fonte esegue una chiamata reale su un punto noto (sito ex Novaceta,
Magenta) e, dove serve, su un punto di controllo dove la risposta deve essere
"positiva". Stampa OK / ERRORE e salva il dettaglio in verifica_fonti_esito.json.

Usa solo la libreria standard di Python: nessuna installazione richiesta.
Uso:  python3 verifica_fonti.py
"""
import json
import datetime
import urllib.parse
import urllib.request

UA = "prefattibilita-dc/0.1 (verifica fonti)"
TIMEOUT = 90

# Punto di prova: sito ex Novaceta, viale Piemonte 66, Magenta (MI)
LAT, LON = 45.4670, 8.8736


def get(url, params=None, data=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def bbox_latlon(lat, lon, d):
    return f"{lat - d},{lon - d},{lat + d},{lon + d}"


# ---------- singole prove ----------

def catasto_wms():
    # WMS 1.3.0, EPSG:4258 (asse lat,lon). Oltre ~200 px il servizio risponde ERRX-2.
    t = get("https://wms.cartografia.agenziaentrate.gov.it/inspire/wms/ows01.php", {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
        "LAYERS": "CP.CadastralParcel", "QUERY_LAYERS": "CP.CadastralParcel",
        "STYLES": "", "CRS": "EPSG:4258", "BBOX": "45.4650,8.8720,45.4670,8.8750",
        "WIDTH": 200, "HEIGHT": 200, "I": 100, "J": 30, "INFO_FORMAT": "text/html"})
    assert "E801_000400.211" in t, "particella attesa non trovata"
    return "Magenta (E801) foglio 4 particella 211"


def catasto_wfs():
    # WFS 2.0.0: i parametri vanno in minuscolo; bbox in ordine lat,lon (EPSG:6706)
    t = get("https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php", {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": "CP:CadastralParcel", "count": 5,
        "bbox": bbox_latlon(LAT, LON, 0.0001)})
    assert "<gml:posList" in t and "E801_000400.211" in t, "geometria non trovata"
    return "poligono della particella E801_000400.211 restituito (GML 3.2)"


def pvgis_tmy():
    d = json.loads(get("https://re.jrc.ec.europa.eu/api/v5_3/tmy",
                       {"lat": LAT, "lon": LON, "outputformat": "json"}))
    h = d["outputs"]["tmy_hourly"]
    assert len(h) == 8760 and "T2m" in h[0] and "RH" in h[0]
    m = d["inputs"]["meteo_data"]
    T = [x["T2m"] for x in h]
    return (f"8760 ore; {m['meteo_db']} {m['year_min']}-{m['year_max']}; "
            f"Tmax {max(T)} °C; ore > 29,4 °C: {sum(t > 29.4 for t in T)}")


def pvgis_serie():
    d = json.loads(get("https://re.jrc.ec.europa.eu/api/v5_3/seriescalc",
                       {"lat": LAT, "lon": LON, "startyear": 2023, "endyear": 2023, "outputformat": "json"}))
    h = d["outputs"]["hourly"]
    assert len(h) == 8760 and "T2m" in h[0]
    return f"8760 ore del 2023 con T2m (campi: {', '.join(h[0])}); niente umidità"


def _idrogeo(lon, lat, r=30):
    return json.loads(get("https://idrogeo.isprambiente.it/api/pir/verifica_pericolosita_at_point",
                          {"center_wkt": f"POINT({lon} {lat})", "radius_meter": r}))


def idrogeo():
    m = _idrogeo(LON, LAT)
    assert m["nome_com"] == "Magenta"
    c = _idrogeo(10.0050, 45.1140)  # controllo: alveo del Po (Castelvetro P.no)
    assert c["pericolosita_idraulica"], "controllo positivo fallito"
    return (f"Magenta: idraulica={m['pericolosita_idraulica']} frane={m['pericolosita_frane']}; "
            f"controllo Po: idraulica={c['pericolosita_idraulica']}")


def _pcn_gfi(mapname, layer, lat, lon):
    return get(f"http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/{mapname}.map", {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
        "LAYERS": layer, "QUERY_LAYERS": layer, "STYLES": "", "CRS": "EPSG:4326",
        "BBOX": bbox_latlon(lat, lon, 0.001), "WIDTH": 101, "HEIGHT": 101,
        "I": 50, "J": 50, "INFO_FORMAT": "text/plain", "FEATURE_COUNT": 5})


def sismica():
    t = _pcn_gfi("Classificazione_sismica_2012", "RN.ZONERISCHIO.CLASSIFICAZIONESISMICA", LAT, LON)
    assert "classificazione = '4'" in t
    c = _pcn_gfi("Classificazione_sismica_2012", "RN.ZONERISCHIO.CLASSIFICAZIONESISMICA", 42.3498, 13.3980)
    assert "classificazione = '2'" in c  # controllo: L'Aquila
    return "Magenta zona 4; controllo L'Aquila zona 2 (dato al 2012)"


def natura2000():
    def q(dist):
        d = json.loads(get(
            "https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer/2/query", {
                "geometry": f"{LON},{LAT}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                "distance": dist, "units": "esriSRUnit_Meter", "outFields": "SITECODE,SITENAME",
                "returnGeometry": "false", "f": "json"}))
        return [f["attributes"]["SITECODE"] + " " + f["attributes"]["SITENAME"] for f in d["features"]]
    s1, s5 = q(1000), q(5000)
    assert s5, "controllo positivo (5 km) fallito"
    return f"entro 1 km: {len(s1)} siti; entro 5 km: {'; '.join(s5)}"


def sitap():
    def q(layer, lat, lon):
        d = json.loads(get("https://sitap.cultura.gov.it/geoserver/sitap_ws_clone/wms", {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "LAYERS": layer, "QUERY_LAYERS": layer, "STYLES": "", "SRS": "EPSG:4326",
            "BBOX": f"{lon - 0.005},{lat - 0.004},{lon + 0.005},{lat + 0.004}",
            "WIDTH": 101, "HEIGHT": 101, "X": 50, "Y": 50,
            "INFO_FORMAT": "application/json", "FEATURE_COUNT": 5}))
        return d["features"]
    m = q("lombardia_142_rispetto_fiumi", LAT, LON)
    c = q("lombardia_142_rispetto_laghi", 45.9870, 9.2610)  # controllo: Bellagio, lago di Como
    assert c, "controllo positivo fallito"
    return f"Magenta (rispetto fiumi): {len(m)} elementi; controllo Bellagio: {c[0]['properties'].get('NOME_LG')}"


def lombardia_contaminati():
    w = {"$where": "upper(comune) like '%MAGENTA%'"}
    a = json.loads(get("https://www.dati.lombardia.it/resource/npku-858g.json", w))
    b = json.loads(get("https://www.dati.lombardia.it/resource/macq-ggfu.json", w))
    nov = [r for r in a + b if "NOVACETA" in r.get("denominazione_sito", "").upper()]
    return (f"Magenta: {len(a)} siti contaminati, {len(b)} bonificati; "
            f"Novaceta: {nov[0]['cod_agisco'] + ' in elenco bonificati' if nov else 'non presente'}")


def falda_cmm():
    d = json.loads(get("https://www.dati.lombardia.it/resource/u3wq-chcr.json", {
        "$where": f"intersects(the_geom, 'POINT ({LON} {LAT})')", "$select": "soggiacenz,classe"}))
    assert d
    return f"classe soggiacenza {d[0]['classe']} m"


def nominatim():
    d = json.loads(get("https://nominatim.openstreetmap.org/search",
                       {"q": "Viale Piemonte 66, Magenta, Italia", "format": "json", "limit": 1}))
    assert d
    return f"{d[0]['display_name']} -> {d[0]['lat']}, {d[0]['lon']}"


def overpass():
    q = (f'[out:json][timeout:60];(way["power"="line"](around:3000,{LAT},{LON});'
         f'nwr["power"="substation"](around:3000,{LAT},{LON}););out tags center;')
    d = json.loads(get("https://overpass-api.de/api/interpreter", data={"data": q}))
    return f"{len(d['elements'])} elementi elettrici entro 3 km (OSM base {d['osm3s']['timestamp_osm_base']})"


def terna():
    t = get("https://www.terna.it/it/sistema-elettrico/statistiche/pubblicazioni-statistiche")
    assert "dati.terna.it/generazione/dati-statistici" in t
    return "pagina pubblicazioni statistiche raggiungibile, rimanda a dati.terna.it"


PROVE = [catasto_wms, catasto_wfs, pvgis_tmy, pvgis_serie, idrogeo, sismica, natura2000, sitap,
         lombardia_contaminati, falda_cmm, nominatim, overpass, terna]

if __name__ == "__main__":
    esito = {"data_prova": datetime.datetime.now().isoformat(timespec="seconds"), "risultati": {}}
    for p in PROVE:
        try:
            msg = p()
            stato = "OK"
        except Exception as e:  # noqa: BLE001 - vogliamo vedere ogni errore
            msg, stato = f"{type(e).__name__}: {e}", "ERRORE"
        esito["risultati"][p.__name__] = {"stato": stato, "dettaglio": msg}
        print(f"[{stato:6}] {p.__name__:22} {msg}")
    with open("verifica_fonti_esito.json", "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=2)
