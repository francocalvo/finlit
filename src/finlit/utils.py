"""
Utility functions and classes that are used throughout the project.
"""

from argparse import ArgumentParser, BooleanOptionalAction
from logging.config import dictConfig
from pathlib import Path


def setup_logger(*, verbose: bool) -> None:
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

    # Add arguments for Postgres connection: host, port, user, password, database
    parser.add_argument(
        "--host",
        dest="host",
        help="Host for the Postgres database",
        default="localhost",
    )

    parser.add_argument(
        "--port",
        dest="port",
        help="Port for the Postgres database",
        default="5432",
    )

    parser.add_argument(
        "--user",
        dest="user",
        help="User for the Postgres database",
        default="postgres",
    )

    parser.add_argument(
        "--password",
        dest="password",
        help="Password for the Postgres database",
        default="postgres",
    )

    parser.add_argument(
        "--database",
        dest="database",
        help="Database name for the Postgres database",
        default="finances",
    )

    return parser


style_css = """
<style>

.reportview-container .sidebar-content {{
    padding-top: 0;
}}
.reportview-container .main .block-container {{
    padding-top: 0;
}}

/* Remove blank space at the center canvas */
.st-emotion-cache-z5fcl4 {
   position: relative;
   top: -62px;
   }

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 0rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
"""


def format_number(num: float, *, prefix: str = "", posfix: str = "") -> str:
    """
    Format a number to a human readable format.

    Args:
    ----
        num (float): Number to format.
        prefix (str): Prefix to add to the formatted number.
        posfix (str): Posfix to add to the formatted number.

    """
    million = 1000000
    thousand = 1000
    formatted = f"{num:.2f}"
    if num > million:
        formatted = (
            f"{num // million} M"
            if not num % million
            else f"{round(num / million, 1)} M"
        )
    elif num > thousand * 100:
        formatted = (
            f"{num // thousand} K"
            if not num % thousand
            else f"{round(num / thousand, 1)} K"
        )

    return f"{prefix}{formatted}{posfix}"
