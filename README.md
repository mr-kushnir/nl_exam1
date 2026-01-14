# NLExam - Telegram Expense Tracker Bot

Telegram-бот для учёта расходов с поддержкой естественного языка и голосовых сообщений.

**Bot:** [@nlexambot](https://t.me/nlexambot)

## Возможности

### Учёт расходов
- Добавление расходов текстом: `кофе 300`, `такси до работы 500р`
- Голосовые сообщения (Yandex SpeechKit)
- Автоматическая категоризация (9 категорий)
- Подтверждение перед сохранением

### Отчёты и статистика
- Расходы за сегодня (`/today`)
- Сравнение по неделям (`/week`)
- Отчёт за месяц (`расходы`)
- Топ категорий (`топ расходов`)
- Поиск по названию (`/find кофе`)

### Бюджет
- Установка месячного бюджета (`/budget 50000`)
- Отслеживание прогресса
- Предупреждения при 80% и превышении

### Управление
- Отмена последнего расхода (`/undo`)
- Экспорт в CSV (`/export`)

## Технологии

| Компонент | Технология |
|-----------|------------|
| Фреймворк | python-telegram-bot 22.x |
| Веб-сервер | FastAPI + uvicorn |
| NLP | YaGPT |
| Голос | Yandex SpeechKit |
| База данных | Yandex YDB |
| Хранилище | Yandex S3 |
| Хостинг | Yandex Serverless Containers |

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

# YDB (для production)
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/xxx/xxx
```

### 3. Запуск локально

```bash
# Polling mode (разработка)
python -m src.bot.main

# Webhook mode (production)
uvicorn src.bot.main:app --host 0.0.0.0 --port 8080
```

### 4. Запуск тестов

```bash
# Все тесты (122 теста)
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ --cov=src --cov-report=term-missing

# Только BDD тесты
python -m pytest tests/steps/ -v
```

## Деплой в Yandex Cloud

### Docker

```bash
# Сборка
docker build -t cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest .

# Push
yc container registry configure-docker
docker push cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest

# Деплой
yc serverless container revision deploy \
    --container-id $YC_CONTAINER_ID \
    --image cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest \
    --cores 1 --memory 512MB --concurrency 4
```

### Webhook

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://$CONTAINER_URL/webhook"
```

## Структура проекта

```
nlexam/
├── src/
│   ├── bot/
│   │   ├── handlers.py      # Обработчики команд
│   │   ├── keyboards.py     # Inline/Reply клавиатуры
│   │   └── main.py          # FastAPI + webhook
│   ├── services/
│   │   ├── yagpt_service.py      # Парсинг через YaGPT
│   │   ├── speech_service.py     # Yandex SpeechKit
│   │   └── expense_storage.py    # Хранение расходов
│   └── db/
│       └── ydb_client.py    # Клиент YDB
├── tests/
│   ├── features/            # 12 BDD сценариев
│   ├── steps/               # 12 step definitions
│   └── test_*.py            # Unit тесты
├── scripts/
│   └── youtrack_kb.py       # KB API клиент
├── Dockerfile
├── requirements.txt
├── CLAUDE.md                # Документация разработки
└── README.md
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и справка |
| `/help` | Подробная справка |
| `/today` | Расходы за сегодня |
| `/week` | Сравнение по неделям |
| `/budget` | Показать бюджет |
| `/budget 50000` | Установить бюджет |
| `/undo` | Отменить последний расход |
| `/export` | Экспорт в CSV |
| `/find кофе` | Поиск по названию |
| `кофе 300` | Добавить расход |
| `расходы` | Отчёт за месяц |
| `топ расходов` | Топ категорий |

## Категории

| Категория | Ключевые слова |
|-----------|----------------|
| Еда | кофе, обед, завтрак, ужин, продукты |
| Транспорт | такси, метро, бензин, парковка |
| Развлечения | кино, бар, концерт, игры |
| Подписки | netflix, spotify, youtube |
| Здоровье | аптека, врач, спортзал |
| Подарки | подарок, цветы |
| Образование | курсы, книги |
| Одежда | одежда, обувь |
| Другое | всё остальное |

## Тестирование

Проект использует BDD (pytest-bdd) и unit тесты.

### BDD Features

- `expense_parsing.feature` - парсинг расходов
- `expense_storage.feature` - хранение данных
- `telegram_bot.feature` - команды бота
- `voice_recognition.feature` - голосовые сообщения
- `confirmation_flow.feature` - подтверждение расходов
- `time_reports.feature` - отчёты по времени
- `budget_management.feature` - управление бюджетом
- `expense_management.feature` - управление расходами
- `analytics.feature` - аналитика

### Результаты

```
122 tests passed
Coverage: ~50%
```

## Безопасность

```bash
# SAST
python -m bandit -r src/

# Зависимости
pip-audit
```

## Лицензия

MIT
