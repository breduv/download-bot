import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from time import perf_counter
from typing import AsyncIterator, Iterable, Protocol

from aiogram import Bot
from prometheus_client import Counter, Gauge, Info, start_http_server


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
DOWNLOADS_TOTAL = Counter(
    "dw_bot_downloads_total",
    "Completed media download jobs grouped by media kind and result.",
    ("kind", "result"),
)
ACTIVE_DOWNLOADS = Gauge(
    "dw_bot_active_downloads",
    "Number of media download jobs currently being processed.",
)
DOWNLOAD_BYTES_TOTAL = Counter(
    "dw_bot_download_bytes_total",
    "Bytes produced by successful media download jobs.",
    ("kind",),
)
LAST_DOWNLOAD_SUCCESS = Gauge(
    "dw_bot_last_download_timestamp_seconds",
    "Unix timestamp of the latest successful media download job.",
)


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


@asynccontextmanager
async def track_download(kind: str) -> AsyncIterator[None]:
    """Track one low-cardinality download job without exposing user data."""
    ACTIVE_DOWNLOADS.inc()
    try:
        yield
    except asyncio.CancelledError:
        DOWNLOADS_TOTAL.labels(kind=kind, result="cancelled").inc()
        raise
    except Exception:
        DOWNLOADS_TOTAL.labels(kind=kind, result="failed").inc()
        raise
    else:
        DOWNLOADS_TOTAL.labels(kind=kind, result="success").inc()
        LAST_DOWNLOAD_SUCCESS.set_to_current_time()
    finally:
        ACTIVE_DOWNLOADS.dec()


def record_download_bytes(kind: str, paths: Iterable[Path | None]) -> None:
    total_bytes = 0
    for path in paths:
        if path is None:
            continue
        try:
            total_bytes += path.stat().st_size
        except OSError:
            logger.warning("Unable to read downloaded file size kind=%s", kind)

    if total_bytes > 0:
        DOWNLOAD_BYTES_TOTAL.labels(kind=kind).inc(total_bytes)


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
