"""
Dictionary of tables to be loaded in the database.
"""
from typing import Dict, Type

from pgloader.tables.all_expenses import AllExpensesTable
from pgloader.tables.base_table import Table

available_tables: Dict[str, Type[Table]] = {
    "all_expenses": AllExpensesTable,
}
