import logging
from pathlib import Path
import sys


def configure_logging(level: int = logging.INFO) -> None:
    log_format = "[%(asctime)s.%(msecs)03d] %(module)15s:%(lineno)-3d %(levelname)-7s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    console_formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format,
    )

    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("spotipy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)