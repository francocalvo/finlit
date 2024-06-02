"""
Base class for all datasets.
"""

from abc import ABC, abstractmethod
from typing import Any

from pandas import DataFrame

from finlit.constants import INITAL_MONTH, INITAL_YEAR
from finlit.data.ledger import Ledger


class Dataset(ABC):
    """
    Base class for all datasets.
    """

    def __init__(
        self,
        ledger: Ledger,
        table_name: str,
        first_available_year: int = INITAL_YEAR,
        first_available_month: int = INITAL_MONTH,
    ) -> None:
        """
        Initialize the table object.
        """
        super().__init__()
        self.table_name = table_name
        self.ledger = ledger
        self.first_available_year = first_available_year
        self.first_available_month = first_available_month

    @abstractmethod
    def build(self, **kwargs: dict[str, Any]) -> DataFrame:
        """
        Build the table in the database.
        """
