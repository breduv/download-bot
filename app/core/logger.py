import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    log_format = "[%(asctime)s.%(msecs)03d] %(module)-18s:%(lineno)-4d %(levelname)-8s - %(message)s"
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

    logging.getLogger("aiogram").setLevel(level)
    logging.getLogger("asyncio").setLevel(level)
    logging.getLogger("spotipy").setLevel(level)
    logging.getLogger("urllib3").setLevel(level)
    logging.getLogger("gallery-dl").setLevel(level)