import logging
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from db.database import init_db
from bot.handlers import register_handlers

logging.basicConfig(level=logging.INFO)

def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(app)

    print("Bot initialized successfully.")
    app.run_polling()

if __name__ == "__main__":
    main()