"""
Dictionary of tables to be loaded in the database.
"""
from typing import Dict, Type

from pgloader.tables.all_bank_postings import AllBankPostingsTable
from pgloader.tables.all_expenses import AllExpensesTable
from pgloader.tables.all_income import AllIncomeTable
from pgloader.tables.all_postings import AllPostingsTable
from pgloader.tables.base_table import Table

available_tables: Dict[str, Type[Table]] = {
    "all_expenses": AllExpensesTable,
    "all_income": AllIncomeTable,
    "all_postings": AllPostingsTable,
    "all_bank_postings": AllBankPostingsTable,
}
