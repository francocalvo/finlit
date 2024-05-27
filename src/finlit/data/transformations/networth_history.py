"""
HERE BE DRAGONS.

https://github.com/beancount/beanlabs/blob/master/beanlabs/compensation/net-worth-over-time.py#L91

I currently don't understand this code. I will need to come back to it later.
It's copied from the beancount repository by the author of beancount.

It returns the market value of the assets in the ledger file as a timeseries.
"""

import collections
import datetime
from collections.abc import Callable
from logging import getLogger
from typing import Set, Tuple

import pandas as pd
from beancount.core import account_types, convert, data, inventory, prices
from beancount.core.data import Currency
from beancount.parser import options
from dateutil import rrule

from finlit.constants import INITAL_MONTH, INITAL_YEAR
from finlit.data.ledger import Ledger

logger = getLogger()

INVESTMENT_PREFIX = "Assets:Inversiones"


# TODO: Refactor this class to add the balance, liabilities and assets as attributes of the class.
class NetworthHistory:
    """
    Table object for the income table.
    """

    def __init__(
        self,
        ledger: Ledger,
    ) -> None:
        """
        Initialize the table  object for the network trajectories.

        Keywords arguments:
        - ledger: Ledger object
        - table_name: str

        Important attribues:
        - interval: it's the amount of month prior to the current date that we want
            to consider.
        - interest_rate: the yearly rate of return
        - years: the amount of years we want to consider
        - dream: the amount of money we want to have in the future per month.
            it's converted to a yearly amount and then considered as yearly return.

        """
        self.ledger: Ledger = ledger

    def map_to_usd(self, inventory, currency, price_map, date) -> float:
        """
        Map the inventory to currency.

        Args:
        ----
          inventory: The inventory to map.
          currency: The currency to map to.
          price_map: The price map to use for conversion.
          date: The date at which to convert.

        """
        if inventory.is_empty():
            return 0.0
        converted = inventory.reduce(
            convert.convert_position,
            currency,
            price_map,
            date,
        )

        splitted = converted.split()
        single_currency = splitted.pop(currency)
        return single_currency.get_only_position().units.number

    def project_missing_currencies(
        self,
        price_map: prices.PriceMap,
        date: datetime.date,
        currencies: Set[Currency],
        target_currency: Currency,
    ) -> prices.PriceMap:
        """
        Project missing currencies to convert `commodities` to `target_currency`.

        We want to convert `currencies` to the currency `target_currency`, but the
        price_map may not contain all the necessary prices. For example, TWD has
        prices in USD, but we want to convert to CAD. TWD being a currency, it
        doesn't have a cost, so routines that convert from cost (e.g.,
        convert.get_value()) will not do their job. What we need to do is convert
        TWD to CAD via USD. The way we do this is by "projecting" the TWD/USD prices
        to TWD/CAD via USD/CAD. This is done iva prices.project().

        We don't want to project any more prices than we need to, howerver. This
        routine is very conservative and automatically finds the subset of
        commodities which will require projection, and automatically infers through
        which currencies it has the opportunity to project.

        Note that this function does not use date/time; if no rates are available to
        at the date required for conversion, the projection will have no effect.
        Therefore, projecting in this way does not guarantee that projection will
        completely success using the returned price map (you should assert). If it
        fails to do so, the solution is to ensure that the ledger contains all
        necessary prices.

        Args:
        ----
          price_map: The original price map to probe.
          date: The date at which to convert.
          currencies: The set of currencies you'd like to eventually convert, the
            subject of conversion.
          target_currency: The target currency to which you'd like to convert them.

        Returns:
        -------
          An updated price map containing projections to make this possible.

        """
        # Get a dictionary of which currency is priced in which other.
        priced_currencies = collections.defaultdict(set)
        for base, quote in price_map.keys():
            priced_currencies[base].add(quote)

        # Get a list of the currencies which have prices to the target currency.
        # This works partly because price maps are symmetrical (e.g., "USD" will
        # have all the currencies that are converted to it).
        available_currencies = priced_currencies[target_currency]
        # For all those remaining commodities, ensure that rates exist to
        # convert by value to the target currency, by projecting through
        # an available price conversion.
        projections = collections.defaultdict(list)
        for pos_currency in currencies:
            rate_date, rate = prices.get_price(
                price_map, (pos_currency, target_currency), date
            )
            if rate is None:
                # Find the available prices for this position.
                quote_currencies = priced_currencies[pos_currency]
                inter_currencies = available_currencies & quote_currencies
                for inter_currency in inter_currencies:
                    projections[inter_currency].append(pos_currency)

        # Apply the projections.
        proj_price_map = price_map
        for inter_currency, commodities in projections.items():
            proj_price_map = prices.project(
                proj_price_map,
                inter_currency,
                target_currency,
                commodities,  # type: ignore[]
            )

        return proj_price_map

    def add_to_inventories(
        self,
        entries,
        acctypes,
        balance,
        liabilities,
        assets,
        *,
        investments=False,
        filter_func: Callable | None = None,
    ) -> Tuple[inventory.Inventory, inventory.Inventory, inventory.Inventory]:
        """
        Create inventories for the balance sheet.

        Args:
        ----
          entries: The entries to process.
          acctypes: The account types map.
          balance: The balance inventory.
          liabilities: The liabilities inventory.
          assets: The assets inventory.
          investments: Whether to include investment accounts.
          filter_func: A filter function to apply to the postings.

        Returns:
        -------
          A tuple of the balance, liabilities and assets inventories.

        """

        filter_function = filter_func if filter_func is not None else lambda _: True

        for entry in data.filter_txns(entries):
            for posting in entry.postings:
                acctype = account_types.get_account_type(posting.account)

                # Check:
                # - if the account is an asset or liability
                # - if the account is an investment account when investments is True
                # - if the filter function returns True
                is_asset_or_liability = acctype in (
                    acctypes.assets,
                    acctypes.liabilities,
                )

                investments_filter = (
                    posting.account.startswith(INVESTMENT_PREFIX)
                    if investments
                    else True
                )

                is_valid = filter_function(posting)

                if is_asset_or_liability and investments_filter and is_valid:
                    balance.add_position(posting)  # type: ignore[]
                    if acctype == acctypes.liabilities:
                        liabilities.add_position(posting)  # type: ignore[]
                    if acctype == acctypes.assets:
                        assets.add_position(posting)  # type: ignore[]

        return balance, liabilities, assets

    def build_timeseries(
        self, *, investments: bool = False, filter_func: Callable | None = None
    ) -> pd.DataFrame:
        entries = self.ledger.entries
        _errors = self.ledger.errors
        options_map = self.ledger.options
        acctypes = options.get_account_types(options_map)
        price_map = prices.build_price_map(entries)
        operating_currencies = options_map["operating_currency"]

        net_worths_dict = collections.defaultdict(list)
        index = 0
        for entry in entries:
            if isinstance(entry, data.Transaction):
                dtstart = entry.date
                break

        dtstart = datetime.datetime(INITAL_YEAR, INITAL_MONTH, 2).date()  # noqa: DTZ001
        dtend = datetime.date.today()  # noqa: DTZ011

        period = rrule.rrule(rrule.DAILY, dtstart=dtstart, until=dtend)

        balance = inventory.Inventory()
        liabilities = inventory.Inventory()
        assets = inventory.Inventory()
        for dtime in period:
            date = dtime.date()

            # Append new entries until the given date.
            new_entries = []
            while index < len(entries):
                entry = entries[index]
                if entry.date >= date:
                    break
                new_entries.append(entry)
                index += 1

            # Simple global aggregation of all intervening postings to a single
            # inventory.
            balance, liabilities, assets = self.add_to_inventories(
                new_entries,
                acctypes,
                balance,
                liabilities,
                assets,
                investments=investments,
                filter_func=filter_func,
            )

            for _, currency in enumerate(operating_currencies):
                # Compute balance at market price values. This will convert all
                # commodities held at cost to their cost value, and others to the
                # priced value, if relevant prices exist. Only commodities which
                # aren't held at cost or which have no price conversion information
                # providing a conversion currency will remain.
                value_balance = balance.reduce(convert.get_value, price_map, date)  # type: ignore[]

                # Convert all contents to destination currency.
                proj_price_map = self.project_missing_currencies(
                    price_map,  # type: ignore[]
                    date,
                    {pos.units.currency for pos in value_balance},
                    currency,
                )

                balance_value = self.map_to_usd(balance, currency, proj_price_map, date)
                balance_liabilities = self.map_to_usd(
                    liabilities, currency, proj_price_map, date
                )
                balance_assets = self.map_to_usd(assets, currency, proj_price_map, date)

                net_worths_dict[currency].append(
                    (
                        date,
                        balance_value,
                        balance_liabilities,
                        balance_assets,
                    )
                )  # type: ignore[]

        first_date = (
            datetime.date(INITAL_YEAR, INITAL_MONTH, 1),
            net_worths_dict["USD"][0][1],
            net_worths_dict["USD"][0][2],
            net_worths_dict["USD"][0][3],
        )

        net_worths_dict["USD"] = [first_date] + net_worths_dict["USD"]
        pd_balance = pd.DataFrame.from_records(
            net_worths_dict["USD"],
            columns=["date", "net_worth", "liabilities", "assets"],
        )

        pd_balance["date"] = pd.to_datetime(pd_balance["date"])
        pd_balance["net_worth"] = pd_balance["net_worth"].astype(float)
        pd_balance["liabilities"] = pd_balance["liabilities"].astype(float)
        pd_balance["assets"] = pd_balance["assets"].astype(float)

        return pd_balance

    # @st.cache_data(
    #     hash_funcs={
    #         "finlit.data.transformations.networth_history.NetworthHistory": lambda x: (
    #             networth_hash(x.ledger)
    #         ),
    #     },
    # )
    def build(
        self, *, investments: bool = False, filter_func: Callable | None = None
    ) -> pd.DataFrame:
        """
        Build the dataframe for the network trajectories.

        Args:
        ----
            investments: bool

        """
        return self.build_timeseries(investments=investments, filter_func=filter_func)


