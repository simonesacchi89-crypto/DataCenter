# Passaporto Acqua e Calore

Strumento locale per la **prefattibilità di un terreno per un data center**. Si fanno quattro passi:

1. **Il sito.** Cerchi comune + foglio + particelle oppure clicchi sulla mappa: compaiono i confini catastali e la superficie.
2. **Il progetto.** Indichi potenza IT, carico e raffreddamento. Lo strumento calcola energia, acqua diretta e indiretta e calore, anche sul clima reale del punto (PVGIS, 2005–2023).
3. **I controlli.** Interroga le fonti pubbliche: vincoli, alluvioni, frane, Natura 2000, sismica, rete elettrica, vicini. Ne esce un semaforo per ognuno dei 14 criteri, con fonte e data. In questo passo aggiungi anche foto e note sullo stato del sito.
4. **La scheda.** Riassunto stampabile (HTML o PDF) con i semafori e le domande da fare a Comune, Terna, ARPA e Soprintendenza.

> Prefattibilità indicativa. Non sostituisce certificato di destinazione urbanistica, richiesta di connessione a Terna, indagini in sito né il parere di un tecnico abilitato.

Un esempio completo sul caso reale di Magenta (ex Novaceta) è in `esempi/scheda_magenta_ex_novaceta.pdf`.

## Installazione (una volta sola)
Servono **Python 3.10 o successivo** e una connessione internet. Dalla cartella del progetto:

```bash
pip install -r requirements.txt
```

## Avvio
```bash
uvicorn backend.app:app
```
Poi apri http://127.0.0.1:8000 nel browser. Per provare subito: premi **"Caso reale: Magenta (SIA)"**, poi **Cerca** nel passo 1, e segui i passi.

## Test (facoltativi)
Servono anche **Node.js 18 o successivo**.
```bash
node --test tests/engine.test.js tests/scheda.test.js
```
```bash
python3 -m pytest tests/
```
I test in Python fanno chiamate reali ai servizi pubblici: richiedono la rete e qualche minuto.

## File principali
- `engine.js` – motore di calcolo di energia e acqua (verificato sui casi reali di `SPEC.md`)
- `backend/` – servizio locale (FastAPI) che interroga le fonti pubbliche e tiene una cache in `cache/`
- `frontend/` – la pagina e il generatore della scheda
- `FONTI.md` – ogni fonte con endpoint verificato, data della prova e licenza
- `DIARIO.md` – cosa è stato fatto in ogni fase e cosa resta aperto
- `SPEC.md` – requisiti e casi di test

## Limiti noti
- Rete elettrica e vicini sensibili usano OpenStreetMap (Overpass), che può essere lento o non raggiungibile: in quel caso il criterio è "da verificare".
- La foto aerea nazionale più recente è del 2012.
- Le soglie dei semafori sono ipotesi iniziali da tarare.
