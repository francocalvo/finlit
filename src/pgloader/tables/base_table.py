"""
Base class for all tables.
"""
from abc import ABC, abstractmethod

from sqlalchemy.engine import Engine

from pgloader.ledger import Ledger
from pgloader.utils import START_MONTH, START_YEAR


class Table(ABC):
    """
    Base class for all tables.
    """

    _schema = "fin"

    def __init__(  # noqa: PLR0913
        self,
        ledger: Ledger,
        engine: Engine,
        table_name: str,
        first_available_year: int = START_YEAR,
        first_available_month: int = START_MONTH,
    ) -> None:
        """
        Initialize the table object.
        """
        super().__init__()
        self.engine = engine
        self.table_name = table_name
        self.ledger = ledger
        self.first_available_year = first_available_year
        self.first_available_month = first_available_month

    @abstractmethod
    def drop(self) -> None:
        """
        Drop the table in the database.
        """

    @abstractmethod
    def create(self) -> None:
        """
        Create the table in the database.
        """

    @abstractmethod
    def build(self) -> None:
        """
        Build the table in the database.
        """

    @abstractmethod
    def rebuild(self) -> None:
        """
        Drop the table and create it again.

        It calls the create and build method.
        """
