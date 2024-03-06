"""
EngineCreator class and its subclasses.
"""
import argparse
import csv
import logging
from abc import abstractmethod
from io import StringIO
from typing import List

from pandas.io.sql import SQLTable
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger()


class EngineCreator:
    """
    Abstract class for creating a SQLAlchemy engine.
    """

    def __init__(self) -> None:
        """
        Create EngineCreator class.
        """

    @abstractmethod
    def create_engine(self, args: argparse.Namespace) -> tuple[Engine, str]:
        """Create a SQLAlchemy engine."""


class PostgresEngineCreator(EngineCreator):
    """
    Create a PostgreSQL engine.
    """

    def __init__(self) -> None:
        """
        Create PostgresEngineCreator class.
        """
        super().__init__()

    def create_engine(self, args: argparse.Namespace) -> tuple[Engine, str]:
        """
        Create a PostgreSQL engine.
        """
        logger.info(
            [
                args.host,
                args.port,
                args.user,
                args.password,
                args.database,
            ]
        )

        conn_str = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}"
        engine = create_engine(conn_str, use_insertmanyvalues=True)

        # check if the connection is successful
        try:
            with engine.connect():
                logger.info("Connection to PostgreSQL is successful")
        except Exception as e:
            logger.exception("Connection to PostgreSQL failed.")
            raise e  # noqa: TRY201

        return engine, conn_str


def psql_insert_copy(
    table: SQLTable, conn: Engine | Connection, keys: List[str], data_iter: str
) -> None:
    """
    Execute SQL statement inserting data.

    Arguments:
    ---------
    table : pandas.io.sql.SQLTable
    conn : sqlalchemy.engine.Engine or sqlalchemy.engine.Connection
    keys : list of str
        Column names
    data_iter : Iterable that iterates the values to be inserted

    """
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.raw_connection() if isinstance(conn, Engine) else conn.connection

    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ", ".join(f'"{k}"' for k in keys)
        table_name = f"{table.schema}.{table.name}" if table.schema else table.name

        sql = f"COPY {table_name} ({columns}) FROM STDIN WITH CSV"
        cur.copy_expert(sql=sql, file=s_buf)
