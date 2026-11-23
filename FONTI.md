# FONTI – endpoint verificati

**Data delle prove:** 21 novembre 2026, eseguite da ambiente cloud.
**Punto di prova:** sito ex Novaceta, viale Piemonte 66, Magenta (MI) – lat 45,4670, lon 8,8736.
**Come rifare le prove:** `python3 verifica_fonti.py` (solo librerie standard; scrive `verifica_fonti_esito.json`).

Legenda stato: ✅ verificato e funzionante · ⚠️ funziona con limiti importanti · ❌ non utilizzabile oggi · 📝 solo inserimento manuale.

## Riepilogo

| # | Fonte | Criterio | Stato | Licenza |
|---|---|---|---|---|
| 1 | Catasto AdE – WMS | 1, mappa | ✅ | CC BY 4.0 |
| 2 | Catasto AdE – WFS | 1 (confine e superficie) | ✅ ricerca per foglio/particella risolta in Fase 2 (via riquadri) | CC BY 4.0 |
| 3 | PVGIS (JRC) – TMY e serie orarie 2005–2023 | 14 (clima) | ✅ | uso libero, condizioni formali da leggere |
| 4 | ISPRA IdroGEO – API | 4, 5 | ⚠️ codici classi frane da confermare | da verificare |
| 5 | Geoportale Nazionale MASE – classificazione sismica | 12 | ⚠️ dato al 2012 | nessuna condizione dichiarata |
| 6 | Geoportale Nazionale MASE – PAI | 4, 5 (riserva) | ⚠️ lento, dati disomogenei | nessuna condizione dichiarata |
| 7 | EEA – Natura 2000 | 11 | ⚠️ dal 23/11/2026 non raggiungibile da qui; sostituita da §8 | EEA (CC BY 4.0 da confermare) |
| 8 | Geoportale Nazionale MASE – WFS SIC/ZSC/ZPS ed EUAP | 11, 3 (parchi) | ✅ usato in Fase 3 | nessuna condizione dichiarata nel servizio; dati MASE: non commerciale (vedi §8) |
| 9 | MiC – SITAP (GeoServer WMS e WFS) | 3 | ⚠️ copertura per regione disomogenea; WFS usato in Fase 3 | non dichiarata |
| 10 | MiC – Vincoli in Rete | 3 | ❌ nessun servizio pubblico | citare la fonte |
| 11 | Regione Lazio – PTPR (WFS) | 3 (Lazio) | ✅ elenco strati letto | da verificare |
| 12 | Lombardia – siti contaminati e bonificati | 6 | ⚠️ senza coordinate | CC0 |
| 13 | Città Metropolitana di Milano – soggiacenza falda | 7 (solo CMM) | ✅ | CC0 |
| 14 | ISPRA MOSAICO – siti contaminati | 6 (nazionale) | ❌ certificato TLS del sito non valido | da verificare |
| 15 | Lazio – siti contaminati | 6 | ❌ dato aperto non trovato | – |
| 16 | OpenStreetMap – Overpass API | 8, 10 | ❌ da cloud; da riprovare in locale | ODbL |
| 17 | OpenStreetMap – Nominatim | geocodifica indirizzo | ✅ | ODbL |
| 18 | GSE Atlaimpianti | 13 | ❌ sistema offline | CC BY-NC-SA 3.0 IT (sito) |
| 19 | Terna – dati statistici | mix elettrico | ⚠️ dati 2025 letti, licenza non trovata | da verificare |
| 20 | Piano regolatore comunale | 2 | 📝 | – |
| 21 | ISTAT – elenco comuni (codice catastale) | ricerca particella | ✅ | da verificare |

---

