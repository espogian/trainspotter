from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from .config import load_config
from .models import SearchConfig
from .scraper import search_trains
from .stations import resolve_station_code

console = Console()


def run(cfg: SearchConfig, verbose: bool = False) -> None:
    origin_code = resolve_station_code(cfg.origin)
    dest_code = resolve_station_code(cfg.destination)

    date_label = cfg.date.strftime("%d %b %Y")
    console.print(
        f"\n[bold cyan]🚄 {cfg.origin} → {cfg.destination}[/] [white]|[/] [yellow]{date_label}[/]"
    )
    console.print("─" * 50)

    with console.status("[bold green]Cerco biglietti..."):
        result = search_trains(cfg, origin_code, dest_code)

    r = result.price_range

    if r.train_count == 0:
        console.print("[red]Nessun treno disponibile per questa data.[/]")
        return

    console.print(f"\n[white]Treni disponibili:[/] [bold]{r.train_count}[/]")

    daily = r.daily_min or r.min_price
    console.print(f"\n[green]💰 Prezzo minimo:[/] [bold]€ {daily:.2f}[/]")
    console.print(f"[red]💰 Prezzo massimo:[/] [bold]€ {r.max_price:.2f}[/]")

    if verbose:
        console.print(f"\n[bold underline]Dettaglio treni:[/]")
        table = Table(box=None, padding=(0, 2))
        table.add_column("Orario", style="cyan")
        table.add_column("Durata", style="white")
        table.add_column("Prezzo da", style="green", justify="right")

        for t in sorted(result.trains, key=lambda x: x.departure_time):
            table.add_row(
                f"{t.departure_time} - {t.arrival_time}",
                t.duration,
                f"€ {t.price:.2f}",
            )
        console.print(table)

    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica prezzi e disponibilità biglietti Italo Treno"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Percorso del file YAML di configurazione (default: config.yaml)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostra la lista completa dei treni con i prezzi",
    )
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Errore configurazione:[/] {e}")
        sys.exit(1)

    run(cfg, verbose=args.verbose)


if __name__ == "__main__":
    main()
