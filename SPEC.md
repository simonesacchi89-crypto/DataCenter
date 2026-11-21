# SPEC – Passaporto Acqua e Calore

## 1. Obiettivo
Prefattibilità rapida di un terreno per un data center, più calcolo di energia, acqua e calore. Utenti: sviluppatori e fondi che cercano siti, società di ingegneria che preparano VIA, comuni che devono valutare domande.

## 2. Input
| Campo | Obbligatorio | Note |
|---|---|---|
| Localizzazione | Sì | Indirizzo, coordinate, oppure comune + foglio + particella (una o più) |
| Potenza IT (MW) | Sì | |
| Carico medio (%) | No | Default 70 |
| Sistema di raffreddamento | Sì | I 5 sistemi di `engine.js` |
| Energia annua dichiarata (GWh) | No | Se presente da documenti di progetto |
| Foto del sito | No | Fase 5 |

## 3. Output: la scheda
- Mappa con confini della particella e strati principali.
- Tabella criteri: semaforo, valore trovato, fonte con data, nota.
- Blocco calcolo: PUE e classe, WUE e classe, acqua diretta (con forbice), acqua indiretta, impronta idrica completa, calore di scarto.
- "Domande da fare": elenco generato dai criteri gialli, rossi e grigi.
- Disclaimer di prefattibilità (vedi `CLAUDE.md`).
- Esportazione della scheda in HTML stampabile o PDF.

## 4. Criteri e regole del semaforo
Le soglie sono **ipotesi iniziali da tarare** con i casi reali. Le soglie di superficie derivano da due soli progetti (Magenta circa 900 m² per MW IT di campus, AWS Rho-Pero circa 1.270 m² per MW).

| # | Criterio | Fonte | Verde | Giallo | Rosso |
|---|---|---|---|---|---|
| 1 | Superficie per MW IT | Catasto (geometria particelle) | ≥ 1.000 m²/MW | 600–1.000 | < 600 |
| 2 | Destinazione urbanistica | Piano regolatore comunale (spesso PDF: in Fase 1 inserimento manuale) | Produttiva / industriale | Da verificare o serve variante | Agricola o tutelata |
| 3 | Vincoli paesaggistici e culturali | Vincoli in rete / SITAP (Ministero della Cultura) | Nessuno entro 500 m | Bene tutelato entro 500 m | Lotto dentro area vincolata |
| 4 | Pericolosità idraulica | ISPRA IdroGEO / piani di assetto idrogeologico | Nessuna o bassa (P1) | Media (P2) | Elevata (P3) |
| 5 | Frane | ISPRA IdroGEO | Nessuna | Pericolosità moderata | Pericolosità elevata o molto elevata |
| 6 | Siti contaminati | Anagrafe regionale dei siti contaminati | Nessuno entro 500 m | Sito vicino o falda contaminata nell'area | Bonifica aperta sul lotto |
| 7 | Profondità della falda | Dati regionali o piezometri | > 8 m | 5–8 m | < 5 m (scavi per serbatoi e vasche in falda) |
| 8 | Distanza dalla rete ad alta tensione | Mappe linee e stazioni (es. OpenStreetMap, dati Terna dove pubblici) | < 2 km | 2–10 km | > 10 km |
| 9 | Capacità di connessione | Solo Terna, su richiesta formale | – | Sempre "da chiedere" | – |
| 10 | Vicini sensibili | Mappe edifici, scuole, ospedali | Nessuna abitazione < 500 m | Abitazioni < 500 m | Scuole o ospedali < 200 m |
| 11 | Aree Natura 2000 | Ministero dell'Ambiente / Agenzia europea dell'ambiente | Nessuna < 1 km | < 1 km (serve screening di incidenza) | Lotto dentro l'area |
| 12 | Sismicità | Classificazione sismica comunale | Zona 3–4 | Zona 2 | Zona 1 |
| 13 | Teleriscaldamento vicino | GSE Atla | Rete < 2 km (opportunità) | – | – (solo informativo) |
| 14 | Clima, acqua, energia | `engine.js` | WUE classe A–B | C–D | E–G o acqua diretta oltre una soglia scelta dall'utente |

