"""
Load the ledger file and store the entries, errors, and options.
"""

from typing import Dict, List, Tuple

from beancount.core.data import Directive
from beancount.loader import LoadError, load_file
from beancount.query.query import run_query


class Ledger:
    """
    Returns the entries, errors, and options from the ledger file.
    """

    entries: List[Directive]
    errors: List[LoadError]
    options: Dict[str, str]

    def __init__(self, ledger_path: str) -> None:
        """
        Load the ledger file and store the entries, errors, and options.
        """
        self.path = ledger_path
        entries, errors, options = load_file(self.path)

        self.entries = entries
        self.errors = errors
        self.options = options

    def run_query(
        self, query: str
    ) -> Tuple[List[Tuple[str, type]], List[Dict[str, type]]]:
        """
        Run the query on the entries and return the result.
        """
        return run_query(self.entries, self.options, query)


def ledger_hash(ledger: Ledger) -> int:
    """
    Return the hash of the ledger file.
    """
    return hash(ledger)
