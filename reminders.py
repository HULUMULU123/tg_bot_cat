import threading
import time
from datetime import datetime, timedelta, timezone

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from keyboards.game_kb import notification_keyboard
from storage import Database


REMINDER_SCHEDULE = [
    ("3d", timedelta(days=3)),
    ("1d", timedelta(days=1)),
    ("3h", timedelta(hours=3)),
    ("10m", timedelta(minutes=10)),
    ("5m", timedelta(minutes=5)),
    ("start", timedelta(seconds=0)),
]

def _format_ts(ts: int) -> str:
    msk = timezone(timedelta(hours=3))
    dt = datetime.fromtimestamp(ts, tz=msk)
    return dt.strftime("%H:%M МСК")


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
    def __init__(
        self,
        bot: TeleBot,
        db: Database,
        poll_interval: int = 30,
        game_url: str | None = None,
    ) -> None:
        self._bot = bot
        self._db = db
        self._poll_interval = poll_interval
        self._game_url = game_url
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
        user_ids = self._db.list_user_ids(only_accepted=True, only_notify=True)
        if not user_ids:
            for reminder in reminders:
                self._db.mark_reminder_sent(reminder["id"])
            return

        for reminder in reminders:
            message = self._build_message(reminder, now_ts)
            markup = self._build_markup(reminder)
            for user_id in user_ids:
                try:
                    self._bot.send_message(chat_id=user_id, text=message, reply_markup=markup)
                except ApiTelegramException:
                    continue
                except Exception:
                    continue
            self._db.mark_reminder_sent(reminder["id"])

    def _build_message(self, reminder, now_ts: int) -> str:
        name = reminder["name"]
        reward = reminder["reward"] or "—"
        starts_at = _format_ts(int(reminder["starts_at"]))
        if reminder["type"] == "start":
            return (
                "💥 СБОЙ НАЧАЛСЯ\n"
                f"📌 {name}\n"
                "⏱ Время ограничено\n"
                "🎟 Вход — за Crash\n"
                f"🏆 Награда: {reward}\n"
                f"🕒 Время начала: {starts_at}"
            )
        remaining = _format_remaining(int(reminder["starts_at"]) - now_ts)
        return (
            "⚠️ Обнаружена аномалия\n"
            f"📌 {name}\n"
            f"💥 Сбой начнется через {remaining}\n"
            f"🏆 Награда: {reward}\n"
            f"🕒 Время начала: {starts_at}"
        )

    def _build_markup(self, reminder):
        return notification_keyboard(
            notify_on=True,
            show_enter=reminder["type"] == "start",
            enter_url=self._game_url,
        )
