"""Command line: python3 -m m1_calc --data DATA/clean --parameters TEMPLATE.xlsx --ships SHIPS.csv|CASE.json --out OUTPUT

Exit codes: 0 = results written; 2 = an input could not be read (nothing written).
"""
import argparse
import sys
from pathlib import Path

from . import __version__
from .engine import value_ship
from .inputs import InputError, read_broker_values, read_parameters, read_sales, read_ships
from .outputs import write_results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="m1_calc", description="Value one ship or a list with the M1 comparable sales model.")
    p.add_argument("--data", required=True, type=Path, help="folder with sales.csv and indicative_prices.csv")
    p.add_argument("--parameters", required=True, type=Path, help="M1 template workbook whose Parameters sheet holds the settings")
    p.add_argument("--ships", required=True, type=Path, help="ships.csv (one row per ship) or a case .json")
    p.add_argument("--out", required=True, type=Path, help="folder for the results")
    a = p.parse_args(argv)
    try:
        sales = read_sales(a.data / "sales.csv")
        values = read_broker_values(a.data / "indicative_prices.csv")
        params = read_parameters(a.parameters)
        ships = read_ships(a.ships)
    except InputError as e:
        print(f"m1_calc {__version__}\nSTOPPED: {e}\nNothing written.")
        return 2
    results = [value_ship(s, sales, values, params) for s in ships]
    note = [f"data: {a.data}", f"parameters: {a.parameters.name}", f"ships: {a.ships.name}",
            f"sales: {len(sales)}; broker values: {len(values)}; ships: {len(ships)}"]
    run = write_results(results, a.out, note)
    print(f"m1_calc {__version__}")
    for r in results:
        v = f"${r.value_musd:.2f}m" if r.value_musd else "no value"
        print(f"  {r.ship.case_id:<10} {r.ship.target_name:<22} {v:>10}  {r.n_comparables:>3} comparables  {r.status}")
    print(f"written: {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
