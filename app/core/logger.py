import logging
from pathlib import Path
import sys


def configure_logging(level: int = logging.INFO, log_file: str = "logs/logs.log") -> None:
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

    # ===== Файл =====
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(
        filename=log_file,
        mode="a",
        encoding="utf-8",
    )

    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format,
    )

    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)