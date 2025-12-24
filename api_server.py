from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from reminders import ReminderService
from storage import Database


def _parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def create_api_app(bot: TeleBot, api_secret: str, db: Database, reminders: ReminderService) -> FastAPI:
    app = FastAPI(title="Subscription Checker")

    class CheckSubscriptionRequest(BaseModel):
        secret: str
        user_id: int
        channel_id: str

    class CheckLegalRequest(BaseModel):
        secret: str
        user_id: int

    class DeleteOutageRequest(BaseModel):
        secret: str
        name: str

    class CreateOutageRequest(BaseModel):
        secret: str
        name: str
        reward: str | int | None = None
        starts_at: str = Field(alias="start_time")
        ends_at: str = Field(alias="end_time")

        class Config:
            populate_by_name = True

    @app.post("/check-sub")
    async def check_subscription(payload: CheckSubscriptionRequest):
        if payload.secret != api_secret:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Invalid secret",
                    "hint": "Check API_SECRET and request payload",
                },
            )

        try:
            member = bot.get_chat_member(payload.channel_id, payload.user_id)
        except ApiTelegramException as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Telegram API error",
                    "message": str(exc),
                    "channel_id": payload.channel_id,
                    "user_id": payload.user_id,
                },
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Unexpected error",
                    "message": repr(exc),
                },
            ) from exc

        subscribed = member.status not in {"left", "kicked"}
        return {"subscribed": subscribed}

    @app.post("/check-legal")
    async def check_legal(payload: CheckLegalRequest):
        if payload.secret != api_secret:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Invalid secret",
                    "hint": "Check API_SECRET and request payload",
                },
            )

        db.ensure_user(payload.user_id)
        accepted = db.is_legal_accepted(payload.user_id)
        return {"accepted": accepted}

    @app.post("/outages")
    async def create_outage(payload: CreateOutageRequest):
        if payload.secret != api_secret:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Invalid secret",
                    "hint": "Check API_SECRET and request payload",
                },
            )

        try:
            starts_at = _parse_datetime(payload.starts_at)
            ends_at = _parse_datetime(payload.ends_at)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid datetime format",
                    "hint": "Use ISO 8601 format like 2024-12-31T12:00:00+03:00",
                },
            ) from exc

        if ends_at <= starts_at:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid time range",
                    "hint": "ends_at must be later than starts_at",
                },
            )

        reward_value = str(payload.reward) if payload.reward is not None else None
        outage_id, scheduled = reminders.schedule_outage(
            name=payload.name,
            reward=reward_value,
            starts_at=int(starts_at.timestamp()),
            ends_at=int(ends_at.timestamp()),
        )
        return {"outage_id": outage_id, "scheduled": scheduled}

    @app.post("/outages/delete")
    async def delete_outage(payload: DeleteOutageRequest):
        if payload.secret != api_secret:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Invalid secret",
                    "hint": "Check API_SECRET and request payload",
                },
            )

        deleted = db.delete_outage_by_name(payload.name)
        return {"deleted": deleted}

    return app
