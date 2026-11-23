# Casi di prova candidati – data center con VIA pubblica

Ricerca del 23/11/2026 sul portale VAS-VIA-AIA del Ministero dell'Ambiente (https://va.mite.gov.it). I data center con gruppi elettrogeni di emergenza oltre 50 MW termici passano dalla procedura statale (verifica di assoggettabilità tra 50 e 150 MWt, VIA oltre 150 MWt), quindi i documenti sono pubblici.
Ogni pagina e documento elencato qui è stato **aperto e controllato** il 23/11/2026. Il portale mostra un avviso di "servizio temporaneamente disabilitato per analisi di sicurezza informatica", ma pagine e PDF si leggono.

| # | Sito | Proponente | Procedura e stato | Pagina / documento verificato | Perché è utile |
|---|---|---|---|---|---|
| 1 | **Liscate (MI)** | Infrastructure Italia Land 6 S.r.l. | VIA conclusa (decreto positivo con prescrizioni); verifiche di ottemperanza in corso nel 2026 | https://va.mite.gov.it/it-IT/Oggetti/Info/10758 | caso **concluso**; tra i documenti ci sono le **planimetrie catastali** (prova diretta del passo 1) |
| 2 | **Bornasco (PV)** | Microsoft 4825 Italy S.r.l. | escluso dalla VIA; ottemperanza conclusa il 13/05/2025 ("Ottemperata") | https://va.mite.gov.it/it-IT/Oggetti/Info/8791 | caso in **area agricola della provincia di Pavia**, diverso da Magenta |
| 3 | **Settimo Milanese (MI)** – MIL03 | Microsoft 4825 Italy S.r.l. | SIA dicembre 2023, quadro progettuale | https://va.mite.gov.it/File/Documento/1022098 | completa il caso "Microsoft Milano" di SPEC con documenti di progetto |
| 4 | **Zibido San Giacomo (MI)** – Edificio A | Amazon Data Services Italy S.r.l. | SIA ottobre 2025; 19 generatori (16 × 2,8 MWe + 3 × 0,8 MW) | https://va.mite.gov.it/File/Documento/1360667 (sintesi non tecnica, 52 pagine) | secondo caso **AWS** dopo Rho-Pero |
| 5 | **Vimercate (MB)** | Kryalos SGR S.p.A. | VIA in istruttoria tecnica; 3 edifici, 133 generatori, circa 1.000 MWt; osservazioni fino all'11/11/2026 | https://va.mite.gov.it/it-IT/Oggetti/Info/11813 (Studio di Impatto Ambientale: https://va.mite.gov.it/File/Documento/1311397) | **campus molto grande**, in corso |
| riserva | Lacchiarella (MI) | Apto Italia S.r.l. | VIA in istruttoria tecnica; generatori 1.010 MWt; più ripubblicazioni 2025–2026 | https://va.mite.gov.it/it-IT/Oggetti/Info/11503 | molto grande, molto discusso |

## Cosa estrarre da ogni caso (per il confronto con lo strumento)
1. Particelle catastali e superficie del lotto → passo 1 (criterio 1).
2. Potenza IT, sistema di raffreddamento, consumi d'acqua, PUE dichiarato → calcolo (criterio 14).
3. Destinazione urbanistica, vincoli, pericolosità, bonifiche, falda → criteri 2–7.
4. Distanza dalla stazione Terna e linea di connessione → criteri 8–9.
5. Ricettori sensibili (abitazioni, scuole) e Natura 2000 → criteri 10–11.
6. Osservazioni e pareri (Comune, ARPA, Soprintendenza) → confronto con le domande della scheda.

## Limiti della ricerca
- Tutti i casi trovati al livello statale sono in **Lombardia** (Milano, Pavia, Monza e Brianza). Per altre regioni la ricerca non ha restituito procedure statali: nel Lazio (Colleferro) il progetto risulta ancora alla fase urbanistica (VAS), in Piemonte (Trino, Moncalieri) i progetti sono annunciati ma non ancora in VIA. I progetti più piccoli passano da procedure regionali o comunali, da cercare a parte.
- Le potenze sul portale sono **termiche dei generatori**, non potenza IT: la potenza IT va letta nei documenti di progetto.

---

## Caso 1 – Liscate (MI): confronto documenti ufficiali / strumento (23/11/2026)

Documenti usati (portale VIA, procedura 10758): relazione VIA (doc. 1117675, 1117683), relazione tecnica integrata (1203875), stima consumi idrici (1317489), inquadramento urbanistico ed estratto di mappa (1203892, 1117595), parere della Città Metropolitana di Milano (1221078).

