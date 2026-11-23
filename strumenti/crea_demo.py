"""Crea la versione dimostrativa in un unico file HTML (si apre con un doppio clic, senza installare nulla).

Contiene la pagina, il motore di calcolo e il caso Magenta (ex Novaceta) "registrato" dalla cache del
programma locale: particelle del foglio 4, clima reale PVGIS (Magenta e Rho-Pero), controlli del lotto,
ortofoto e foto di esempio. Le richieste al programma locale vengono servite da questi dati.
Serve internet solo per lo sfondo della mappa (OpenStreetMap) e la libreria della mappa.

Uso, dalla cartella del progetto:  python3 strumenti/crea_demo.py
Risultato: esempi/demo_passaporto_magenta.html
"""
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
OUT = ROOT / "esempi" / "demo_passaporto_magenta.html"
CENTRO_LOTTO = (45.4676, 8.8732)  # lotto ex Novaceta


def leggi(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def particelle_magenta():
    viste = {}
    for f in [CACHE / "catasto" / "foglio_E801_000400.json", *sorted((CACHE / "catasto").glob("riquadro_45.46*_8.8*.json"))]:
        for p in leggi(f):
            viste.setdefault(p["riferimento"], p)
    # data di aggiornamento del foglio dove manca (le particelle dei riquadri non la riportano)
    agg = next((p["foglio_aggiornato_al"] for p in viste.values() if p.get("foglio_aggiornato_al")), None)
    for p in viste.values():
        if not p.get("foglio_aggiornato_al") and p["riferimento"].startswith("E801_000400."):
            p["foglio_aggiornato_al"] = agg
    return list(viste.values())


def clima(chiave):
    tmy = leggi(CACHE / "pvgis" / f"tmy_{chiave}.json")
    anni = {a: [round(t, 1) for t in v] for a, v in leggi(CACHE / "pvgis" / f"serie_{chiave}.json").items()}
    tmy["ore"] = [{"time(UTC)": h["time(UTC)"], "T2m": round(h["T2m"], 1), "RH": round(h["RH"], 1)} for h in tmy["ore"]]
    tmy.update({"anni": anni, "da_cache": True,
                "fonte": "PVGIS 5.3 – Commissione europea, JRC: temperature orarie 2005–2023 (seriescalc) e umidità dall'anno meteorologico tipo (TMY)"})
    return tmy


def controlli_magenta():
    # controlli eseguiti il 23/11/2026 alle 9:32 sul lotto di 15 particelle (Geoportale Nazionale funzionante)
    rec = None
    for f in (CACHE / "controlli").glob("*.json"):
        d = leggi(f)
        if (d.get("comune") or {}).get("codice_catastale") == "E801":
            rec = d
    assert rec, "controlli di Magenta non trovati in cache"
    for c in rec["criteri"]:
        if c["id"] == 11 and c["stato"] == "verde" and c["dettagli"]:
            # taratura successiva (soglia 5 km): stessa regola di backend/controlli.py
            dist = c["valore"].split("a ")[-1].rstrip(")")
            c.update(stato="giallo", valore=f"sito a {dist} (entro 5 km)", criterio="Aree Natura 2000 (entro 5 km)",
                     nota="Tra 1 e 5 km lo screening di incidenza è spesso richiesto (casi Magenta 3,4 km e Liscate 3,8 km).",
                     domanda="Chiedere all'ente gestore se è richiesta la Valutazione di incidenza (screening).")
        if c["id"] == 4 and "reticolo" not in c["nota"]:
            c["nota"] += (" La mosaicatura ISPRA non comprende il reticolo idrico minore (rogge, canali, fontanili): "
                          "verificare lo studio del reticolo minore e la componente geologica del PGT.")
    return rec


def ortofoto():
    out = {}
    for anno, nome in [(2012, "2012_45.46377_8.86828_45.47146_8.87809_1000"), (2006, "2006_45.46400_8.86800_45.47120_8.87850_1000"),
                       (2000, "2000_45.46400_8.86800_45.47120_8.87850_1000")]:
        rec = leggi(CACHE / "ortofoto" / f"{nome}.json")
        s, w, n, e = map(float, nome.split("_")[1:5])
        import math
        alt = round(1000 * (n - s) / ((e - w) * math.cos(math.radians((s + n) / 2))))
        out[str(anno)] = {**rec, "anno": anno, "fonte": f"Geoportale Nazionale MASE – Ortofoto a colori {anno} (WMS)",
                          "riquadro": [s, w, n, e], "larghezza": 1000, "altezza": alt,
                          "nota": f"Foto aerea (volo: {rec.get('date_volo') or anno}): lo stato attuale del sito può essere diverso."}
    return out


def foto_demo():
    meta = leggi(ROOT / "esempi" / "foto_demo" / "foto.json")
    files = {m["file"]: base64.b64encode((ROOT / "esempi" / "foto_demo" / m["file"]).read_bytes()).decode() for m in meta}
    return meta, files


def main():
    parts = particelle_magenta()
    demo = {
        "registrato_il": "23/11/2026",
        "comune": {"nome": "Magenta", "sigla": "MI", "codice_catastale": "E801", "istat": "015130", "regione": "Lombardia"},
        "meta_catasto": {"fonte": "Agenzia delle Entrate – Cartografia catastale (WFS INSPIRE)",
                         "url": "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php",
                         "licenza": "CC BY 4.0 – © Agenzia delle Entrate", "consultato_il": "2026-11-23T08:30:00+00:00",
                         "nota": "Superficie grafica calcolata dal confine della mappa catastale: può differire dalla superficie catastale ufficiale."},
        "particelle": parts,
        "clima": {"45.468_8.873": clima("45.468_8.873"), "45.510_9.087": clima("45.510_9.087")},
        "controlli": controlli_magenta(),
        "ortofoto": ortofoto(),
    }
    meta_foto, files_foto = foto_demo()
    demo["foto_meta"], demo["foto_file"] = meta_foto, files_foto

    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for nome, path in [("engine.js", ROOT / "engine.js"), ("dati.js", ROOT / "dati.js"), ("casi.js", ROOT / "casi.js"),
                       ("scheda.js", ROOT / "frontend" / "scheda.js")]:
        codice = path.read_text(encoding="utf-8").replace("</script", "<\\/script")
        html = html.replace(f'<script src="{nome}"></script>', f"<script>\n{codice}\n</script>")
    intercetta = (ROOT / "strumenti" / "demo_fetch.js").read_text(encoding="utf-8")
    dati = json.dumps(demo, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    blocco = f"<script>\nconst DEMO = {dati};\n</script>\n<script>\n{intercetta}\n</script>\n"
    # i dati e l'intercettazione devono essere caricati prima di tutti gli altri script
    i = html.index("<script")
    html = html[:i] + blocco + html[i:]
    banner = ('<div class="demo-banner" role="note"><b>Versione dimostrativa</b> · funziona senza installare nulla. '
              'Il caso <b>Magenta (ex Novaceta)</b> è registrato con i dati raccolti il 23/11/2026: premi '
              '<i>Caso reale: Magenta (SIA)</i>, poi <i>Cerca</i>, e segui i 4 passi. Potenza, raffreddamento e fonte dell\'acqua '
              'si possono cambiare. Per altri siti serve la versione completa (programma locale). Serve internet per lo sfondo della mappa.</div>')
    html = html.replace('<div class="wrap">', '<div class="wrap">\n' + banner, 1)
    html = html.replace("</style>", "  .demo-banner { border: 2px solid var(--water); background: var(--water-soft); color: var(--fg); "
                                    "border-radius: 8px; padding: 10px 14px; margin: 0 0 14px; font-size: 14px; }\n</style>", 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"Creato {OUT} ({OUT.stat().st_size / 1e6:.1f} MB), {len(parts)} particelle registrate")


if __name__ == "__main__":
    main()
