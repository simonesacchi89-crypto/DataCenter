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
