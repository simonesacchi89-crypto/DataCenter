"""Ortofoto del lotto (Fase 5) dal Geoportale Nazionale MASE (WMS raster), con data del volo.

Verificato il 23/11/2026: ortofoto a colori 2012, 2006, 2000; layer OI.ORTOIMMAGINI.<anno>.32/.33
(fuso UTM 32 a ovest di 12° E, 33 a est) e OI.DATEVOLO.<anno> per le date di volo.
GetCapabilities: "Fees: Nessuna condizione applicata; AccessConstraints: Nessuno".
"""
import base64
import math
import re

from backend import catasto
from backend.controlli import _get

URL = "http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/raster/ortofoto_colore_{a2}.map"
ANNI = (2012, 2006, 2000)
FONTE = "Geoportale Nazionale MASE – Ortofoto a colori {anno} (WMS)"


def ortofoto(s: float, w: float, n: float, e: float, anno: int = 2012, larghezza: int = 1000) -> dict:
    if anno not in ANNI:
        raise ValueError(f"Anno non disponibile: scegli tra {', '.join(map(str, ANNI))}")
    if not (0 < n - s <= 0.05 and 0 < e - w <= 0.07):
        raise ValueError("Riquadro non valido o troppo grande (massimo circa 5 km)")
    url = URL.format(a2=str(anno)[2:])
    fuso = 32 if (w + e) / 2 < 12 else 33
    # altezza proporzionata: in EPSG:4326 il WMS restituisce l'immagine "stirata" sul riquadro richiesto
    lat0 = (s + n) / 2
    altezza = max(100, min(2000, round(larghezza * (n - s) / ((e - w) * math.cos(math.radians(lat0))))))

    def produci():
        img = _get(url, {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": f"OI.ORTOIMMAGINI.{anno}.{fuso}",
                         "STYLES": "", "CRS": "EPSG:4326", "BBOX": f"{s},{w},{n},{e}", "WIDTH": larghezza, "HEIGHT": altezza,
                         "FORMAT": "image/jpeg"}, timeout=120)
        if not img.startswith(b"\xff\xd8"):
            raise catasto.ErroreFonte("Il Geoportale non ha restituito un'immagine: " + img[:200].decode("utf-8", "replace"))
        date = None
        try:
            d = 0.0005
            info = _get(url, {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo", "LAYERS": f"OI.DATEVOLO.{anno}",
                              "QUERY_LAYERS": f"OI.DATEVOLO.{anno}", "STYLES": "", "CRS": "EPSG:4326",
                              "BBOX": f"{lat0 - d},{(w + e) / 2 - d},{lat0 + d},{(w + e) / 2 + d}", "WIDTH": 101, "HEIGHT": 101,
                              "I": 50, "J": 50, "INFO_FORMAT": "text/plain"}).decode("utf-8", "replace")
            # formati diversi per anno: "date = '20120516;20120529'" (2012), "data_prin_ = '19/05/07'" (2006, 2000)
            trovate = [f"{x[6:8]}/{x[4:6]}/{x[:4]}" for x in re.findall(r"\b(\d{8})\b", info)]
            trovate += [f"{d}/{m_}/{('19' if int(y) > 50 else '20') + y}" for d, m_, y in re.findall(r"'(\d{2})/(\d{2})/(\d{2})'", info)]
            date = ", ".join(dict.fromkeys(trovate)) or None
        except catasto.ErroreFonte:
            pass
        return {"immagine": "data:image/jpeg;base64," + base64.b64encode(img).decode(), "date_volo": date}

    rec = catasto._cache_json(f"ortofoto/{anno}_{s:.5f}_{w:.5f}_{n:.5f}_{e:.5f}_{larghezza}.json", 365, produci)
    return {**rec, "anno": anno, "fonte": FONTE.format(anno=anno), "url": url, "riquadro": [s, w, n, e],
            "larghezza": larghezza, "altezza": altezza,
            "nota": f"Foto aerea (volo: {rec.get('date_volo') or anno}): lo stato attuale del sito può essere diverso."}
