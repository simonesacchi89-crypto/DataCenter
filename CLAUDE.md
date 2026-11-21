# Passaporto Acqua e Calore – prefattibilità siti per data center

## Chi sono e come lavorare con me
- Sono Simone, bid manager nelle gare pubbliche ICT. **Non sono uno sviluppatore.**
- Parlami in italiano, con passi piccoli. Prima di ogni fase dimmi cosa farai e cosa mi servirà vedere alla fine.
- Chiedimi conferma prima di: installare strumenti pesanti, creare account su servizi esterni, spendere soldi, pubblicare online.
- Quando qualcosa non funziona, spiegami il problema in parole semplici e proponi la soluzione.

## Cos'è il progetto
Uno strumento che, dato un terreno (indirizzo, coordinate oppure comune + foglio + particella) e un'ipotesi di data center (potenza IT, sistema di raffreddamento), produce:
1. una **scheda di prefattibilità** con un semaforo (verde / giallo / rosso) per ogni criterio e l'elenco delle domande da fare a comune e Terna;
2. il **calcolo di energia, acqua diretta, acqua indiretta (centrali elettriche) e calore di scarto**, con le classi A–G della bozza di etichetta UE.

I dettagli sono in `SPEC.md`. Leggilo tutto prima di iniziare.

## File già pronti
- `engine.js` – motore di calcolo acqua/energia già verificato su casi reali (AWS Rho-Pero, Magenta, Microsoft Milano). **Non cambiare la fisica senza dirmelo**: se lo modifichi, i casi di test in `SPEC.md` devono continuare a tornare.
- `calcolatore.html` – versione attuale del calcolatore, pagina singola. Usala come riferimento per interfaccia e testi.

## Regole sui dati (importanti)
- **Non inventare indirizzi di servizi web (endpoint), codici di strati o formati.** Per ogni fonte in `SPEC.md` trova la documentazione ufficiale, verifica che il servizio risponda davvero e scrivi in `FONTI.md` l'endpoint verificato, la data della prova e la licenza.
- Ogni dato mostrato nella scheda deve riportare **fonte e data di aggiornamento**.
- Se una fonte non risponde o non copre l'area, il criterio diventa **"da verificare"** (grigio), mai verde.
- Non raccogliere né mostrare dati personali dei proprietari dei terreni.
- La scheda deve riportare sempre: "Prefattibilità indicativa. Non sostituisce certificato di destinazione urbanistica, richiesta di connessione a Terna, indagini in sito né il parere di un tecnico abilitato."

## Scelte tecniche consigliate (semplici da mantenere)
- **Backend:** Python con FastAPI. Serve per interrogare i servizi pubblici (molti non accettano chiamate dirette dal browser) e per tenere una cache dei risultati.
- **Frontend:** una pagina HTML con mappa Leaflet; il calcolo resta in `engine.js` lato browser.
- **Prima tutto in locale** sul mio computer. La pubblicazione online la decidiamo dopo.
- Test automatici per `engine.js` (casi di `SPEC.md`) e per ogni connettore di dati (una particella nota per fonte).

## Ordine di lavoro
Segui le fasi di `SPEC.md` una alla volta. Alla fine di ogni fase: mostrami il risultato su un caso reale, aggiorna `FONTI.md` e scrivi in `DIARIO.md` cosa è stato fatto e cosa resta aperto.
