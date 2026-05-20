from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import yaml

from .models import BotConfig, SearchConfig


def _load_yaml(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return yaml.safe_load(path.read_text())


def load_search_config(data: dict) -> SearchConfig:
    search = data.get("search", {})
    origin = search.get("origin")
    destination = search.get("destination")
    raw_date = search.get("date")
    passengers = search.get("passengers", 1)

    if not origin:
        raise ValueError("`search.origin` is required in config")
    if not destination:
        raise ValueError("`search.destination` is required in config")
    if not raw_date:
        raise ValueError("`search.date` is required in config")

    if isinstance(raw_date, date):
        parsed_date = raw_date
    else:
        parsed_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()

    if not isinstance(passengers, int) or passengers < 1:
        raise ValueError("`search.passengers` must be a positive integer")

    return SearchConfig(
        origin=origin,
        destination=destination,
        date=parsed_date,
        passengers=passengers,
    )


def load_bot_config(data: dict) -> BotConfig:
    bot = data.get("bot", {})
    token = bot.get("token")
    chat_id = bot.get("chat_id")
    schedule = bot.get("schedule")

    if not token:
        raise ValueError("`bot.token` is required in config")
    if not chat_id:
        raise ValueError("`bot.chat_id` is required in config")
    if not schedule:
        raise ValueError("`bot.schedule` is required in config")

    return BotConfig(token=token, chat_id=int(chat_id), schedule=schedule)


def load_config(path: str | Path) -> SearchConfig:
    return load_search_config(_load_yaml(path))


def load_full_config(path: str | Path) -> tuple[SearchConfig, BotConfig]:
    data = _load_yaml(path)
    return load_search_config(data), load_bot_config(data)
