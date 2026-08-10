import asyncio
import logging
from dataclasses import dataclass
from threading import Thread
from time import perf_counter
from typing import Protocol

from aiogram import Bot
from prometheus_client import Gauge, Info, start_http_server


logger = logging.getLogger(__name__)

TELEGRAM_API_UP = Gauge(
    "dw_bot_telegram_api_up",
    "Whether the latest Telegram Bot API health check succeeded.",
)
TELEGRAM_LAST_SUCCESS = Gauge(
    "dw_bot_telegram_last_success_timestamp_seconds",
    "Unix timestamp of the latest successful Telegram Bot API health check.",
)
TELEGRAM_CHECK_DURATION = Gauge(
    "dw_bot_telegram_check_duration_seconds",
    "Duration of the latest Telegram Bot API health check.",
)
POLLING_UP = Gauge(
    "dw_bot_polling_up",
    "Whether the Telegram long-polling loop is expected to be running.",
)
BOT_INFO = Info("dw_bot", "Public identity of the Telegram bot.")


class StoppableServer(Protocol):
    def shutdown(self) -> None: ...

    def server_close(self) -> None: ...


@dataclass(frozen=True)
class MetricsServer:
    server: StoppableServer
    thread: Thread

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def start_metrics(port: int) -> MetricsServer:
    server, thread = start_http_server(port, addr="0.0.0.0")
    logger.info("Prometheus metrics server started port=%d", port)
    return MetricsServer(server=server, thread=thread)


async def monitor_telegram_api(bot: Bot, interval_seconds: int) -> None:
    while True:
        started_at = perf_counter()
        try:
            identity = await bot.get_me()
            TELEGRAM_API_UP.set(1)
            TELEGRAM_LAST_SUCCESS.set_to_current_time()
            BOT_INFO.info(
                {
                    "bot_id": str(identity.id),
                    "username": identity.username or "",
                },
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            TELEGRAM_API_UP.set(0)
            logger.exception("Telegram Bot API health check failed")
        finally:
            TELEGRAM_CHECK_DURATION.set(perf_counter() - started_at)

        await asyncio.sleep(interval_seconds)