## 5. Fonti da verificare (Fase 0)
Per ognuna: trovare l'endpoint ufficiale, provarlo, annotare licenza e data in `FONTI.md`.
- Catasto, Agenzia delle Entrate: consultazione WMS e dati vettoriali (WFS e download) in open data, licenza CC BY 4.0, aggiornamento semestrale, escluse Trento e Bolzano. Non include i proprietari.
- ISPRA IdroGEO: pericolosità idraulica e frane, servizi WMS e dati.
- Ministero della Cultura: Vincoli in rete e SITAP.
- GSE Atla: reti di teleriscaldamento.
- PVGIS (Commissione europea, JRC): anno meteorologico tipo orario per qualsiasi punto. **Sostituisce il clima sintetico di `engine.js`** e migliora la precisione.
- OpenStreetMap (Overpass API): linee e stazioni elettriche, scuole, ospedali, edifici.
- Natura 2000: confini delle aree protette.
- Anagrafi regionali dei siti contaminati: partire dal Lazio (Tuscia) e dalla Lombardia (casi di test).
- Mix elettrico: Terna (bilancio annuale) per aggiornare i fattori di acqua indiretta.

## 6. Fasi di lavoro
- **Fase 0 – Fonti.** Verifica di tutte le fonti del punto 5, compilazione di `FONTI.md`. Nessuna interfaccia.
- **Fase 1 – Calcolatore con clima reale.** Integrare `engine.js` con il clima orario PVGIS del punto scelto. I casi di test del punto 7 devono tornare entro le tolleranze.
- **Fase 2 – Particella sulla mappa.** Da comune + foglio + particella, oppure da coordinate: geometria, superficie, mappa.
- **Fase 3 – Controlli automatici.** Criteri 3, 4, 5, 8, 10, 11, 12, 13. Inserimento manuale per i criteri 2, 6 e 7 dove non ci sono dati aperti.
- **Fase 4 – Scheda e domande.** Semafori, domande, esportazione.
- **Fase 5 – Foto.** Caricamento di foto o immagini satellitari, descrizione automatica dello stato del sito (edifici, coperture, alberi, accessi) come nota, mai come semaforo.

## 7. Casi di test

### Calcolo (devono tornare)
| Caso | Dato pubblicato | Atteso dal modello | Tolleranza |
|---|---|---|---|
| AWS Rho-Pero, 79 MW IT, Milano, aria diretta + evaporativo (soglia 28 °C, mandata 24 °C, ricircolo 2,7) | 50.000 m³/anno, PUE 1,08 | ~51.900 m³, PUE 1,08 | ±20% sull'acqua |
| Magenta, 240 MW IT, Milano, chiller ad aria a circuito chiuso | PUE annuo obiettivo 1,25, picco 1,50 | ~1,17 annuo, ~1,40 ora peggiore | Segnalare se fuori 1,10–1,30 |
| Magenta, soluzione scartata hybrid cooler | ~500.000 m³/anno | 436.000–536.000 (bagnato sopra 25–26 °C) | ±20% |
| Magenta, soluzione scartata adiabatica | ~200.000 m³/anno | ~185.000 (acqua sopra 29 °C) | ±20% |
| Microsoft Milano, evaporativo diretto sopra 29,4 °C | Acqua < 5% dell'anno; WUE EMEA 0,03 | ~3,7% delle ore; WUE ~0,028 | Plausibilità |
| Rete Italia 2025 (metodo The Green Grid) | – | ~0,67 L/kWh; ~2,9 con evaporazione bacini | Ricalcolare se cambia il mix |

Con il clima reale PVGIS i risultati cambieranno un po': annotare le differenze in `DIARIO.md`.

### Sito (Magenta, ex Novaceta, viale Piemonte 66): cosa la scheda dovrebbe trovare
Fonte: Studio di Impatto Ambientale (dicembre 2025), contributo ARPA Lombardia (maggio 2026), parere della Soprintendenza, osservazioni pubbliche.
- Superficie circa 215.300 m² per 240 MW IT → giallo (circa 900 m²/MW).
- Area industriale dismessa → urbanistica verde.
- Bonifiche ancora aperte su parte del lotto; falda con superamenti per solventi clorurati → rosso o giallo.
- Falda a 3–8 m con oscillazioni di circa 2 m → giallo.
- Stazione Terna circa 500 m a nord; nuovo elettrodotto 360 MW in autorizzazione → verde sulla distanza, capacità "da chiedere".
- Rilievi della Soprintendenza su skyline e altezza degli edifici → giallo sui vincoli.
- Residenti a circa 400–450 m che contestano rumore e generatori → giallo.
- Nessuna rete di teleriscaldamento a Magenta → informativo.
- Screening di incidenza ambientale presentato → verificare il criterio Natura 2000.

## 8. Limiti da mostrare sempre
- La capacità di connessione la conosce solo Terna.
- La destinazione urbanistica vale solo con il certificato del comune.
- Il calcolo è una stima preliminare: per un progetto vero servono i dati dei costruttori (curve dei chiller, portate d'aria, ricircoli).
