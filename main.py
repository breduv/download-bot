import asyncio
import logging
from app.application import run_application
from app.core import get_settings, configure_logging


if __name__ == "__main__":
    settings = get_settings()
    configure_logging(level=getattr(logging, settings.log_level))
    asyncio.run(run_application(settings))