# Telegram Game Mini-App Bot

Простой телеграм-бот на библиотеке **telebot (pyTelegramBotAPI)** с игровым меню и HTTP API для проверки подписки.

## Возможности
- Команда `/start` выводит приветствие и главное меню.
- Инлайн-меню с разделами: играть, правила, лор.
- Обработчики в отдельных модулях для удобства расширения.
- FastAPI сервер с эндпоинтом `POST /check-sub` для проверки подписки на канал по секрету API.

## Структура проекта
```
bot.py              # Точка входа: запускает telebot и HTTP API
config.py           # Загрузка настроек из .env
handlers/
  └── user_game.py  # Клиентская часть: /start и меню игры
keyboards/
  └── game_kb.py    # Inline-клавиатуры для меню
api_server.py       # FastAPI приложение с эндпоинтом /check-sub
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

## Примечания
- В случае неправильного секрета возвращается `403 Forbidden`.
- Статус подписки определяется через `get_chat_member`; пользователи со статусами `left` и `kicked` считаются не подписанными.
