from __future__ import annotations

import json
import ssl
from urllib.request import Request, urlopen

_STATIONS_API = "https://api-biglietti.italotreno.com/api/v1/stations/list"
_CACHE: dict[str, str] | None = None


def _make_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _fetch_all_stations() -> dict[str, str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    body = json.dumps({"culture": "it-IT"}).encode()
    req = Request(
        _STATIONS_API,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    ctx = _make_ssl_context()
    with urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())

    name_to_code: dict[str, str] = {}
    for code, info in data.items():
        name = info.get("name", "").strip()
        if name and code:
            name_to_code[name.lower()] = code

    _CACHE = name_to_code
    return name_to_code


def resolve_station_code(name: str) -> str:
    mapping = _fetch_all_stations()
    key = name.strip().lower()

    exact = mapping.get(key)
    if exact:
        return exact

    for stored_name, code in mapping.items():
        if key in stored_name or stored_name in key:
            return code

    raise ValueError(
        f"Stazione '{name}' non trovata. "
        f"Usa il nome esatto (es. 'Roma Termini', 'Milano Centrale')."
    )
