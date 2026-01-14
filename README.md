# NLExam - Telegram Expense Tracker Bot

Telegram-бот для учёта расходов с поддержкой естественного языка и голосовых сообщений.

**Bot:** [@nlexambot](https://t.me/nlexambot)

## Возможности

### Учёт расходов
- Добавление расходов текстом в свободной форме
- Голосовые сообщения (Yandex SpeechKit)
- Автоматическая категоризация (12 категорий)
- Умное распознавание сумм на естественном языке

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

## Форматы ввода расходов

Бот понимает множество форматов записи расходов:

### Стандартные форматы
```
кофе 300
такси 500р
обед 1500
```

### Сумма в начале
```
500 рублей на такси
за 300 купил воду
отдал 1500 за доставку
```

### Разговорные суммы
```
маме отправил две тыщи      → 2000₽
сотка на проезд             → 100₽
штука на такси              → 1000₽
пятихатка за стрижку        → 500₽
косарь на продукты          → 1000₽
двадцатка за воду           → 20₽
```

### Сокращения и сленг
```
кофе 3 сотни                → 300₽
бенз на 2к                  → 2000₽
пиво 250р                   → 250₽
на карту жене 5к            → 5000₽
доширак 50 рэ               → 50₽
```

### Умножение количества
```
купил 2 кофе по 200         → 400₽
2 билета в кино 800         → 800₽
взял 5 булок по 45          → 225₽
обед на двоих 1500          → 1500₽
```

### С контекстом времени
```
вчера потратил 500 на еду   → 500₽
утром кофе 250              → 250₽
на прошлой неделе ремонт 15000 → 15000₽
```

### Сложные описания
```
заплатил за интернет и связь 900  → 900₽ (Связь)
скинулись на подарок шефу 500     → 500₽ (Подарки)
вернул долг Серёге 3000           → 3000₽ (Переводы)
подписка на яндекс плюс 300       → 300₽ (Подписки)
```

### Голосовые сообщения (STT)
```
"кофе триста рублей"        → 300₽
"такси пятьсот"             → 500₽
"эээ обед где-то тыща двести" → 1200₽
```

## Технологии

| Компонент | Технология |
|-----------|------------|
| Фреймворк | python-telegram-bot 22.x |
| Веб-сервер | FastAPI + uvicorn |
| NLP | YaGPT (Yandex GPT) |
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
# Все тесты (170 тестов)
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ --cov=src --cov-report=term-missing

# Только BDD тесты
python -m pytest tests/steps/ -v

# Тесты парсера
python -m pytest tests/test_parser_edge_cases.py -v
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
| Еда | кофе, обед, завтрак, ужин, продукты, ресторан |
| Транспорт | такси, метро, бензин, парковка, каршеринг |
| Развлечения | кино, бар, концерт, игры, пиво |
| Подписки | подписка, netflix, spotify, youtube, плюс |
| Здоровье | аптека, врач, спортзал, фитнес |
| Подарки | подарок, цветы, букет |
| Образование | курсы, книги, обучение |
| Одежда | одежда, обувь, zara |
| Переводы | перевод, маме, другу, долг |
| Дом | квартира, аренда, ремонт, мебель |
| Связь | телефон, интернет, мтс |
| Другое | всё остальное |

## Тестирование

Проект использует BDD (pytest-bdd) и unit тесты.

### BDD Features (12)

- `expense_parsing.feature` - парсинг расходов
- `expense_storage.feature` - хранение данных
- `telegram_bot.feature` - команды бота
- `voice_recognition.feature` - голосовые сообщения
- `confirmation_flow.feature` - подтверждение расходов
- `time_reports.feature` - отчёты по времени
- `budget_management.feature` - управление бюджетом
- `expense_management.feature` - управление расходами
- `analytics.feature` - аналитика
- `bdd_sync.feature` - синхронизация BDD
- `integration_testing.feature` - интеграционные тесты
- `production_deployment.feature` - деплой

### Результаты

```
171 tests passed
Coverage: ~50%

Parser edge cases: 48 tests
- Разговорные суммы: 8 tests
- Сленг и сокращения: 6 tests
- Неоднозначные формулировки: 5 tests
- Сумма в начале: 3 tests
- С датой/временем: 3 tests
- Сложные описания: 4 tests
- Граничные случаи: 7 tests
- STT артефакты: 3 tests
```

## Безопасность

```bash
# SAST
python -m bandit -r src/

# Зависимости
pip-audit
```

SQL Injection защита: параметризованные запросы в YDB клиенте.

## Лицензия

MIT
