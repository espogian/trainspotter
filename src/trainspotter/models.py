from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class SearchConfig:
    origin: str
    destination: str
    date: date
    passengers: int = 1


@dataclass
class TrainResult:
    departure_time: str
    arrival_time: str
    duration: str
    price: Decimal
    price_label: str


@dataclass
class PriceRange:
    min_price: Decimal
    max_price: Decimal
    train_count: int
    daily_min: Decimal | None = None


@dataclass
class BotConfig:
    token: str
    chat_id: int
    schedule: str