## 1. Catasto – Agenzia delle Entrate, WMS
- **Documentazione:** https://www.agenziaentrate.gov.it/portale/schede/fabbricatiterreni/consultazione-cartografia-catastale/servizio-consultazione-cartografia
- **Endpoint verificato:** `https://wms.cartografia.agenziaentrate.gov.it/inspire/wms/ows01.php` (WMS 1.3.0)
- **Strati:** `CP.CadastralParcel` (particelle, interrogabile), `CP.CadastralZoning` (fogli), `fabbricati`, `strade`, `acque`, `codice_plla`, `province`.
- **Sistemi di riferimento:** EPSG:6706, 4258, 25832–25834, 3044–3046. Con EPSG:4258 in WMS 1.3.0 il BBOX è in ordine **lat,lon**.
- **Prova:** GetMap PNG ✅; GetFeatureInfo `INFO_FORMAT=text/html` → `NationalCadastralReference = E801_000400.211` (Magenta, foglio 4, particella 211).
- **Limite trovato in prova:** GetFeatureInfo risponde `ERRX-2` con immagini oltre ~200 px; con 101 px a volte non trova la particella. Usare 200×200.
- **Formato codice:** `E801_000400.211` = codice catastale comune `E801` + foglio `0004` + allegato `0` + sviluppo `0` + `.` particella.
- **Licenza:** CC BY 4.0, obbligo di citare l'Agenzia delle Entrate (Fees nel GetCapabilities: "CC BY 4.0").
- **Copertura:** tutta Italia tranne le Province autonome di Trento e Bolzano.
- **Aggiornamento:** non dichiarato per il WMS; il download massivo è semestrale. Nessun dato sui proprietari.

## 2. Catasto – Agenzia delle Entrate, WFS
- **Documentazione:** https://www.agenziaentrate.gov.it/portale/cartografia-catastale-wfs
- **Endpoint verificato:** `https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php` (WFS 2.0.0, MapServer)
- **Tipi:** `CP:CadastralParcel`, `CP:CadastralZoning`. CRS predefinito EPSG:6706.
- **Prova riuscita:** `service=WFS&version=2.0.0&request=GetFeature&typeNames=CP:CadastralParcel&bbox=45.4669,8.8735,45.4671,8.8737&count=5` → poligono GML 3.2 della particella 211 (41 vertici, **circa 66.100 m²**). Il foglio 4 (`E801_000400`) risulta aggiornato al 11/09/2025 (`BEGINLIFESPANVERSION`).
- **Attenzione:** i nomi dei parametri vanno **in minuscolo** (con `SERVICE=`, `BBOX=` maiuscoli il servizio risponde "Richiesta non valida"); bbox in ordine lat,lon.
- **Non funziona:** ricerca per codice (`resourceId`, filtro `PropertyIsEqualTo` su `NATIONALCADASTRALREFERENCE`, anche combinato con BBOX): risposta vuota o errore 500. La documentazione non dice quali filtri sono supportati.
- **Conseguenza per la Fase 2:** "comune + foglio + particella" va risolto in un altro modo (download massivo per comune in GML, oppure ricerca per riquadro del foglio). Da decidere in Fase 2.
- **Limiti trovati in Fase 2 (prove del 23/11/2026), gestiti in `backend/catasto.py`:**
  - `count=5000` viene rifiutato con "Richiesta non valida"; `4999` no. Usiamo `count=1000` e, se la risposta arriva piena, si divide il riquadro.
  - Riquadri oltre ~0,07° di lato: risposta `numberMatched="unknown"` con 0 oggetti, **senza errore**. Si lavora a tessere di 0,05°.
  - Errori "Richiesta non valida" **intermittenti** su richieste corrette: 4 tentativi con pause 1-2-4 s, poi riquadri più piccoli.
- **Ricerca comune + foglio + particella (Fase 2):** nome comune → codice catastale (ISTAT, §21) → riquadro del comune (Nominatim, §17) → fogli `CP:CadastralZoning` nel riquadro (filtrati per prefisso del codice) → particelle `CP:CadastralParcel` nel riquadro del foglio, filtrate per numero. Prova: Magenta foglio 4 particella 211 trovata; le 15 particelle del lotto ex Novaceta sommano 215.349 m² (SIA: 215.300).
- **Data di aggiornamento:** `BEGINLIFESPANVERSION` del foglio (Magenta foglio 4: 11/09/2025), mostrata nella scheda.
- **Download massivo:** https://www.agenziaentrate.gov.it/portale/download-massivo-cartografia-catastale – GML in ZIP per comune, aggiornamento semestrale, CC BY 4.0. URL dei file non ancora verificato.
- **Limiti dichiarati:** "un limite massimo di richieste contemporanee" (numero non indicato).

