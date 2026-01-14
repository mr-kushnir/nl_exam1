# NLExam - Telegram Expense Tracker Bot

Telegram-бот для учёта расходов с поддержкой естественного языка и голосовых сообщений.

## Возможности

- Добавление расходов текстом: `кофе 300`, `такси до работы 500р`
- Голосовые сообщения (распознавание через ElevenLabs)
- Автоматическая категоризация расходов
- Отчёты по расходам за месяц
- Статистика по категориям

## Технологии

- **Python 3.12** + FastAPI + python-telegram-bot
- **YaGPT** - парсинг расходов из естественного языка
- **ElevenLabs** - распознавание голосовых сообщений
- **Yandex Cloud**:
  - Serverless Containers - хостинг
  - YDB - база данных
  - Container Registry - хранение образов
  - Object Storage (S3) - файлы

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone https://github.com/mr-kushnir/nl_exam1.git
cd nl_exam1

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:

```env
# Telegram
BOT_TOKEN=your_telegram_bot_token

# Yandex Cloud
YC_TOKEN=your_yandex_cloud_oauth_token
YC_FOLDER_ID=your_folder_id

# ElevenLabs (опционально, для голосовых)
ELEVENLABS_API_KEY=your_elevenlabs_key

# YDB (опционально, для production)
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/xxx/xxx
```

### 3. Запуск локально (polling mode)

```bash
python -m src.bot.main
```

### 4. Запуск тестов

```bash
# Все тесты
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ --cov=src --cov-report=term-missing

# Только BDD тесты
python -m pytest tests/steps/ -v
```

## Деплой в Yandex Cloud

### 1. Сборка Docker образа

```bash
VERSION=$(date +%Y%m%d-%H%M%S)
docker build -t cr.yandex/$YC_REGISTRY_ID/nlexam-bot:$VERSION .
```

### 2. Push в Container Registry

```bash
yc container registry configure-docker
docker push cr.yandex/$YC_REGISTRY_ID/nlexam-bot:$VERSION
```

### 3. Деплой Serverless Container

```bash
yc serverless container revision deploy \
    --container-id $YC_CONTAINER_ID \
    --image cr.yandex/$YC_REGISTRY_ID/nlexam-bot:$VERSION \
    --cores 1 \
    --memory 512MB \
    --concurrency 4 \
    --execution-timeout 30s \
    --service-account-id $YC_SERVICE_ACCOUNT_ID \
    --environment "BOT_TOKEN=$BOT_TOKEN,YDB_ENDPOINT=$YDB_ENDPOINT,..."
```

### 4. Настройка webhook

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://$CONTAINER_URL/webhook"
```

## Структура проекта

```
nlexam/
├── src/
│   ├── bot/
│   │   ├── handlers.py      # Обработчики команд бота
│   │   └── main.py          # Точка входа (FastAPI + webhook)
│   ├── services/
│   │   ├── yagpt_service.py      # Парсинг расходов через YaGPT
│   │   ├── elevenlabs_service.py # Распознавание голоса
│   │   └── expense_storage.py    # Хранение расходов
│   └── db/
│       └── ydb_client.py    # Клиент YDB
├── tests/
│   ├── features/            # BDD сценарии (.feature)
│   ├── steps/               # Step definitions
│   └── test_*.py            # Unit тесты
├── Dockerfile
├── requirements.txt
└── README.md
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и краткая справка |
| `/help` | Подробная справка |
| `кофе 300` | Добавить расход |
| `расходы` | Отчёт за месяц |
| `сколько на кофе` | Сумма по позиции |
| `топ расходов` | Топ категорий |

## Разработка

Проект использует BDD (Behavior-Driven Development) с pytest-bdd.

```bash
# Линтинг
ruff check src/

# Безопасность
bandit -r src/
pip-audit
```

## Лицензия

MIT
