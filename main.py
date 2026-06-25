import asyncio
import logging
import sys

from app.application import run_application
from app.core import get_settings, configure_logging


logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()

    try:
        settings = get_settings()
        configure_logging(getattr(logging, settings.log_level))
        asyncio.run(run_application(settings))
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return 0
    except Exception:
        logger.exception("Application stopped due to unhandled exception")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
