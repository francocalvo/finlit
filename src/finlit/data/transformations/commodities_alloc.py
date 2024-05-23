"""
HERE BE DRAGONS.

https://github.com/beancount/beanlabs/blob/master/beanlabs/compensation/net-worth-over-time.py#L91

I currently don't understand this code. I will need to come back to it later.
It's copied from the beancount repository by the author of beancount.

It returns the market value of the assets in the ledger file as a timeseries.
"""

import collections
import datetime
from logging import getLogger

from beancount.core import account_types, data, inventory, prices
from beancount.parser import options
from dateutil import rrule

from finlit.constants import INITAL_MONTH, INITAL_YEAR
from finlit.data.ledger import Ledger

logger = getLogger()


class NetworthHistory:
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
        # logger.debug("Initializing the NetworthTrajectory object.")

        self.ledger: Ledger = ledger

    def get_entries(self) -> None:
        acctypes = options.get_account_types(self.ledger.options)
        price_map = prices.build_price_map(self.ledger.entries)
        operating_currencies = ["USD"]

        net_worths_dict = collections.defaultdict(list)
        liabilities_dict = collections.defaultdict(list)
        assets_dict = collections.defaultdict(list)

        index = 0

        dtstart = datetime.datetime(INITAL_YEAR, INITAL_MONTH, 2).date()  # noqa: DTZ001
        dtend = datetime.datetime.now().date()  # noqa: DTZ005

        period = rrule.rrule(rrule.DAILY, dtstart=dtstart, until=dtend)

        commodities: list[data.Commodity] = []
        allocs: dict[data.Commodity, inventory.Inventory] = {}

        # Append new entries until the given date.
        while index < len(self.ledger.entries):
            entry = self.ledger.entries[index]
            new_entries.append(entry)
            index += 1

        # Simple global aggregation of all intervening postings to a single
        # inventory.
        for entry in data.filter_txns(new_entries):
            for posting in entry.postings:
                acctype = account_types.get_account_type(posting.account)
                if acctype in (acctypes.assets, acctypes.liabilities):
                    balance.add_position(posting)  # type: ignore[]
                    if acctype == acctypes.liabilities:
                        liabilities.add_position(posting)  # type: ignore[]
                    if acctype == acctypes.assets:
                        assets.add_position(posting)  # type: ignore[]