## 3. PVGIS – Commissione europea, JRC
- **Documentazione:** https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/getting-started-pvgis/api-non-interactive-service_en
- **Endpoint verificato:** `https://re.jrc.ec.europa.eu/api/v5_3/tmy?lat=..&lon=..&outputformat=json` (anche `v5_2` risponde)
- **Prova:** 8.760 ore con `T2m` (°C), `RH` (%), irraggiamento, vento, pressione. Dati meteo ERA5 2005–2023, radiazione PVGIS-SARAH3. Magenta: Tmax 37,8 °C, Tmin −6,9 °C, 303 ore sopra 29,4 °C, 511 sopra 28 °C.
- **Limiti:** 30 chiamate/secondo per IP; **le chiamate dal browser (AJAX) sono vietate** → deve passare dal backend (conferma la scelta di FastAPI).
- **Licenza:** manuale PVGIS: "completely free to use, with no restrictions on what the results can be used for, and with no registration necessary". Pagina "Usage Conditions" non letta (errore 429): da rileggere.
- **Nota:** è in beta PVGIS 6 (dati 2014–2025); per ora usiamo la 5.3, versione di produzione.
- **Serie orarie pluriennali (verificato il 23/11/2026):** `https://re.jrc.ec.europa.eu/api/v5_3/seriescalc?lat=..&lon=..&startyear=2005&endyear=2023&outputformat=json` → ore reali 2005–2023 con `T2m` (anche irraggiamento e vento), **senza umidità relativa**. Circa 14 MB e 10 s per punto; il backend tiene solo le temperature (~1 MB in cache).
- **Uso nel progetto (Fase 1):** temperature dalle serie 2005–2023 (19 anni) + punto di rugiada medio per mese e ora dall'anno tipo dello stesso punto. L'anno tipo da solo non va usato per l'acqua: sceglie un anno diverso per ogni mese e può capitare un'estate fresca o torrida (vedi DIARIO, 23/11/2026).

## 4. ISPRA IdroGEO – API
- **Documentazione:** specifica OpenAPI in `https://idrogeo.isprambiente.it/api/` (versione 3.3.1).
- **Endpoint verificato:** `GET https://idrogeo.isprambiente.it/api/pir/verifica_pericolosita_at_point?center_wkt=POINT(lon lat)&radius_meter=30` (raggio 30–500 m)
- **Risposta:** comune, provincia, regione, autorità di distretto, `pericolosita_idraulica`, `pericolosita_frane`, elenco frane/eventi, data di estrazione.
- **Prove:**
  - Magenta: idraulica nessuna, frane nessuna (autorità di distretto Po).
  - Controllo alveo del Po (Castelvetro P.no / Piacenza): idraulica `['1','2','3']`; centro di Cremona: `['1']`; Sarno: frane `[1,2,4]`; Genova: frane `[1]`.
