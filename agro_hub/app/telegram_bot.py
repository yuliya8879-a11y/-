import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from .database import SessionLocal
from .message_handler import handle_incoming_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! 👋\n\n"
        "Я помогу вам оформить лот на продажу зерна.\n\n"
        "Расскажите, что хотите продать?\n"
        "Например: «Орловская область, ячмень, 500 тонн»"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    sender_id = str(user.id)
    name = user.full_name or user.username

    db: Session = SessionLocal()
    try:
        reply = await handle_incoming_message(
            db=db,
            channel="telegram",
            sender_id=sender_id,
            text=text,
            name=name,
        )
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения Telegram: {e}", exc_info=True)
        await update.message.reply_text(
            "Извините, произошла ошибка. Пожалуйста, попробуйте ещё раз."
        )
    finally:
        db.close()


def create_telegram_app() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан — Telegram бот не будет запущен")
        return None

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


async def process_webhook_update(update_data: dict):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    app = create_telegram_app()
    if app is None:
        return
    await app.initialize()
    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)
    await app.shutdown()
