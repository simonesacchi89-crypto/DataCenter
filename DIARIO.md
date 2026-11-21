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
