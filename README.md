<div align="center">

# DW Bot

**Telegram-бот для поиска и скачивания аудио, видео и фотогалерей**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.29-2CA5E0?logo=telegram&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2026.8.19-FF0000?logo=youtube&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-metrics-E6522C?logo=prometheus&logoColor=white)

Ищет треки по названию, разбирает ссылки популярных платформ, предлагает
доступные форматы и отправляет готовые медиафайлы прямо в Telegram.

</div>

---

## Возможности

| | |
| --- | --- |
| 🔎 **Поиск музыки** | Ищет треки через Spotify и показывает до 10 результатов |
| 🎧 **Готовое аудио** | Скачивает трек, конвертирует в MP3 и добавляет название, исполнителя и обложку |
| 🎬 **Выбор качества** | Показывает доступные разрешения YouTube и вариант «Только звук» |
| 🖼️ **Фотогалереи** | Отправляет TikTok-фотографии медиагруппами с учётом лимитов Telegram |
| 🍪 **Cookies для YouTube** | Повторяет запрос с cookies, если обычная загрузка или получение форматов завершились ошибкой |
| ⚡ **Inline-режим** | Принимает ссылки через `@username_бота <URL>` в любом чате |
| 🌐 **Раздельные прокси** | Поддерживает независимые прокси для Telegram и внешних медиасервисов |
| 📈 **Наблюдаемость** | Экспортирует Prometheus-метрики и проверяет доступность Telegram Bot API |
| 🐳 **Готовый контейнер** | В образ уже входят Python, FFmpeg, `ffprobe` и Deno |

## Поддерживаемые источники

| Источник | Что делает бот |
| --- | --- |
| Текстовый запрос | Ищет треки в Spotify и предлагает выбрать результат |
| Spotify | Получает метаданные, скачивает аудио и добавляет обложку |
| YouTube | Показывает разрешения видео и вариант «Только звук» |
| YouTube Shorts | Скачивает видео напрямую |
| YouTube Music | Скачивает аудио |
| TikTok | Раскрывает короткие ссылки, скачивает видео и фотогалереи |
| Instagram | Скачивает видео по публичной ссылке |
| Pinterest | Скачивает видео по публичной ссылке |
| VK / VK Видео | Скачивает клипы |

## Как это работает

```mermaid
flowchart LR
    A[Текст или URL] --> B[SearchService]
    B --> C{Источник}
    C -->|Поиск и метаданные| D[Spotify]
    C -->|Аудио и видео| E[yt-dlp]
    C -->|TikTok-галереи| F[gallery-dl]
    D --> G[DownloadService]
    E --> G
    F --> G
    G --> H[FFmpeg и обработка медиа]
    H --> I[Отправка в Telegram]
    I --> J[Очистка временного каталога]
```

Один запрос проходит следующие этапы:

1. `SearchService` определяет, является ввод поисковым запросом или ссылкой.
2. Для Spotify и обычных YouTube-видео бот формирует inline-клавиатуру выбора.
3. `DownloadService` направляет задачу подходящему провайдеру.
4. Провайдер скачивает файл и при необходимости запускает FFmpeg.
5. Бот проверяет размер, отправляет результат пользователю и очищает временные файлы.

Для YouTube первая попытка выполняется без cookies. Если `yt-dlp` возвращает
ошибку и файл cookies настроен, бот повторяет запрос с авторизацией. Это работает
как для загрузки медиа, так и для получения списка доступных разрешений.

## Быстрый старт

### 1. Создайте `.env`

```dotenv
BOT_TOKEN=telegram-bot-token
SPOTIFY_CLIENT_ID=spotify-client-id
SPOTIFY_CLIENT_SECRET=spotify-client-secret

# Файл внутри /app/data
COOKIES_FILE=youtube.cookies.txt

# Необязательно
MEDIA_PROXY=
TELEGRAM_PROXY=
LOG_LEVEL=INFO
SEARCH_LIMIT=5
MAX_UPLOAD_SIZE_MB=49
INLINE_CACHE_CHAT_ID=
METRICS_PORT=9101
TELEGRAM_HEALTH_INTERVAL_SECONDS=30
```

Файл `.env` исключён из Git и Docker build context. Не добавляйте токены и
секреты в репозиторий.

### 2. Подготовьте YouTube cookies

Текущий Compose монтирует серверный каталог `/home/gleb/dw_bot` внутрь
контейнера как `/app/data`:

```text
сервер:     /home/gleb/dw_bot/youtube.cookies.txt
контейнер:  /app/data/youtube.cookies.txt
```

Скопируйте Netscape-файл cookies на сервер и ограничьте доступ к нему:

```bash
chmod 600 /home/gleb/dw_bot/youtube.cookies.txt
```

Имя файла должно совпадать со значением `COOKIES_FILE`. Путь в переменной не
обязателен: конфигурация берёт имя и ищет файл именно в `/app/data`.

> **Безопасность:** cookies дают доступ к вашей YouTube-сессии. Используйте
> отдельный аккаунт, не публикуйте файл и регулярно обновляйте его.

### 3. Создайте monitoring-сеть

Сеть является внешней для Compose и создаётся на Docker-хосте один раз:

```bash
docker network create --driver bridge --internal monitoring
```

### 4. Запустите бота

```bash
docker compose up -d --build
docker compose logs -f download-bot
```

Проверить состояние контейнера:

```bash
docker inspect --format='{{.State.Health.Status}}' download-bot
```

Остановка:

```bash
docker compose down
```

## Настройки

