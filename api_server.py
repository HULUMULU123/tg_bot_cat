from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException


def create_api_app(bot: TeleBot, api_secret: str) -> FastAPI:
    app = FastAPI(title="Subscription Checker")

    class CheckSubscriptionRequest(BaseModel):
        secret: str
        user_id: int
        channel_id: str

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

    return app
