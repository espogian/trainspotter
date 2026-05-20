from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

from .config import load_full_config
from .models import SearchConfig
from .scraper import search_trains
from .stations import resolve_station_code

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("trainspotter")


def _format_result(cfg: SearchConfig, result) -> str:
    r = result.price_range
    date_label = cfg.date.strftime("%d %b %Y")
    lines = [
        f"🚄 *{cfg.origin} → {cfg.destination}* | {date_label}",
        "",
    ]

    if r.train_count == 0:
        lines.append("Nessun treno disponibile per questa data.")
        return "\n".join(lines)

    lines.append(f"Treni disponibili: *{r.train_count}*")
    daily = r.daily_min or r.min_price
    if daily == r.min_price:
        lines.append(f"💰 Prezzo minimo: *€ {daily:.2f}*")
    else:
        lines.append(f"💰 Prezzo minimo: *€ {daily:.2f}*")
    lines.append(f"💰 Prezzo massimo: *€ {r.max_price:.2f}*")

    lines.append("")
    for t in sorted(result.trains, key=lambda x: x.departure_time):
        lines.append(
            f"`{t.departure_time} - {t.arrival_time}`  {t.duration}  *€ {t.price:.2f}*"
        )

    return "\n".join(lines)


async def _send_report(bot: Bot, chat_id: int, cfg: SearchConfig) -> None:
    try:
        origin_code = await asyncio.to_thread(resolve_station_code, cfg.origin)
        dest_code = await asyncio.to_thread(resolve_station_code, cfg.destination)
    except ValueError as e:
        await bot.send_message(chat_id=chat_id, text=f"❌ {e}")
        return

    try:
        result = await asyncio.to_thread(search_trains, cfg, origin_code, dest_code)
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"❌ Errore ricerca: {e}")
        log.error("Search failed", exc_info=True)
        return

    text = _format_result(cfg, result)
    await bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trainspotter Telegram Bot — ricerca schedulata Italo Treno"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Percorso del file YAML di configurazione (default: config.yaml)",
    )
    args = parser.parse_args()

    try:
        search_cfg, bot_cfg = load_full_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        log.error("❌ Errore configurazione: %s", e)
        sys.exit(1)

    http_request = HTTPXRequest(httpx_kwargs={"verify": False})
    bot = Bot(token=bot_cfg.token, request=http_request)
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        _send_report,
        CronTrigger.from_crontab(bot_cfg.schedule),
        args=[bot, bot_cfg.chat_id, search_cfg],
        id="trainspotter_report",
        name="Ricerca Italo Treno schedulata",
        replace_existing=True,
    )

    scheduler.start()
    log.info("Scheduler avviato con cron: %s", bot_cfg.schedule)

    # Startup notification
    cron_desc = bot_cfg.schedule
    await bot.send_message(
        chat_id=bot_cfg.chat_id,
        text=(
            f"🤖 *Trainspotter avviato*\n"
            f"Ricerca: {search_cfg.origin} → {search_cfg.destination}\n"
            f"Schedulazione: `{cron_desc}`"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        scheduler.shutdown(wait=False)
        log.info("Bot arrestato.")


if __name__ == "__main__":
    asyncio.run(main())
