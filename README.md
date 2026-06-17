# Fixool Site OS Light

Versione leggera per testare sul campo un modello operativo di coordinamento cantieri Fixool.

## Cosa fa

- Gestione cantieri
- Anagrafica artigiani / squadre
- Attività con fase, responsabile, scadenza, stato, priorità e dipendenze
- Ticket per blocchi, richieste decisione, materiali, difetti, extra lavori e rischi ritardo
- Assistente leggero di smistamento: incolli un messaggio dal campo e propone tipo ticket, priorità e impatto
- Report giornaliero interno e versione cliente
- Dashboard KPI
- Export CSV

## Installazione rapida

1. Estrai lo ZIP in una cartella del PC.
2. Apri il Prompt dei comandi o PowerShell nella cartella estratta.
3. Installa i requisiti:

```bash
python -m pip install -r requirements.txt
```

4. Avvia l'app:

```bash
python -m streamlit run app.py
```

5. Si aprirà il browser con l'applicazione.

## Note operative

- Il database viene creato automaticamente nel file `fixool_site_os.db` nella stessa cartella dell'app.
- Al primo avvio vengono caricati dati demo.
- Per un test reale, puoi svuotare il database da `Impostazioni` e creare un cantiere vero.
- Questa versione non ha login, permessi, cloud o integrazione WhatsApp. Serve per validare il processo.

## Come testarlo sul campo

Per 1 cantiere pilota:

1. Crea il cantiere.
2. Inserisci gli artigiani coinvolti.
3. Crea 15-25 attività principali con scadenze e responsabili.
4. Ogni messaggio rilevante ricevuto da WhatsApp va copiato in `Ticket / Assistente`.
5. Ogni blocco va trasformato in ticket con responsabile e scadenza.
6. A fine giornata genera il report interno.
7. Dopo 2 settimane esporta i dati e valuta: blocchi, ritardi, responsabilità, cause ricorrenti.

## Evoluzioni possibili

- Integrazione WhatsApp Business
- Login artigiani
- App mobile semplificata
- Notifiche automatiche
- Agente AI vero per classificazione, priorità e smistamento
- Vendor rating artigiani
- Dashboard marginalità / extra costi