| Переменная | По умолчанию | Назначение |
| --- | ---: | --- |
| `BOT_TOKEN` | — | Токен Telegram-бота от BotFather |
| `SPOTIFY_CLIENT_ID` | — | Client ID приложения Spotify |
| `SPOTIFY_CLIENT_SECRET` | — | Client Secret приложения Spotify |
| `COOKIES_FILE` | — | Имя Netscape-файла в `/app/data` для повторных YouTube-запросов |
| `MEDIA_PROXY` | — | Прокси для Spotify, `yt-dlp` и `gallery-dl` |
| `TELEGRAM_PROXY` | — | Прокси подключения к Telegram Bot API |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` или `CRITICAL` |
| `SEARCH_LIMIT` | `5` | Количество результатов Spotify, допустимо 1–10 |
| `MAX_UPLOAD_SIZE_MB` | `49` | Максимальный размер одного медиафайла |
| `INLINE_CACHE_CHAT_ID` | — | Чат или канал для служебной загрузки inline-медиа |
| `METRICS_PORT` | `9101` | Внутренний порт Prometheus-метрик |
| `TELEGRAM_HEALTH_INTERVAL_SECONDS` | `30` | Интервал проверки Telegram API, допустимо 10–300 секунд |
| `IMAGE_TAG` | `latest` | Тег Docker-образа, используемый Compose |

Обязательны `BOT_TOKEN`, `SPOTIFY_CLIENT_ID` и `SPOTIFY_CLIENT_SECRET`. В текущем
Docker Compose также следует задать `COOKIES_FILE`: пустое значение не является
именем файла и не пройдёт проверку конфигурации.

## Inline-режим

В BotFather включите:

1. Inline Mode командой `/setinline`.
2. Inline feedback командой `/setinlinefeedback`.
3. Для feedback выберите 100%, иначе бот будет получать не все события выбора.

После этого пользователь может написать:

```text
@username_бота <URL>
```

Бот покажет временный результат «Готовлю файл...», скачает медиа и заменит его
готовым файлом. Если `INLINE_CACHE_CHAT_ID` не задан, пользователь должен хотя бы
один раз открыть бота в личных сообщениях, чтобы Telegram разрешил служебную
загрузку.

## Мониторинг

Метрики доступны внутри сетей Docker на `METRICS_PORT` (`9101` по умолчанию).
Порт не публикуется на интерфейс Docker-хоста.

Пример Prometheus job:

```yaml
scrape_configs:
  - job_name: dw_bot
    scrape_interval: 15s
    static_configs:
      - targets: ["download-bot:9101"]
```

Основные метрики:

| Метрика | Значение |
| --- | --- |
| `dw_bot_polling_up` | Состояние Telegram long polling |
| `dw_bot_telegram_api_up` | Результат последней проверки Telegram Bot API |
| `dw_bot_telegram_last_success_timestamp_seconds` | Время последней успешной проверки |
| `dw_bot_telegram_check_duration_seconds` | Длительность последней проверки |
| `dw_bot_info` | Публичная информация о боте |

Docker healthcheck проверяет доступность endpoint метрик, состояние polling и
свежесть последнего успешного обращения к Telegram API.

## Структура проекта

```text
app/
├── bot/          # Обработчики Telegram, роутер и клавиатуры
├── core/         # Настройки и конфигурация логирования
├── errors/       # Прикладные исключения и публичные сообщения
├── models/       # Типы запросов и медиа
├── providers/    # Spotify, yt-dlp, gallery-dl и обработка обложек
├── services/     # Разбор запросов и координация скачивания
├── healthcheck.py
└── metrics.py
```

Точка входа — `main.py`. Загруженные файлы создаются во временных каталогах и
удаляются после отправки, поэтому постоянное хранилище медиа боту не требуется.

## Локальная разработка

Требования:

- Python 3.11 или новее;
- FFmpeg и `ffprobe` в `PATH`;
- Deno в `PATH` для JavaScript-компонентов `yt-dlp`;
- настроенный `.env`.

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

При локальном запуске `COOKIES_FILE=youtube.cookies.txt` указывает на файл:

```text
<корень проекта>/data/youtube.cookies.txt
```

Проверка синтаксиса:

```powershell
python -m compileall -q app main.py
```

## CI/CD

GitLab CI для ветки `main`:

1. Собирает образ `download-bot:<commit-sha>`.
2. Передаёт тег в deploy job через dotenv-артефакт.
3. Обновляет сервис без повторной сборки.
4. Удаляет неиспользуемые Docker-образы после успешного деплоя.

Runner должен иметь доступ к Docker daemon, внешней сети `monitoring`, каталогу
с cookies и рабочему Compose-проекту.

## Безопасность и ограничения

- Бот зависит от доступности Telegram, Spotify и структуры внешних сайтов.
- После изменений YouTube, TikTok и других платформ может потребоваться
  обновление `yt-dlp` или `gallery-dl`.
- Cookies помогают с авторизацией и возрастными ограничениями, но не дают доступ
  к удалённому контенту и материалам без прав аккаунта.
- Региональные ограничения могут потребовать `MEDIA_PROXY`.
- Telegram дополнительно ограничивает типы и размеры отправляемых файлов.
- Бот предназначен только для материалов, которые пользователь имеет право
  скачивать и распространять.

> **Важно:** не передавайте `.env`, cookies и прокси-учётные данные в логи,
> Docker-образы, Git или публичные каналы.

---

<div align="center">

Ищет · скачивает · обрабатывает · отправляет

</div>
