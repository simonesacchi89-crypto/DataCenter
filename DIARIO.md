# DIARIO

## 21 novembre 2026 – Fase 0: verifica delle fonti

### Cosa è stato fatto
- Letti `CLAUDE.md` e `SPEC.md`.
- Per ogni fonte del punto 5 di SPEC: cercata la documentazione ufficiale, provato il servizio con chiamate reali sul sito ex Novaceta di Magenta e, dove possibile, su un punto di controllo con risposta attesa positiva (alveo del Po, Sarno, L'Aquila, Bellagio).
- Scritto `verifica_fonti.py`: rifà tutte le prove in un colpo (solo Python standard). Esito di oggi: **11 prove su 12 OK**, fallisce solo Overpass.
- Compilato `FONTI.md` con endpoint, data, licenza e limiti di ogni fonte.
- Nessuna modifica a `engine.js` e `calcolatore.html`.

### Cosa trova già oggi la "scheda" sul caso Magenta (confronto con SPEC §7)
| Criterio | Atteso da SPEC | Trovato dalle fonti | Coerente? |
|---|---|---|---|
| 1 Superficie | ~215.300 m² | particella 211 = ~66.100 m²; servono le altre particelle del lotto | da completare in Fase 2 |
| 4 Idraulica | – | nessuna pericolosità (IdroGEO) | sì |
| 5 Frane | – | nessuna (IdroGEO) | sì |
| 6 Contaminati | rosso/giallo (bonifiche aperte) | Novaceta nell'elenco regionale dei **bonificati** (dato 2023, senza coordinate) | **no** → il dato aperto da solo non basta: criterio manuale/grigio |
| 7 Falda | giallo (3–8 m) | classe 5–7,5 m | sì (giallo) |
| 11 Natura 2000 | screening presentato | sito più vicino a 3–4 km (Boschi della Fagiana) | con la soglia 1 km verrebbe verde: **soglia da tarare** |
| 12 Sismica | – | zona 4 (dato al 2012) | sì |
| 14 Clima | – | PVGIS: 303 ore sopra 29,4 °C (3,5%) | in linea con Microsoft "< 5% dell'anno" e col ~3,7% del modello |

### Scoperte utili
- Il Geoportale Nazionale MASE espone 205 servizi WMS (sismica, PAI, Natura 2000, ecc.): utile riserva.
- SITAP ha due GeoServer WMS pubblici non citati nella documentazione, trovati nella pagina ufficiale.
- PVGIS vieta le chiamate dal browser: conferma la scelta del backend FastAPI.

### Cosa resta aperto
1. **Catasto, ricerca per foglio + particella:** il WFS non accetta filtri per codice. Decidere in Fase 2 tra download massivo per comune (GML) o ricerca per riquadro del foglio.
2. **IdroGEO, codici delle classi frane:** non documentati. Chiedere a ISPRA o trovare la documentazione; fino ad allora grigio.
3. **Overpass (OpenStreetMap):** bloccato da questo ambiente cloud. Riprovare dal computer di Simone; in alternativa estratto OSM regionale in locale.
4. **Classificazione sismica:** dato al 2012; trovare il file aggiornato della Protezione Civile.
5. **ISPRA MOSAICO:** sito con certificato non valido; trovare gli endpoint WMS/WFS dal catalogo ISPRA.
6. **Lazio:** siti contaminati senza dato aperto; dati.lazio.it non raggiungibile da qui.
7. **Teleriscaldamento:** GSE Atla offline e senza reti TLR; valutare elenchi GSE "sistemi efficienti" e anagrafica ARERA.
8. **Licenze da confermare:** PVGIS (pagina condizioni), IdroGEO (dati), EEA Natura 2000, Terna, Regione Lazio.
9. **Terna:** trovare i file scaricabili per aggiornare il fattore di acqua indiretta in Fase 1.
10. **Soglie da tarare:** Natura 2000 (screening presentato anche con sito a 3–4 km); contaminati (gli elenchi senza confini non bastano).

## 23 novembre 2026 – Fase 1: calcolatore con clima reale

### Come si avvia (sul computer di Simone)
1. Una volta sola: `pip install -r requirements.txt`
2. Dalla cartella del progetto: `uvicorn backend.app:app`
3. Aprire http://127.0.0.1:8000 → "Clima del sito" → "Coordinate: clima reale PVGIS" → "Scarica il clima reale del punto".

Test: `node --test tests/engine.test.js` (motore) e `python3 -m pytest tests/` (backend, con chiamata reale a PVGIS). Confronto climi: `node tests/confronto_pvgis.js` (aggiungere `--tmy` per il solo anno tipo).

### Cosa è stato fatto
- `dati.js`: clima di Milano/Roma/Viterbo, mix elettrico e parametri dei 5 sistemi spostati fuori dalla pagina, identici a `calcolatore.html`.
- `engine.js`: **fisica invariata** (`simulate` non toccata). Aggiunti solo: `simulateMultiHours` (stessa aggregazione di `simulateMulti` su anni forniti dall'esterno; un test verifica che i risultati coincidano), `hoursAboveHours`, `hoursFromPVGIS` (anno tipo) e `yearsFromPVGIS` (19 anni reali).
- `casi.js` + `tests/engine.test.js`: i casi di SPEC §7 come test automatici. **Con il clima sintetico tornano tutti (12/12)**, con gli stessi numeri di SPEC.
- `backend/app.py` (FastAPI): `GET /api/clima?lat&lon` scarica da PVGIS anno tipo e serie 2005–2023, salva in `cache/pvgis/` con fonte e data di scarico; se PVGIS non risponde dà un errore chiaro (502). Serve anche la pagina.
- `frontend/index.html`: il calcolatore con la nuova scelta "Coordinate: clima reale PVGIS". Mostra fonte, punto, quota e data di scarico. Se il programma locale è spento o PVGIS non risponde, lo dice e il risultato è marcato "da verificare". `calcolatore.html` è rimasto intatto. Verificato nel browser: con il clima sintetico i numeri sono identici all'originale.
- `verifica_fonti.py`: aggiunta la prova delle serie PVGIS.

### Scoperta: l'anno tipo PVGIS non va bene per l'acqua
L'anno tipo sceglie per ogni mese un anno "normale" diverso. Per l'energia va bene, per l'acqua no: l'acqua dipende dalle poche ore più calde, e queste dipendono da quale estate capita.
- Rho-Pero: agosto 2007 (fresco, 18 ore sopra 29,4 °C) → AWS 30.700 m³.
- Linate, a 20 km: agosto 2011 (caldo, 142 ore) → AWS 61.800 m³.

Per questo il calcolatore usa **19 anni reali** (temperature vere 2005–2023 e umidità tipica del mese dall'anno tipo). Il risultato è la media, la forbice è minimo–massimo tra anni veri.

### Confronto casi di test: clima sintetico contro 19 anni reali PVGIS
| Caso | Pubblicato | Sintetico Milano | PVGIS Magenta | PVGIS Rho-Pero | PVGIS Linate |
|---|---|---|---|---|---|
| AWS acqua (m³) | 50.000 | 51.857 ✅ | 42.076 ✅ | **35.424 ❌ (−29%)** | 48.523 ✅ |
| AWS PUE | 1,08 | 1,08 | 1,08 | 1,08 | 1,08 |
| Magenta chiller PUE annuo | 1,25 obiettivo | 1,17 | 1,16 | 1,16 | 1,16 |
| Magenta chiller PUE ora peggiore | 1,50 picco | 1,40 | 1,40 | 1,40 | 1,41 |
| Magenta hybrid >25 °C (m³) | ~500.000 | 535.835 ✅ | 446.044 ✅ | 398.521 ❌ | 465.689 ✅ |
| Magenta hybrid >26 °C (m³) | ~500.000 | 435.823 ✅ | 355.299 ❌ | 313.017 ❌ | 374.715 ❌ |
| Magenta adiabatico (m³) | ~200.000 | 184.519 ✅ | **148.597 ❌ (−26%)** | 130.849 ❌ | 197.861 ✅ |
| Microsoft ore >29,4 °C | < 5% | 3,7% | 3,0% | 2,4% | 3,4% |
| Microsoft WUE | 0,03 (EMEA) | 0,028 | 0,023 | 0,019 | 0,027 |

Forbice tra anni reali per AWS a Rho-Pero: **11.500–74.000 m³**.

Lettura:
- **Energia: invariata.** I PUE non dipendono quasi dal clima scelto.
- **Acqua: con il clima reale del proprio sito i casi stanno sotto il dato pubblicato del 20–30%.** Il clima sintetico di Linate (medie 1991–2020 con ondate di calore statistiche) è più caldo nelle ore estreme della media reale 2005–2023 del punto ERA5. Le soglie dei preset (es. AWS: acqua sopra 28 °C, mandata 24 °C) erano state tarate sul clima sintetico.
- Possibile spiegazione per AWS: i 50.000 m³ della VIA potrebbero essere un valore di progetto prudente (anno caldo) e non una media. La forbice reale lo comprende.
- Limite di ERA5: griglia di circa 25 km, sottostima l'isola di calore urbana e i picchi. Rho-Pero e Linate cadono in celle diverse.

### Cosa resta aperto
1. ~~Decisione di Simone: ritarare le soglie o no?~~ → **Deciso il 23/11/2026: non si ritarano** (vedi sotto).
2. Umidità: stimata dal punto di rugiada tipico del mese. Nelle ondate di calore l'umidità reale può essere diversa. Se serve più precisione, va trovata una fonte oraria con umidità per tutti gli anni (da verificare come da regole).
3. Coordinate precise dei siti AWS e Microsoft: per AWS ho usato il centro di Pero (45,510, 9,087); per Microsoft Linate (indirizzo non pubblico).
4. Licenza formale PVGIS (pagina "Usage Conditions") ancora da leggere.
5. I controlli "Verifica sui casi reali" della pagina usano ancora il clima sintetico di Milano (sono il riferimento dei test).

### Decisione del 23/11/2026: soglie non ritarate
Simone ha scelto di **non ritarare** le soglie dei sistemi sul clima reale. Con il clima reale del proprio sito il dato pubblicato si confronta con la forbice dei 19 anni:

| Caso | Pubblicato (m³) | Media modello | Forbice 2005–2023 | Anni in cui è raggiunto |
|---|---|---|---|---|
| AWS Rho-Pero, aria diretta | 50.000 (VIA) | 35.424 | 11.530–73.951 | 3 su 19: 2006, 2015, 2022 |
| Magenta adiabatico >29 °C | 200.000 (SIA) | 148.597 | 42.772–321.258 | 2 su 19: 2006, 2022 |
| Magenta hybrid >25 °C | 500.000 (SIA) | 446.044 | 220.674–670.232 | 4 su 19: 2017, 2019, 2022, 2023 |
| Magenta hybrid >26 °C | 500.000 (SIA) | 355.299 | 153.825–570.833 | 1 su 19: 2022 |

I dati pubblicati si leggono come **valori da anno caldo** (2006, 2015 e 2022 sono estati notoriamente calde), non come medie.
- **Nuovo criterio di test col clima reale:** il dato pubblicato deve stare dentro la forbice degli anni reali ed essere raggiunto almeno in un anno. I test col clima sintetico restano con le tolleranze di SPEC §7. In totale 16 test, tutti verdi.
- I dati PVGIS di Magenta e Rho-Pero sono salvati in `tests/fixtures/` (scaricati il 23/11/2026), così i test funzionano anche senza rete.
- La pagina mostra la tabella "I dati pubblicati negli anni veri" nella sezione di verifica, se il programma locale è avviato.

## 23 novembre 2026 – Fase 2: particella sulla mappa

### Cosa è stato fatto
- `backend/catasto.py`: connettore Catasto (WFS Agenzia delle Entrate) con tre funzioni:
  - **da coordinate** → particella che contiene il punto;
  - **da comune + foglio + particelle** → nome comune → codice catastale (ISTAT) → riquadro del comune (OpenStreetMap/Nominatim) → foglio → particelle;
  - **particelle visibili** in un riquadro (per disegnare i confini sulla mappa).
  Per ogni particella: confine, superficie grafica, data di aggiornamento del foglio, fonte, licenza e data di consultazione. Cache su disco (7 giorni catasto, 30 giorni ISTAT, 180 giorni riquadri dei comuni).
- Nuovi indirizzi del backend: `/api/particella/punto`, `/api/particelle/cerca`, `/api/particelle/riquadro`.
- Pagina: nuova sezione **"Il sito"** in cima, con ricerca, mappa (sfondo OpenStreetMap), confini catastali da vicino, selezione con un clic, totale in m² ed ettari, **m²/MW** con il colore del criterio 1 di SPEC (soglie indicative). Le coordinate del clima si aggiornano al centro delle particelle scelte.
- Test: `tests/test_catasto.py` (4 senza rete, 4 con il servizio reale). In totale 12 test Python + 16 del motore, tutti verdi.

### Prova sul caso reale: Magenta, ex Novaceta
- "Magenta, foglio 4, particella 211" → 66.262 m², foglio aggiornato all'11/09/2025.
- Le 15 particelle che cadono nel perimetro "area ex Novaceta" di OpenStreetMap (foglio 4: 37, 42, 166, 206, 207, 210, 211, 212, 213, 214, 218, 219, 237, 242, 243) sommano **215.349 m²**. Lo SIA dichiara **circa 215.300 m²**: differenza 0,02%.
- Con 240 MW IT: **897 m²/MW → giallo** "da approfondire", come atteso da SPEC §7.

### Limiti del servizio catasto scoperti (gestiti nel codice, dettagli in FONTI.md)
- Rifiuta richieste con `count=5000` (ma non 4999).
- Oltre circa 7 km di lato risponde "0 risultati" senza errore: rischio di falsi "niente trovato". Il codice divide sempre i riquadri grandi.
- Errori intermittenti su richieste corrette: il codice riprova. La prima ricerca in un comune può richiedere circa 30 secondi; poi resta in cache.
- Il WMS del catasto non si può sovrapporre alla mappa web (non supporta EPSG:3857): i confini si disegnano dai dati vettoriali.

### Cosa resta aperto
1. Il lotto va scelto a mano (clic o elenco di particelle): non esiste un dato aperto che dica "questo è il sito del progetto".
2. Superficie grafica ≠ superficie catastale ufficiale: lo dice la scheda; per i numeri ufficiali serve la visura.
3. Licenza ISTAT da verificare.
4. Ricerca per **indirizzo** non ancora nella pagina (Nominatim trova la via ma non sempre il civico): si può aggiungere come "vai a" sulla mappa.
5. Trento e Bolzano: catasto provinciale, non coperto (la scheda dice "da verificare").
