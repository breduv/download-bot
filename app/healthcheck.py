import os
import re
import sys
import time
from urllib.request import urlopen


def read_metric(body: str, name: str) -> float | None:
    match = re.search(rf"^{re.escape(name)}\s+([^\s]+)$", body, re.MULTILINE)
    return float(match.group(1)) if match else None


def main() -> int:
    port = int(os.getenv("METRICS_PORT", "9101"))
    interval = int(os.getenv("TELEGRAM_HEALTH_INTERVAL_SECONDS", "30"))

    try:
        with urlopen(f"http://127.0.0.1:{port}/metrics", timeout=3) as response:
            body = response.read().decode("utf-8")
    except Exception:
        return 1

    telegram_up = read_metric(body, "dw_bot_telegram_api_up")
    last_success = read_metric(
        body,
        "dw_bot_telegram_last_success_timestamp_seconds",
    )
    polling_up = read_metric(body, "dw_bot_polling_up")

    if telegram_up != 1 or polling_up != 1 or last_success is None:
        return 1

    maximum_age = max(interval * 3, 90)
    return 0 if time.time() - last_success <= maximum_age else 1


if __name__ == "__main__":
    sys.exit(main())
