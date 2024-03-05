"""
Utility functions and classes that are used throughout the project.
"""
from argparse import ArgumentParser, BooleanOptionalAction
from logging.config import dictConfig
from pathlib import Path


def setup_logger(verbose: bool) -> None:
    """
    Set up the logger for the application.
    """
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s",  # noqa: E501
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "default": {
                    "level": "INFO" if not verbose else "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                }
            },
            "root": {
                "level": "INFO" if not verbose else "DEBUG",
                "handlers": ["default"],
            },
        }
    )


def create_parser() -> ArgumentParser:
    """
    Create an argument parser for the command line interface.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "--ledger",
        type=Path,
        dest="ledger",
        required=True,
        help="Path to the ledger file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        required=False,
        action=BooleanOptionalAction,
        help="Verbose flag for debugging purposes",
    )

    parser.add_argument(
        "--rebuild",
        "-r",
        dest="rebuild",
        required=False,
        action=BooleanOptionalAction,
        help="Verbose flag for rebuild database",
    )

    return parser
