from __future__ import annotations

import os
import re
from dataclasses import dataclass
from decimal import Decimal

from playwright.sync_api import sync_playwright

from .models import PriceRange, SearchConfig, TrainResult

_SEARCH_URL = "https://biglietti.italotreno.com/it/booking/ricerca-treni"
_PRICE_RE = re.compile(r"da\s*(\d+[.,]\d{2})\s*€")

os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

_HEADERS = {
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}


@dataclass
class SearchResult:
    price_range: PriceRange
    trains: list[TrainResult]


def _build_search_url(cfg: SearchConfig, origin_code: str, dest_code: str) -> str:
    date_str = cfg.date.strftime("%d/%m/%Y")
    params = (
        f"osc={origin_code}"
        f"&dsc={dest_code}"
        f"&jt=single"
        f"&od={date_str}"
        f"&adt={cfg.passengers}"
        f"&yng=0&chd=0&snr=0&inf=0&pet=0&promo="
        f"&lang=it&startSearch=true"
    )
    return f"{_SEARCH_URL}?{params}"


def _parse_price(text: str) -> Decimal | None:
    m = _PRICE_RE.search(text)
    if m:
        raw = m.group(1).replace(",", ".")
        return Decimal(raw)
    return None


def _get_daily_min(page) -> Decimal | None:
    text = page.evaluate("() => document.body.innerText")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Biglietti Da" in line:
            for j in range(i, min(i + 5, len(lines))):
                price = _parse_price(lines[j])
                if price is not None:
                    return price
    return None


def _parse_results(page) -> list[TrainResult]:
    text = page.evaluate("() => document.body.innerText")
    lines = text.split("\n")

    trains: list[TrainResult] = []

    for i, line in enumerate(lines):
        line = line.strip()
        time_m = re.match(r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})$", line)
        if not time_m:
            continue

        dep = time_m.group(1)
        arr = time_m.group(2)
        duration = ""
        price = None

        for j in range(i + 1, min(i + 20, len(lines))):
            lj = lines[j].strip()
            dur_m = re.match(r"(\d+\s*h\s*\d*\s*min)", lj)
            if dur_m:
                duration = dur_m.group(1).strip()
            p = _parse_price(lj)
            if p is not None:
                price = p

        if price is not None:
            trains.append(
                TrainResult(
                    departure_time=dep,
                    arrival_time=arr,
                    duration=duration,
                    price=price,
                    price_label=f"da {price:.2f} €",
                )
            )

    return trains


def search_trains(cfg: SearchConfig, origin_code: str, dest_code: str) -> SearchResult:
    url = _build_search_url(cfg, origin_code, dest_code)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--ignore-certificate-errors"],
        )
        context = browser.new_context(
            locale="it-IT",
            timezone_id="Europe/Rome",
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.set_extra_http_headers(_HEADERS)

        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.body.innerText.includes('Elenco Treni')"
            " || document.body.innerText.includes('Non Disponibile')"
            " || document.body.innerText.includes('DATE SUCCESSIVE')",
            timeout=40000,
        )
        page.wait_for_timeout(1000)

        daily_min = _get_daily_min(page)
        trains = _parse_results(page)
        browser.close()

    if not trains:
        return SearchResult(
            price_range=PriceRange(
                min_price=Decimal(0),
                max_price=Decimal(0),
                train_count=0,
                daily_min=daily_min,
            ),
            trains=[],
        )

    prices = [t.price for t in trains]
    return SearchResult(
        price_range=PriceRange(
            min_price=min(prices),
            max_price=max(prices),
            train_count=len(trains),
            daily_min=daily_min,
        ),
        trains=trains,
    )
