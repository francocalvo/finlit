"""
Data extraction from a ledger file.

Most of the code is copied from the beancount repository by the author of beancount:
https://github.com/beancount/beanlabs/blob/master/beanlabs/compensation/net-worth-over-time.py#L91

It returns a DataFrame with the net worth of the user over time.
"""

from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from altair import pd
from beancount.core import convert, data, inventory, prices
from beancount.core.account import root

# from finlit.data.transformations.networth_history import project_missing_currencies
from finlit.data.datasets.networth_history import project_missing_currencies
from finlit.data.ledger import Ledger

INVESTMENT_PREFIX = "Assets:Inversiones"
MAIN_CURR = "USD"


class Asset(TypedDict):
    """
    Asset class.
    """

    ticker: str
    name: str
    asset_class: str
    portfolio: str
    nominales: float | None
    value: float | None
    meta: dict[str, str] | None


def create_asset(
    ticker: str,
    name: str,
    asset_class: str,
    portfolio: str,
    meta: dict[str, str] | None = None,
) -> Asset:
    """
    Create an asset with the given parameters.
    """
    return {
        "ticker": ticker,
        "name": name,
        "asset_class": asset_class,
        "portfolio": portfolio,
        "nominales": None,
        "value": None,
        "meta": meta,
    }


class PorfolioAssets:
    """
    LOL.
    """

    def __init__(
        self,
        ledger: Ledger,
    ) -> None:
        """
        Gimme that ledger.
        """
        self.ledger: Ledger = ledger

    def get_entries(self) -> dict[str, Asset]:
        """
        Get the entries.
        """
        price_map = prices.build_price_map(self.ledger.entries)

        today = datetime.now().date()  # noqa: DTZ005

        index = 0

        commodities: dict[str, Asset] = {}
        allocs: dict[str, inventory.Inventory] = {}

        # Append new entries until the given date.
        while index < len(self.ledger.entries):
            entry = self.ledger.entries[index]
            if isinstance(entry, data.Commodity) and entry.currency not in commodities:
                # commodities[entry.currency] = Asset[entry.currency, entry)
                meta = {
                    e: entry.meta[e]
                    for e in entry.meta
                    if e
                    not in ["name", "asset-class", "portfolio", "filename", "lineno"]
                }
                commodities[entry.currency] = create_asset(
                    entry.currency,
                    entry.meta.get("name", ""),
                    entry.meta.get("asset-class", ""),
                    entry.meta.get("portfolio", ""),
                    meta if meta else None,
                )
            if isinstance(entry, data.Transaction):
                for posting in entry.postings:
                    if root(2, posting.account) == INVESTMENT_PREFIX:
                        if posting.units.currency not in allocs:
                            allocs[posting.units.currency] = inventory.Inventory()
                        allocs[posting.units.currency].add_position(posting)  # type: ignore[]
            index += 1

        usd_proj_price_map = project_missing_currencies(
            price_map,  # type: ignore[]
            today,
            set(commodities.keys()),  # type: ignore[]
            MAIN_CURR,
        )

        del_currencies = [curr for curr in commodities if curr not in allocs]
        for curr in del_currencies:
            del commodities[curr]

        for curr, inv in allocs.items():
            nominales = inv.reduce(convert.get_units)
            nominal_units: Decimal | None = nominales.get_currency_units(curr).number

            if nominal_units and nominal_units > 0:
                value = inv.reduce(
                    convert.convert_position,
                    MAIN_CURR,  # type: ignore[]
                    usd_proj_price_map,  # type: ignore[]
                    today,  # type: ignore[]
                )  # type: ignore[]

                commodities[curr]["nominales"] = (
                    float(nominal_units) if nominal_units else 0
                )

                value_units: Decimal | None = value.get_currency_units(MAIN_CURR).number
                commodities[curr]["value"] = float(value_units) if value_units else 0
            else:
                del commodities[curr]
        return commodities

    def build(self) -> pd.DataFrame:
        """
        Build the DataFrame.
        """
        assets_dict = self.get_entries()
        portfolio = pd.DataFrame.from_dict(assets_dict, orient="index")
        sum_value = portfolio["value"].sum()
        weights = [value / sum_value for value in portfolio["value"]]
        portfolio["weight"] = weights

        return portfolio
