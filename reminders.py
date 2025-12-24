import threading
import time
from datetime import datetime, timedelta, timezone

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from storage import Database


REMINDER_SCHEDULE = [
    ("3d", timedelta(days=3)),
    ("1d", timedelta(days=1)),
    ("3h", timedelta(hours=3)),
    ("10m", timedelta(minutes=10)),
    ("5m", timedelta(minutes=5)),
    ("start", timedelta(seconds=0)),
]

REMINDER_LABELS = {
    "3d": "через 3 дня",
    "1d": "через 1 день",
    "3h": "через 3 часа",
    "10m": "через 10 минут",
    "5m": "через 5 минут",
    "start": "сейчас",
}


def _format_ts(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _format_remaining(seconds: int) -> str:
    if seconds <= 0:
        return "меньше минуты"
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    minutes = minutes % 60
    hours = hours % 24

    parts: list[str] = []
    if days:
        parts.append(f"{days} дн.")
    if hours:
        parts.append(f"{hours} ч.")
    if minutes:
        parts.append(f"{minutes} мин.")
    return " ".join(parts) if parts else "меньше минуты"


class ReminderService:
    def __init__(self, bot: TeleBot, db: Database, poll_interval: int = 30) -> None:
        self._bot = bot
        self._db = db
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def schedule_outage(self, name: str, reward: str | None, starts_at: int, ends_at: int) -> tuple[int, int]:
        outage_id = self._db.create_outage(name=name, reward=reward, starts_at=starts_at, ends_at=ends_at)
        now_ts = int(time.time())
        reminders: list[tuple[str, int]] = []
        for reminder_type, delta in REMINDER_SCHEDULE:
            send_at = int(starts_at - delta.total_seconds())
            if send_at <= now_ts:
                continue
            reminders.append((reminder_type, send_at))
        created = self._db.create_reminders(outage_id, reminders)
        return outage_id, created

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now_ts = int(time.time())
            due_reminders = self._db.get_due_reminders(now_ts)
            if due_reminders:
                self._dispatch_reminders(due_reminders, now_ts)
            self._stop_event.wait(self._poll_interval)

    def _dispatch_reminders(self, reminders, now_ts: int) -> None:
        user_ids = self._db.list_user_ids(only_accepted=True)
        if not user_ids:
            for reminder in reminders:
                self._db.mark_reminder_sent(reminder["id"])
            return

        for reminder in reminders:
            message = self._build_message(reminder, now_ts)
            for user_id in user_ids:
                try:
                    self._bot.send_message(chat_id=user_id, text=message)
                except ApiTelegramException:
                    continue
                except Exception:
                    continue
            self._db.mark_reminder_sent(reminder["id"])

    def _build_message(self, reminder, now_ts: int) -> str:
        name = reminder["name"]
        reward = reminder["reward"] or "—"
        starts_at = _format_ts(int(reminder["starts_at"]))
        label = REMINDER_LABELS.get(reminder["type"], "скоро")
        if reminder["type"] == "start":
            return (
                f"Сбой «{name}» начался.\n"
                f"Время начала: {starts_at}."
            )
        remaining = _format_remaining(int(reminder["starts_at"]) - now_ts)
        return (
            f"Напоминание: сбой «{name}» начнется {label}.\n"
            f"Осталось: {remaining}.\n"
            f"Время начала: {starts_at}."
        )
