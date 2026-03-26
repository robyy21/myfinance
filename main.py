import os
from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("BOT HIDUP 🔥")

def main():
    print("BOT STARTING...")

    app = ApplicationBuilder().token("8140221752:AAHvIhhyj5L3tQEv062uxmWZjPT0BSo0DrM").build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == "__main__":
    main()
