import logging
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN, CHAT_ID
from db.database import init_db
from db.crud import get_setting, set_setting
from bot.handlers import register_handlers
from bot.keyboards import build_main_menu

logging.basicConfig(level=logging.INFO)

async def on_startup(app):
    old_msg_id = get_setting("ui_message_id")
    if old_msg_id:
        try:
            await app.bot.delete_message(chat_id=CHAT_ID, message_id=int(old_msg_id))
        except Exception:
            pass

    msg = await app.bot.send_message(
        chat_id=CHAT_ID,
        text="📚 *Learntinuum is back online\\!*\n\nChoose an action:",
        reply_markup=build_main_menu(),
        parse_mode="MarkdownV2",
    )
    set_setting("ui_message_id", str(msg.message_id))
    app.bot_data["ui_message_id"] = msg.message_id

def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    register_handlers(app)

    print("Bot initialized successfully.")
    app.run_polling()

if __name__ == "__main__":
    main()