- **Interpretazione (dedotta, non documentata):** idraulica `1/2/3` = scenari P1/P2/P3 (l'alveo è dentro tutti e tre, il centro di Cremona solo nel P1; coerente con la fascia C del PAI Po). **Per le frane la corrispondenza codici → classi (P1–P4, AA) non è documentata:** chiedere a idrogeo@isprambiente.it o trovarla prima della Fase 3. Fino ad allora il criterio frane, se c'è un codice, va in grigio "da verificare".
- **Licenza:** la specifica indica AGPL-3.0 per il software; licenza dei dati non trovata (pagina termini `/app/page/toc` non leggibile senza browser). Da verificare.
- **Servizi WMS IdroGEO:** non trovati nella documentazione.

## 5. Geoportale Nazionale (MASE) – Classificazione sismica
- **Elenco servizi ufficiale:** https://gn.mase.gov.it/portale/servizio-di-consultazione-wms (205 servizi)
- **Endpoint verificato:** `http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/Classificazione_sismica_2012.map` – strato `RN.ZONERISCHIO.CLASSIFICAZIONESISMICA`
- **Prova:** GetFeatureInfo `text/plain` → Magenta `classificazione = '4'` (DGR 14964 del 07/11/2003); controllo L'Aquila `'2'`.
- **Limite:** dato **"al 2012"**. Alcune regioni hanno riclassificato dopo (es. Lombardia, DGR 2014 in vigore dal 2016). Mostrare sempre "classificazione al 2012 – verificare la delibera regionale vigente". La fonte primaria (Protezione Civile) è un sito JavaScript non leggibile in automatico: da cercare il file aggiornato.
- **Licenza:** GetCapabilities "Fees: Nessuna condizione applicata; AccessConstraints: Nessuno".
- **Nota:** servizio solo in `http` (non https).

## 6. Geoportale Nazionale (MASE) – PAI
- **Endpoint:** `http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/PAI_pericolosita.map` – strati `RN.PAI.PERICOLOSITA.ALLUVIONE`, `RN.PAI.PERICOLOSITA.FRANA_01`, `RN.PAI.PERICOLOSITA.FRANA_02`
- **Prova:** Cremona → `tipologia = 'FASCIA C'`, piano PAI Po. Molte richieste in timeout (> 60 s); attributi spesso vuoti (`data_aggiornamento` vuota).
- **Uso consigliato:** solo come riserva di IdroGEO.

## 7. EEA – Natura 2000
- **Documentazione:** https://www.eea.europa.eu/data-and-maps/data/natura-14
- **Endpoint verificato:** `https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer/2/query` (strato 2 = SIC/ZSC + ZPS; 0 = Habitat, 1 = Uccelli). Parametri: `geometry=lon,lat`, `geometryType=esriGeometryPoint`, `inSR=4326`, `distance`, `units=esriSRUnit_Meter`, `f=json`.
- **WMS:** `https://bio.discomap.eea.europa.eu/arcgis/services/ProtectedSites/Natura2000Sites/MapServer/WMSServer`
- **Prova:** Magenta → nessun sito entro 3 km; entro 4 km IT2050005 Boschi della Fagiana; entro 5 km anche IT2010014 e IT2080301 Boschi del Ticino. `RELEASE_DATE` 13/12/2024 (versione "fine 2024").
- **Licenza:** copyright "EEA, Copenhagen, 2025"; scheda metadati collegata a CC BY 4.0 (testo non letto): da confermare.
- **23/11/2026:** da questo ambiente le connessioni a `bio.discomap.eea.europa.eu` si interrompono (anche una semplice GET). Per il criterio 11 si usa il WFS del Geoportale Nazionale (§8 bis), fonte ufficiale italiana.

## 8. MASE – Natura 2000 ufficiale italiana
- **Pagina:** https://www.mase.gov.it/portale/web/guest/schede-e-cartografie (aggiornata 27/01/2026)
- **Download:** `https://download.mase.gov.it/Natura2000/Trasmissione%20CE_dicembre2025` – shapefile SIC/ZSC/ZPS, UTM 32N WGS84. Non ancora scaricato.
- **WMS (Geoportale Nazionale):** `.../Vettoriali/SIC_ZSC_ZPS.map`, strato `SP.SITIPROTETTI.SIC_ZSC_ZPS` (GetCapabilities ✅).
- **Licenza:** "I dati possono essere utilizzati solo per fini non commerciali, previa citazione della fonte. È vietata la distribuzione, l'adattamento e ogni altra modifica." → per uno strumento potenzialmente commerciale preferire EEA.

## 8 bis. Geoportale Nazionale MASE – servizi WFS (verificati il 23/11/2026, Fase 3)
- **Elenco ufficiale:** https://gn.mase.gov.it/portale/wfs (67 servizi).
- **Natura 2000:** `http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/wfs/SIC_ZSC_ZPS.map`, tipo `SP.SITIPROTETTI.SIC_ZSC_ZPS`. WFS 1.1.0, bbox `s,w,n,e,urn:ogc:def:crs:EPSG::4326`, GML 3.1 con coordinate **lat lon**. Campi: `site_code`, `tipo_sito`, `denominazi`, `aggiorn` (AAAAMM, es. 201210), `regione`.
  Prova: attorno a Magenta trova IT2050005, IT2080301, IT2010014, IT1150001. Il lotto ex Novaceta dista 3,4 km dal più vicino.
- **Aree protette EUAP (parchi e riserve, art. 142 lett. f):** `.../ms_ogc/wfs/EUAP.map`, tipo `SP.SITIPROTETTI.EUAP`. Campi: `codice_are`, `tipo` (PNR, PN, RNR...), `nome_gazze`, `ente_gesto`. Prova: trova "Parco naturale lombardo della Valle del Ticino" (EUAP0195). Copre il buco di SITAP sui parchi regionali lombardi.
- **Altri utili:** `PAI_pericolosita.map`, `Classificazione_sismica_2012.map` (anche in WFS).
- **Nota:** servizi solo in `http`. Il campo `aggiorn` dei siti Natura 2000 riporta date vecchie (2006–2012): da confrontare con lo shapefile MASE di dicembre 2025.

## 9. Ministero della Cultura – SITAP
- **Pagina:** https://sitap.cultura.gov.it/ (descrizione: https://cultura.gov.it/sitap-sistema-informativo-territoriale-ambientale-e-paesaggistico)
- **Endpoint trovati nella pagina ufficiale e verificati:**
  - `https://sitap.cultura.gov.it/geoserver/sitap_ws_clone/wms` (156 strati)
  - `https://sitap.cultura.gov.it/geoserver/sitap_wms_bounce/wms` (33 strati)
- **Strati:** organizzati per regione, es. `lombardia_art136`, `lombardia_142_rispetto_fiumi`, `lombardia_142_rispetto_laghi`, `lombardia_142_boschi_e_foreste`, `LAZIO_art_136_c_d`, `LAZIO_art142_g_boschi`, `LAZIO_art_142_fascia_150m_fiumi`, `v_geo_anagrafica_beni_poligonali`, `unesco_official_2026_polygon_core` …
- **Prova:** GetFeatureInfo `application/json` (WMS 1.1.1). Magenta: nessun elemento negli strati Lombardia provati. Controllo Bellagio: `lombardia_142_rispetto_laghi` → "Como (Lago di)". `lombardia_art136` a Bellagio non restituisce nulla: da capire in Fase 3.
- **Limiti:** copertura molto diversa da regione a regione; SITAP dichiara di avere "carattere meramente informativo" e nessun valore certificativo.
- **Licenza:** GetCapabilities "Fees: NONE, AccessConstraints: NONE"; nessuna licenza esplicita sul sito.
- **WFS (verificato il 23/11/2026, Fase 3):** `https://sitap.cultura.gov.it/geoserver/sitap_ws_clone/wfs` e `.../sitap_wms_bounce/wfs` (WFS 2.0.0, `outputFormat=application/json`, `srsName=EPSG:4326`). Il bbox va dato come `ovest,sud,est,nord,EPSG:4326` (lon, lat): con l'ordine opposto risponde 0 oggetti senza errore. Alcuni strati hanno coordinate con quota (x, y, z). Gli strati `v_geo_anagrafica_beni_*` rispondono errore 400.
- **Lombardia, contenuto:** `lombardia_art136` (332 decreti), `lombardia_art136_perimetri` (555), `lombardia_136_difficile_cartografazione`, `lombardia_142_*` (fiumi, laghi, boschi, montagne, ghiacciai, zone umide). **Mancano i parchi regionali (art. 142 lett. f)**: si usa EUAP (§8 bis).
- **Data dei dati:** non dichiarata dalla fonte.

## 10. Ministero della Cultura – Vincoli in Rete
- **Pagina:** https://cultura.gov.it/vincoli-in-rete-ricerca-sia-di-tipo-alfanumerico-che-cartografico
- **Esito:** nessun WMS/WFS/API pubblico trovato; il sito apre su un'area riservata. Fonte da citare: "Istituto Superiore per la Conservazione ed il Restauro – MiC". In parte coperto da SITAP (`v_geo_anagrafica_beni_*`, `Beni_monumentali_art_10_tutela_indiretta`).

## 11. Regione Lazio – Geoportale (PTPR)
- **Endpoint verificato:** `https://geoportale.regione.lazio.it/geoserver/ows?service=WFS&version=1.1.0&request=GetCapabilities` (254 strati)
- **Strati utili:** PTPR Tavola B (beni paesaggistici), es. `geonode:aree_archeologiche`, `geonode:boschi`, `geonode:ex_1497_ab`, `geonode:decreti_archeologici`, `geonode:aree_naturali_protette1`; Tavola A `geonode:rispetto_5_vincoli`.
- **Non presente:** strato dei siti contaminati.
- **Licenza / data:** da verificare. Interrogazione puntuale non ancora provata (Fase 3, caso Tuscia).

## 12. Regione Lombardia – siti contaminati e bonificati
- **Pagine:** https://www.dati.lombardia.it/d/npku-858g (contaminati) e https://www.dati.lombardia.it/d/macq-ggfu (bonificati)
- **Endpoint verificati:** `https://www.dati.lombardia.it/resource/npku-858g.json` e `.../macq-ggfu.json` (API Socrata, filtro `$where=upper(comune) like '%MAGENTA%'`)
- **Prova:** Magenta → 3 contaminati, 9 bonificati. **Novaceta, viale Piemonte 66 (MI130.0003) è nell'elenco dei bonificati**, mentre lo SIA (dic. 2025) e ARPA (mag. 2026) riportano bonifiche ancora aperte su parte del lotto.
- **Limiti:** **nessuna coordinata** (solo comune e indirizzo); dati al 31/12/2023, aggiornamento annuale. Va usato come segnale per comune, il criterio resta "da verificare" o manuale.
- **Licenza:** CC0 1.0.

## 13. Città Metropolitana di Milano – soggiacenza falda
- **Pagina:** https://www.dati.lombardia.it/d/u3wq-chcr ("Soggiacenza indicativa CMMI – Marzo 2022")
- **Endpoint verificato:** `https://www.dati.lombardia.it/resource/u3wq-chcr.json?$where=intersects(the_geom,'POINT (lon lat)')`
- **Prova:** Magenta → classe **5–7,5 m** (atteso dallo SIA: 3–8 m) → giallo.
- **Limiti:** solo Città Metropolitana di Milano; dato "indicativo", marzo 2022, non aggiornato. Nessun dato regionale equivalente trovato.
- **Licenza:** CC0.

## 14. ISPRA – MOSAICO (siti contaminati nazionali)
- **Pagina:** https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/siti-contaminati/anagrafe-dei-siti-da-bonificare – dichiara WMS e WFS pubblicati nel 2025, link nel catalogo metadati ISPRA.
- **Esito:** `https://mosaicositicontaminati.isprambiente.it/` non raggiungibile: certificato TLS non verificabile (errore del sito). Endpoint WMS/WFS non ancora trovati. Da riprovare.

## 15. Regione Lazio – siti contaminati
- **Esito:** `www.dati.lazio.it` non raggiungibile da qui; nel geoportale regionale nessuno strato dedicato. Criterio 6 nel Lazio: inserimento manuale per ora.

## 16. OpenStreetMap – Overpass API
- **Documentazione:** https://wiki.openstreetmap.org/wiki/Overpass_API
- **Endpoint provati:** `https://overpass-api.de/api/interpreter` (connessione chiusa dal server), `overpass.kumi.systems` e `overpass.private.coffee` (timeout), `maps.mail.ru/osm/tools/overpass` (raggiunto ma "server too busy"), `overpass.osm.jp` (502).
- **23/11/2026:** `overpass.kumi.systems` ha risposto 504 (sovraccarico), `overpass-api.de` connessione chiusa. Il connettore (`backend/controlli.py`) è pronto e provato con una risposta di prova; va provato dal vivo sul computer locale.
- **Diagnosi:** la rete di questo ambiente è senza restrizioni e `api.openstreetmap.org` e Nominatim rispondono; il blocco è lato server Overpass verso indirizzi cloud. **Da riprovare dal computer di Simone** prima della Fase 3.
- **Alternative se resta bloccato:** estratto OSM regionale scaricato una volta (es. Geofabrik) e interrogato in locale.
- **Licenza:** ODbL 1.0, citare "© OpenStreetMap contributors".

## 17. OpenStreetMap – Nominatim (geocodifica)
- **Endpoint verificato:** `https://nominatim.openstreetmap.org/search?q=...&format=json`
- **Prova:** "Viale Piemonte 66, Magenta" → trova la via (45,46593, 8,87352), non il civico.
- **Regole d'uso:** massimo 1 richiesta al secondo, User-Agent identificativo, cache obbligatoria. Licenza ODbL.
- **Uso in Fase 2:** riquadro (`boundingbox`) del comune per cercare i fogli catastali; cache 180 giorni, pausa di 1,1 s tra le richieste.
- **Sfondo della mappa:** tessere `https://tile.openstreetmap.org/{z}/{x}/{y}.png` (verificate, uso leggero consentito con attribuzione). Il WMS del catasto non supporta EPSG:3857 (provato: errore), quindi i confini si disegnano dal WFS.

## 18. GSE – Atlaimpianti (teleriscaldamento)
- **Pagina:** https://www.gse.it/dati-e-scenari/atlaimpianti – "attualmente non disponibile poiché in fase di aggiornamento"; `atla.gse.it` non risponde.
- **Contenuto:** impianti incentivati dal GSE; **le reti di teleriscaldamento non sono citate.**
- **Alternative trovate:** elenchi GSE dei "Sistemi di teleriscaldamento efficienti" 2022–2024 (PDF) da https://www.gse.it/servizi-per-te_site/efficienza-energetica_site/teleriscaldamento_site/Pagine/ELENCO-SISTEMI-EFFICIENTI.aspx; anagrafica ARERA delle reti. Da valutare in Fase 3; per ora criterio 13 manuale/informativo.

## 19. Terna – dati statistici (mix elettrico)
- **Pagina verificata:** https://www.terna.it/it/sistema-elettrico/statistiche/pubblicazioni-statistiche → rimanda a `https://dati.terna.it/generazione/dati-statistici#produzione/energia-elettrica-fonte`
- **Dati 2025 letti nella pagina (Ufficio statistico Terna):** domanda 312,2 TWh; produzione lorda 277,1 TWh (+2,3%); termoelettrico non rinnovabile 51,1%; fotovoltaico oltre 45 TWh (+25%); idroelettrico 43,7 TWh (−20,1%); import netto 46,9 TWh.
- **Limiti:** il portale dati.terna.it è in JavaScript, file scaricabili e licenza non ancora trovati. Il fattore di `engine.js` (~0,67 L/kWh, "Rete Italia 2025") va ricontrollato con questi numeri in Fase 1.

## 21. ISTAT – Elenco dei comuni italiani
- **Endpoint verificato (23/11/2026):** `https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv` (CSV, codifica Latin-1, separatore `;`, 7.896 comuni).
- **Colonne usate:** "Denominazione in italiano", "Sigla automobilistica", "Codice Catastale del comune" (es. Magenta → E801), "Codice Comune formato alfanumerico", "Denominazione Regione".
- **Uso:** dal nome del comune al codice catastale. Nomi doppi (es. San Teodoro ME/SS): si chiede la provincia.
- **Licenza:** da verificare (la pagina note legali ISTAT non si legge senza browser). Cache locale 30 giorni.

## 20. Destinazione urbanistica
- Nessuna fonte nazionale: PGT/PRG comunali spesso in PDF. Inserimento manuale in Fase 1–3, come previsto da SPEC.
