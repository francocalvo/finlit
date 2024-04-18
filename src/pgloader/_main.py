from logging import getLogger

from sqlalchemy import text
from sqlalchemy.schema import CreateSchema

from pgloader.engine import PostgresEngineCreator
from pgloader.ledger import Ledger
from pgloader.tables import available_tables
from pgloader.utils import create_parser, setup_logger

SCHEMA = "fin"


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

    # Setting up the schema
    with engine.connect() as connection:
        logger.debug("Creating the schema '%s' if it doesn't exist.", SCHEMA)
        connection.execute(CreateSchema(SCHEMA, if_not_exists=True))
        connection.commit()

        # Creating user
        logger.debug("Creating the user 'grafanareader' if it doesn't exist.")
        dml_user = text(
            """
            DO
            $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grafanareader')
                THEN
                    CREATE USER grafanareader WITH PASSWORD :password;
                END IF;
            END
            $$;
            """
        )
        connection.execute(dml_user, {"password": args.grafanareader_password})
        connection.commit()

        # Give the user the right to read the schema
        logger.debug("Granting the user 'grafanareader' the right to read the schema.")
        dml_grant = text(
            f"""
            GRANT USAGE ON SCHEMA {SCHEMA} TO grafanareader;
        """
        )
        connection.execute(dml_grant)
        connection.commit()

        dml_grant = text(
            "GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO grafanareader;"
        )

        # Change the search path
        logger.debug("Changing the search path to '%s'.", SCHEMA)
        dml_search_path = text(f"ALTER ROLE grafanareader SET search_path TO {SCHEMA}")
        connection.execute(dml_search_path)
        connection.commit()

    return 0
