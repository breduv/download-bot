import asyncio
import logging
from app.application import run_application
from app.core.logger import configure_logging


if __name__ == "__main__":
    configure_logging()
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    asyncio.run(run_application())