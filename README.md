# Trainspotter

Tool per verificare la disponibilità e i prezzi dei biglietti **Italo Treno** su una specifica tratta e data.

## Funzionalità

- **CLI**: Ricerca biglietti per tratta e data, mostra conteggio e range prezzi
- **Bot Telegram**: Ricerca schedulata via espressione cron con invio automatico del report su Telegram
- Lista dettagliata treni con orari, durata e prezzo (flag `--verbose`)
- Configurazione via file YAML

## Requisiti

- Python 3.11+
- [Playwright](https://playwright.dev/python/) (Chromium)

## Installazione

```bash
cd trainspotter

# Crea l'ambiente virtuale
uv venv

# Attiva l'ambiente virtuale
source .venv/bin/activate

# Installa le dipendenze
uv add pyyaml rich playwright apscheduler python-telegram-bot

# Installa il browser Chromium per Playwright
uv run playwright install chromium
```

In caso di errori SSL in reti aziendali:
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 uv run playwright install chromium
```

## Configurazione

Copia il file di esempio e modificalo con i tuoi dati:

```bash
cp config.yaml.example config.yaml
```

Il file `config.yaml.example` contiene placeholder; `config.yaml` è già escluso da Git per non esporre token e chat_id.

```yaml
search:
  origin: "Roma Termini"
  destination: "Milano Centrale"
  date: "2026-06-20"
  passengers: 1

bot:
  token: "IL_TUO_TOKEN_TELEGRAM"
  chat_id: 123456789
  schedule: "35 17 * * *"
```

### Sezione `search`

| Campo | Descrizione | Esempio |
|---|---|---|
| `origin` | Stazione di partenza | `Roma Termini`, `Napoli Centrale` |
| `destination` | Stazione di arrivo | `Milano Centrale`, `Torino Porta Susa` |
| `date` | Data nel formato `YYYY-MM-DD` | `2026-06-20` |
| `passengers` | Numero di passeggeri adulti | `1` |

Le stazioni supportate includono tutte le stazioni Italo (Roma Termini, Roma Tiburtina, Milano Centrale, Torino Porta Nuova, Napoli Centrale, Bologna Centrale, Firenze S.M.N., Venezia Mestre, etc.).

### Sezione `bot`

| Campo | Descrizione | Esempio |
|---|---|---|
| `token` | Token del bot Telegram (da @BotFather) | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `chat_id` | ID della chat/utente dove inviare i report | `123456789` |
| `schedule` | Espressione cron per la schedulazione | `35 17 * * *` (17:35) |

Per ottenere il `chat_id`, avvia il bot e invia un messaggio a `@userinfobot` su Telegram.

### Espressioni cron di esempio

| Orario | Espressione |
|---|---|
| Ogni giorno alle 08:00 | `0 8 * * *` |
| Due volte al giorno (08:00 e 18:00) | `0 8,18 * * *` |
| Ogni giorno alle 17:35 | `35 17 * * *` |
| Ogni lunedì alle 09:00 | `0 9 * * 1` |

## Utilizzo

### CLI (una tantum)

```bash
# Ricerca base
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter

# Con percorso config personalizzato
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter -c percorso/config.yaml

# Con lista dettagliata dei treni
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter --verbose
```

### Bot Telegram (ricerca schedulata)

```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter.bot
```

Il bot rimane in esecuzione e invia automaticamente i report all'ora configurata.

## Esempio di output CLI

```
🚄 Roma Termini → Milano Centrale | 20 Jun 2026
──────────────────────────────────────────────────

Treni disponibili: 31

💰 Prezzo minimo: € 29.90
💰 Prezzo massimo: € 79.90

Dettaglio treni:
  Orario           Durata        Prezzo da
  05:40 - 09:20    3 h 40 min      € 44.90
  06:30 - 09:45    3 h 15 min      € 39.90
  07:05 - 10:15    3 h 10 min      € 42.90
  ...
```

## Esempio di messaggio Telegram

```
🚄 Roma Termini → Milano Centrale | 20 Jun 2026

Treni disponibili: 31
💰 Prezzo minimo: € 29.90
💰 Prezzo massimo: € 79.90

05:40 - 09:20  3 h 40 min  € 44.90
06:30 - 09:45  3 h 15 min  € 39.90
07:05 - 10:15  3 h 10 min  € 42.90
...
```

## Come funziona

1. Carica la configurazione dal file YAML
2. Risolve i codici stazione tramite l'API pubblica di Italo (`/api/v1/stations/list`)
3. Costruisce l'URL di ricerca e naviga con Playwright headless
4. Attende il caricamento dei risultati renderizzati lato client (React/Next.js)
5. Esegue il parsing del testo della pagina per estrarre orari, durate e prezzi
6. **CLI**: mostra i risultati a terminale con `rich`
7. **Bot**: invia il report formattato su Telegram all'orario schedulato (APScheduler con espressione cron)

## Struttura del progetto

```
trainspotter/
├── pyproject.toml              # Dipendenze e metadati
├── config.yaml                 # Configurazione di default
└── src/
    └── trainspotter/
        ├── __init__.py
        ├── __main__.py          # Entry point CLI
        ├── bot.py               # Bot Telegram + scheduler APScheduler
        ├── models.py            # Dataclass (SearchConfig, BotConfig, TrainResult, PriceRange)
        ├── config.py            # Caricamento e validazione YAML
        ├── stations.py          # Mappa nomi stazioni → codici stazione
        └── scraper.py           # Automazione browser e parsing risultati
```

## Note

- Il tool utilizza Playwright in modalità headless per aggirare la protezione anti-bot del CDN Akamai.
- In reti aziendali con certificati SSL self-signed, impostare `NODE_TLS_REJECT_UNAUTHORIZED=0`.
- I prezzi visualizzati sono i prezzi di partenza per tratta e possono variare in base alla tariffa e ai servizi selezionati.
