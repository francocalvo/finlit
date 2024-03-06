from logging import getLogger

from pgloader.engine import PostgresEngineCreator
from pgloader.ledger import Ledger
from pgloader.tables import available_tables
from pgloader.utils import create_parser, setup_logger


def main() -> int | None:
    parser = create_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    logger = getLogger()

    logger.debug("Arguments: %s", args)
    if not args.rebuild:
        logger.info("Only behavior is to rebuild the database.")

    logger.info("Starting the application.")
    logger.debug("Verbose mode is activated.")

    engine, _ = PostgresEngineCreator().create_engine(args)

    ledger = Ledger(args.ledger)

    for table_name, table_class in available_tables.items():
        table = table_class(ledger, engine, table_name)
        if args.rebuild:
            table.rebuild()
        else:
            table.build()

    return 0
