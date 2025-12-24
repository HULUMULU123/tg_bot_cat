# Telegram Game Mini-App Bot

Простой телеграм-бот на библиотеке **telebot (pyTelegramBotAPI)** с игровым меню и HTTP API для проверки подписки.

## Возможности
- Команда `/start` показывает юридическую информацию и просит принять правила.
- После принятия правил открывается приветствие и главное меню.
- Инлайн-меню с разделами: играть, правила, лор.
- Обработчики в отдельных модулях для удобства расширения.
- FastAPI сервер с эндпоинтами:
  - `POST /check-sub` для проверки подписки на канал по секрету API.
  - `POST /check-legal` для проверки, принял ли пользователь правила.
  - `POST /outages` для создания сбоя и напоминаний.

## Структура проекта
```
bot.py              # Точка входа: запускает telebot и HTTP API
config.py           # Загрузка настроек из .env
handlers/
  └── user_game.py  # Клиентская часть: /start и меню игры
keyboards/
  └── game_kb.py    # Inline-клавиатуры для меню
api_server.py       # FastAPI приложение с эндпоинтами /check-sub, /check-legal, /outages
storage.py          # SQLite хранилище пользователей, сбоев и напоминаний
reminders.py        # Сервис отправки напоминаний о сбоях
```

## Подготовка окружения
1. Python 3.11+
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте файл `.env` по примеру:
   ```bash
   cp .env.example .env
   # Заполните BOT_TOKEN и API_SECRET
   ```

## Запуск
Запустите бота и API сервер одной командой:
```bash
python bot.py
```

### Проверка подписки
Пример запроса к HTTP API:
```bash
curl -X POST http://localhost:8000/check-sub \
  -H "Content-Type: application/json" \
  -d '{"secret":"<API_SECRET>","user_id":123,"channel_id":-1001234567890}'
```
Ответ:
```json
{"subscribed": true}
```

### Проверка принятия правил
```bash
curl -X POST http://localhost:8000/check-legal \
  -H "Content-Type: application/json" \
  -d '{"secret":"<API_SECRET>","user_id":123}'
```
Ответ:
```json
{"accepted": true}
```

### Создание сбоя и напоминаний
```bash
curl -X POST http://localhost:8000/outages \
  -H "Content-Type: application/json" \
  -d '{"secret":"<API_SECRET>","name":"Технический сбой","reward":"100 монет","starts_at":"2025-01-01T10:00:00+03:00","ends_at":"2025-01-01T12:00:00+03:00"}'
```
Ответ:
```json
{"outage_id": 1, "scheduled": 6}
```

## Примечания
- В случае неправильного секрета возвращается `403 Forbidden`.
- Статус подписки определяется через `get_chat_member`; пользователи со статусами `left` и `kicked` считаются не подписанными.