| Aspetto | Documenti ufficiali | Strumento | Esito |
|---|---|---|---|
| Particelle | foglio 2, mappali 258 e 437 (codice E610) | trovate entrambe | ✅ |
| Superficie | **68.890 m²** da visura (2024) | **31.813 m²** (258 + 437 di oggi) | ❌ **il foglio è stato aggiornato il 09/11/2026**: la vecchia 437 è stata frazionata (la parte ovest oggi è la 692, 15.926 m²); con la 692 si arriva a 47.739 m²; circa 21.000 m² restano da chiarire (probabilmente la vecchia 258 verso est) |
| m²/MW (40 MW IT) | 1.722 → verde | 795 → giallo (con i numeri di oggi) | dipende dalla superficie, vedi sopra |
| Urbanistica | ambito produttivo | manuale | da inserire (verde) |
| Vincoli | il cavidotto non interessa aree vincolate; tre parchi regionali vicini (Agricolo Sud Milano, Adda Nord, Adda Sud) | aree boscate (art. 142 lett. g) a **141 m** dal lotto; aree protette EUAP non verificabili (Geoportale fuori servizio) | ⚠️ lo strumento trova un elemento in più (bosco vicino) che i documenti non citano per il lotto |
| Idraulica / frane | – | nessuna pericolosità | ✅ (nessuna segnalazione nei documenti) |
| Falda | soggiacenza **3–5 m** (SIA) → rosso | proposta **5–7,5 m** (Città Metropolitana, dato indicativo 2022) → giallo | ❌ il dato aperto è **meno prudente** del SIA |
| Siti contaminati | nessuna bonifica citata sul lotto | in comune: 1 sito contaminato (Air Liquide, via al Lago) | manuale; coerente |
| Rete elettrica | nuovo cavidotto di **9,93 km** | grigio (Overpass non raggiungibile) | con le soglie attuali sarebbe giallo (2–10 km) |
| Natura 2000 | ZSC "Sorgenti della Muzzetta" a **3,8 km**, richiesto lo screening di incidenza | grigio (Geoportale fuori servizio il 23/11: "Database connection failed") | **secondo caso con screening richiesto a 3–4 km** |
| Sismica | – | grigio (stesso guasto) | – |
| Acqua diretta | solo uffici e umidificazione: circa **550 m³/anno** (211 + 152 + 187 m³) | 0 m³ con circuito chiuso; WUE classe **A** (anche aggiungendo i 550 m³) | ✅ |
| Raffreddamento | chiller con condensatori remoti e recupero di calore | sistema "chiller ad aria, circuito chiuso" | ✅ |
| Energia | – | PUE 1,16 (ora peggiore 1,40), 407 GWh/anno | PUE non trovato nei documenti letti (la Città Metropolitana chiede una relazione PUE in italiano) |
| Acqua indiretta | non considerata | circa **273.000 m³/anno** (oltre il 99% dell'impronta idrica) | informazione che i documenti non danno |

### Cosa insegna
1. **Le particelle cambiano**: confrontare sempre la data di aggiornamento del foglio con la data dei documenti. Aggiunto nella pagina un avviso quando il foglio è stato aggiornato negli ultimi 12 mesi.
2. **Falda**: il dato di Città Metropolitana (classi indicative) può essere più ottimista dei rilievi del SIA. Tenere la proposta come modificabile e chiedere sempre i piezometri.
3. **Natura 2000**: a Magenta (3,4 km) e a Liscate (3,8 km) è stato chiesto lo screening di incidenza. La soglia di 1 km di SPEC sembra troppo stretta: proposta da discutere, giallo fino a 5 km.
4. **Servizi pubblici**: il 23/11 il Geoportale Nazionale era fuori servizio; lo strumento ha messo correttamente i criteri in grigio, non in verde.

---

## Caso 2 – Bornasco (PV), Microsoft "MIL05": confronto documenti ufficiali / strumento (23/11/2026)

Documenti usati (portale VIA, oggetto 8791): decreto direttoriale del 20/07/2023 (doc. 873141) e parere della Commissione tecnica VIA n. 751 del 29/05/2023 (873142), relazione tecnica delle integrazioni (821621), parere ARPA Lombardia (985661). Esito: **verifica di assoggettabilità – non sottoposto a VIA**, con prescrizioni (ottemperanza conclusa il 13/05/2025).

| Aspetto | Documenti ufficiali | Strumento | Esito |
|---|---|---|---|
| Particelle | foglio 14: 31 (61.375 m²), 32 (93.858), 370 (2.773, fuori comparto), 372 (7.345); totale 165.351 m² | trovata solo la **370** (2.810 m², **+1,3%**); 31, 32 e 372 **non esistono più** | ❌ foglio aggiornato il 07/05/2026: dopo l'intervento le particelle sono state frazionate (oggi 388, 389, 391, 392, 396, 398…). Seconda conferma del problema visto a Liscate |
| Superficie / m²/MW | circa 16 ha; potenza IT non indicata nei documenti letti (generatori: 61,5 MW termici nella prima fase) | non calcolabile | – |
| Urbanistica | ambito di trasformazione produttivo ATP1 del PGT, oggi seminativo, in Rete Ecologica Regionale | manuale | giallo/verde da inserire a mano |
| Vincoli | "non sono presenti elementi assoggettati alla tutela del Codice dei Beni Culturali e del Paesaggio" sull'area; parere del Ministero della Cultura agli atti | vincolo art. 136 "Paesaggio naturale e rurale, intero territorio di Zeccone" a **36 m**; area boscata (art. 142 g) a **3 m**; Parco Visconteo (art. 136) a 423 m (misure dalla particella 370, vicina al lotto) | ⚠️ coerente: nessun vincolo sul lotto, ma vincoli **entro 500 m** → giallo; lo strumento li elenca, i documenti letti no |
| Idraulica / frane | il reticolo idrico minore attraversa il sito (classe di fattibilità 4c lungo i corsi d'acqua) | nessuna pericolosità (mosaicatura ISPRA) | ⚠️ ISPRA non vede il reticolo minore: va detto nella nota |
| Falda | **3,2–3,4 m** dal piano campagna → rosso | manuale (fuori dalla Città Metropolitana di Milano) | da inserire: rosso |
| Rete elettrica | elettrodotti di alta tensione ai margini del comune; linea che attraversa il sito | grigio (Overpass) | atteso verde |
| Vicini | abitazioni a circa **200 m** (Zeccone) | grigio (Overpass) | atteso giallo |
| Natura 2000 | Riserva Garzaia di Porta Chiosa (SIC/ZSC/ZPS) a **1,7 km**; Garzaia della Carola a 3,3 km; screening di incidenza svolto | grigio (Geoportale fuori servizio) | con la nuova soglia di 5 km sarebbe **giallo**: coerente |
| Sismica | zona 3 | grigio (Geoportale fuori servizio) | atteso verde |
| Acqua | raffreddamento con acqua di **prima falda da 5 pozzi**, prelievo massimo **81 m³/h** (22,5 l/s), più acqua piovana recuperata; consumo annuo non indicato nei documenti letti | il modello non distingue la **fonte** dell'acqua (pozzi o acquedotto) | ⚠️ limite del modello: aggiungere "fonte dell'acqua" e il prelievo di picco |

### Cosa insegna
1. **Particelle rinumerate dopo l'autorizzazione** (secondo caso su due): lo strumento è pensato per siti *prima* del progetto, ma per verificare progetti già autorizzati servono i confini dei documenti, non i numeri di particella. Possibile miglioramento: caricare il perimetro del progetto (disegno o file) invece dei numeri.
2. **Vincoli entro 500 m**: lo strumento trova elementi vicini che i documenti non riportano per il lotto. È il comportamento voluto (prudente).
3. **Reticolo idrico minore**: la pericolosità idraulica ISPRA non comprende le rogge; aggiungere la nota.
4. **Fonte dell'acqua**: in Lombardia il raffreddamento con acqua di falda è frequente; il criterio 14 dovrebbe chiederla.

---

## Caso 3 – Vimercate (MB), campus ex IBM: confronto documenti ufficiali / strumento (23/11/2026)

Procedura VIA in istruttoria (oggetto 11813, 289 documenti). Documenti usati: sintesi non tecnica (doc. 1400562), Studio di Impatto Ambientale di settembre 2026 (1438137), screening di incidenza (1400547), relazione geologica (1400571), parere del Comune di Vimercate del 28/10/2026 (1442015) e controdeduzioni (1452113).

| Aspetto | Documenti ufficiali | Strumento | Esito |
|---|---|---|---|
| Particelle | 41 particelle sui fogli 6, 7, 22 e 23 (elenco nel parere del Comune) | **40 su 41** trovate; manca la 136 del foglio 6 (aggiornato il 13/04/2026) | ✅ |
| Superficie | superficie territoriale di progetto **193.036 m²**; intervento complessivo **281.094 m²** | somma delle particelle **298.844 m²** (+6% sull'intervento complessivo) | ✅ coerente (superficie grafica; le particelle comprendono anche parcheggi e aree di ricomposizione) |
| Potenza / m²/MW | **156 MW IT** (DC1 60 + DC2 60 + DC3 36) → 1.237 m²/MW sulla superficie territoriale | 1.916 m²/MW sulle particelle | ✅ verde in entrambi i casi |
| Urbanistica | ex area industriale IBM; "Ambito di Trasformazione" **in variante al PGT**; variante generale adottata a settembre 2026 | manuale | da inserire: **giallo** (serve variante) |
| Vincoli | parere del Comune dopo la **Commissione Paesaggio**; richieste su mitigazioni e schermature | vincolo art. 136 **"Nucleo abitato di Oreno… Villa Gallarati Scotti" a 163 m**; aree boscate (art. 142 g) a 25 m | ✅ giallo, coerente con l'attenzione paesaggistica del Comune |
| Idraulica / frane | nessuna criticità segnalata nei documenti letti | nessuna pericolosità | ✅ |
| Falda | **7,4–20,8 m**, media circa 15 m (piezometri 2024); oscillazione ±2 m | manuale (nessun dato aperto per la provincia di Monza e Brianza) | da inserire: verde (giallo nella parte sud, 7,4 m) |
| Siti contaminati | nessuna bonifica citata nei documenti letti | in comune 3 contaminati e 6 bonificati, nessuno è l'area ex IBM | coerente |
| Rete elettrica | due cavi interrati a 220 kV di **5,7 km** verso la futura stazione Terna di Vimercate | grigio (Overpass) | con le soglie attuali sarebbe giallo (2–10 km) |
| Natura 2000 | ZSC "Valle S. Croce e Valle del Curone" a **4,3 km**; **screening di incidenza presentato**; pareri dei parchi Valle del Lambro e Montevecchia | grigio (Geoportale fuori servizio) | **terza conferma** della soglia di 5 km: sarebbe giallo |
| Acqua diretta | chiller ad aria con free cooling, consumo "pressoché nullo": circa **185 m³/anno** (uffici) | stesso sistema; WUE classe **A** | ✅ |
| Energia | PUE non trovato nei documenti letti | PUE 1,15 (ora peggiore 1,39); 1.578 GWh/anno | – |
| Acqua indiretta | non considerata | circa **1,06 milioni di m³/anno** (oltre il 99,9% dell'impronta idrica) | informazione che i documenti non danno |
| Calore | predisposizione al recupero di calore se nascerà un teleriscaldamento a Vimercate | 1.408 GWh termici/anno; teleriscaldamento: informativo | ✅ coerente |

### Cosa insegna
1. È il caso più vicino all'uso vero (progetto non ancora autorizzato): **particelle e superficie tornano**.
2. **Vincoli**: lo strumento trova da solo il vincolo sul nucleo storico di Oreno, il tema paesaggistico su cui il Comune ha chiesto approfondimenti.
3. **Natura 2000**: terzo caso su tre con screening richiesto tra 3 e 5 km: confermata la taratura a 5 km.
4. Mancano dati aperti sulla **falda** fuori dalla Città Metropolitana di Milano.

---

## Riepilogo dei casi (23/11/2026)

| Criterio | Magenta | Liscate | Bornasco | Vimercate | Giudizio |
|---|---|---|---|---|---|
| Particelle trovate | 15/15 | 2/2 (ma frazionate dopo la VIA) | 1/4 (rinumerate dopo l'intervento) | 40/41 | ✅ per siti non ancora trasformati |
| Superficie | +0,02% | ❌ catasto cambiato | non verificabile | +6% | ✅ quando il catasto non è cambiato |
| Vincoli entro 500 m | verde (Soprintendenza critica) | bosco a 141 m | art. 136 a 36 m | art. 136 a 163 m | ⚠️ trova i vincoli cartografati, non i pareri |
| Natura 2000 | 3,4 km, screening | 3,8 km, screening | 1,7 km, screening | 4,3 km, screening | ✅ con la soglia a 5 km |
| Falda | 5–7,5 m (SIA 3–8) | 5–7,5 m (SIA **3–5**) | manuale (SIA 3,2–3,4) | manuale (SIA 7,4–20,8) | ❌ dato aperto scarso o ottimista |
| Acqua diretta / WUE | classe A | classe A | raffreddamento con acqua di falda (non modellato) | classe A | ✅ con un limite da colmare |
| Acqua indiretta | 99% dell'impronta | >99% | – | >99,9% | messaggio costante |
| Rete elettrica | grigio | grigio (cavidotto 9,9 km) | grigio (linea sul sito) | grigio (cavi 5,7 km) | da provare con Overpass in locale |