def networth_hash(ledger: Ledger) -> int:
    """
    Return the hash of the ledger file.
    """
    return hash(frozenset([hash(ledger)]))


def project_missing_currencies(
    price_map: prices.PriceMap,
    date: datetime.date,
    currencies: Set[Currency],
    target_currency: Currency,
) -> prices.PriceMap:
    """
    Project missing currencies to convert `commodities` to `target_currency`.

    We want to convert `currencies` to the currency `target_currency`, but the
    price_map may not contain all the necessary prices. For example, TWD has
    prices in USD, but we want to convert to CAD. TWD being a currency, it
    doesn't have a cost, so routines that convert from cost (e.g.,
    convert.get_value()) will not do their job. What we need to do is convert
    TWD to CAD via USD. The way we do this is by "projecting" the TWD/USD prices
    to TWD/CAD via USD/CAD. This is done iva prices.project().

    We don't want to project any more prices than we need to, howerver. This
    routine is very conservative and automatically finds the subset of
    commodities which will require projection, and automatically infers through
    which currencies it has the opportunity to project.

    Note that this function does not use date/time; if no rates are available to
    at the date required for conversion, the projection will have no effect.
    Therefore, projecting in this way does not guarantee that projection will
    completely success using the returned price map (you should assert). If it
    fails to do so, the solution is to ensure that the ledger contains all
    necessary prices.

    Args:
    ----
      price_map: The original price map to probe.
      date: The date at which to convert.
      currencies: The set of currencies you'd like to eventually convert, the
        subject of conversion.
      target_currency: The target currency to which you'd like to convert them.

    Returns:
    -------
      An updated price map containing projections to make this possible.

    """

    # Get a dictionary of which currency is priced in which other.
    priced_currencies = collections.defaultdict(set)
    for base, quote in price_map.keys():
        priced_currencies[base].add(quote)

    # Get a list of the currencies which have prices to the target currency.
    # This works partly because price maps are symmetrical (e.g., "USD" will
    # have all the currencies that are converted to it).
    available_currencies = priced_currencies[target_currency]

    # For all those remaining commodities, ensure that rates exist to
    # convert by value to the target currency, by projecting through
    # an available price conversion.
    projections = collections.defaultdict(list)
    for pos_currency in currencies:
        rate_date, rate = prices.get_price(
            price_map, (pos_currency, target_currency), date
        )
        if rate is None:
            # Find the available prices for this position.
            quote_currencies = priced_currencies[pos_currency]
            inter_currencies = available_currencies & quote_currencies
            for inter_currency in inter_currencies:
                projections[inter_currency].append(pos_currency)

    # Apply the projections.
    proj_price_map = price_map
    for inter_currency, commodities in projections.items():
        proj_price_map = prices.project(
            proj_price_map,
            inter_currency,
            target_currency,
            commodities,  # type: ignore[]
        )

    return proj_price_map
