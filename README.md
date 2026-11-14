# In Sala — registro del monitor PS

Registra ogni 5 minuti i numeri del monitor pubblico del Pronto Soccorso del
GOM di Reggio Calabria (https://prontosoccorso.ospedalerc.it/areasLoginBridge/),
per costruire stime realistiche dei tempi di attesa per chi aspetta.

- `scrape.py` legge il monitor e aggiunge una riga al CSV del mese.
- `data/monitor_gom_AAAA-MM.csv` contiene i dati: un file per mese.
- `.github/workflows/monitor.yml` lo esegue ogni 5 minuti su GitHub Actions.

I dati sono solo i totali che l'ospedale pubblica già: nessun dato personale.
Il ticket di accesso temporaneo del monitor non viene salvato.

## Colonne

| colonna | significato |
| --- | --- |
| letto_utc, letto_roma | quando è stato letto il monitor |
| aggiornato_monitor | orario di aggiornamento mostrato dal monitor |
| rossi/arancioni/azzurri/verdi/bianchi_entrati | persone entrate per codice colore |
| totale_entrati | "Attualmente sono entrati n°" |
| in_attesa | "Sono in attesa n°" |
| affollamento | grado di affollamento indicato dal monitor |
| casi_24h | casi trattati nelle ultime 24 ore |

Prova manuale: `python scrape.py --dry-run`
