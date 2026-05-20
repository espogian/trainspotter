# Trainspotter

CLI tool and Telegram bot to check **Italo Treno** ticket availability and prices on a specific route and date.

## Features

- **CLI**: Search tickets by route and date, shows count and price range
- **Telegram Bot**: Scheduled search via cron expression with automatic report delivery to Telegram
- Detailed train list with times, duration and price (`--verbose` flag)
- YAML configuration

## Requirements

- Python 3.11+
- [Playwright](https://playwright.dev/python/) (Chromium)

## Installation

```bash
cd trainspotter

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv add pyyaml rich playwright apscheduler python-telegram-bot

# Install Chromium browser for Playwright
uv run playwright install chromium
```

In case of SSL errors on corporate networks:
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 uv run playwright install chromium
```

## Configuration

Copy the example file and edit it with your data:

```bash
cp config.yaml.example config.yaml
```

`config.yaml.example` contains placeholders; `config.yaml` is excluded from Git to avoid exposing tokens and chat IDs.

```yaml
search:
  origin: "Roma Termini"
  destination: "Milano Centrale"
  date: "2026-06-20"
  passengers: 1

bot:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
  chat_id: 123456789
  schedule: "35 17 * * *"
```

### `search` section

| Field | Description | Example |
|---|---|---|
| `origin` | Departure station | `Roma Termini`, `Napoli Centrale` |
| `destination` | Arrival station | `Milano Centrale`, `Torino Porta Susa` |
| `date` | Date in `YYYY-MM-DD` format | `2026-06-20` |
| `passengers` | Number of adult passengers | `1` |

Supported stations include all Italo stations (Roma Termini, Roma Tiburtina, Milano Centrale, Torino Porta Nuova, Napoli Centrale, Bologna Centrale, Firenze S.M.N., Venezia Mestre, etc.).

### `bot` section

| Field | Description | Example |
|---|---|---|
| `token` | Telegram bot token (from @BotFather) | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `chat_id` | Chat/user ID to receive reports | `123456789` |
| `schedule` | Cron expression for scheduling | `35 17 * * *` (17:35) |

To get your `chat_id`, start `@userinfobot` on Telegram and send it a message.

### Sample cron expressions

| Time | Expression |
|---|---|
| Every day at 08:00 | `0 8 * * *` |
| Twice a day (08:00 and 18:00) | `0 8,18 * * *` |
| Every day at 17:35 | `35 17 * * *` |
| Every Monday at 09:00 | `0 9 * * 1` |

## Usage

### CLI (one-off)

```bash
# Basic search
PYTHONPATH=src uv run python -m trainspotter

# With custom config path
PYTHONPATH=src uv run python -m trainspotter -c path/to/config.yaml

# With detailed train list
PYTHONPATH=src uv run python -m trainspotter --verbose
```

On corporate networks with self-signed SSL certificates:
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter --verbose
```

### Telegram Bot (scheduled search)

```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 PYTHONPATH=src uv run python -m trainspotter.bot
```

The bot stays running and automatically sends reports at the configured time.

## CLI output example

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

## Telegram message example

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

## How it works

1. Loads configuration from YAML file
2. Resolves station codes via Italo's public API (`/api/v1/stations/list`)
3. Builds the search URL and navigates with Playwright headless
4. Waits for client-rendered results (React/Next.js)
5. Parses the page text to extract times, durations and prices
6. **CLI**: displays results in the terminal using `rich`
7. **Bot**: sends a formatted report to Telegram at scheduled time (APScheduler with cron expression)

## Project structure

```
trainspotter/
├── pyproject.toml              # Dependencies and metadata
├── config.yaml.example         # Example configuration template
└── src/
    └── trainspotter/
        ├── __init__.py
        ├── __main__.py          # CLI entry point
        ├── bot.py               # Telegram bot + APScheduler
        ├── models.py            # Dataclasses (SearchConfig, BotConfig, TrainResult, PriceRange)
        ├── config.py            # YAML loading and validation
        ├── stations.py          # Station name → station code mapping
        └── scraper.py           # Browser automation and result parsing
```

## Notes

- The tool uses Playwright in headless mode to bypass Akamai CDN bot protection.
- On corporate networks with self-signed SSL certificates, set `NODE_TLS_REJECT_UNAUTHORIZED=0`.
- Prices shown are starting prices per route and may vary based on fare type and selected services.
