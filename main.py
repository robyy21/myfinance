import threading
import os

# ====== IMPORT BOT ======
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# IMPORT SEMUA FUNCTION BOT KAMU
from bot import (add, income, saldo, laporan, today,
chart, setbudget, export, bulanan,
start, handle_message, list_transaksi, hapus, edit)

# ====== IMPORT WEB ======
from flask import Flask, render_template
import pandas as pd

app_web = Flask(__name__)

def load_data_web():
    return pd.read_csv("data.csv")

@app_web.route("/")
def index():
    df = load_data_web()

    if df.empty:
        return "Belum ada data"

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()
    saldo = income - expense

    return f"""
    <h1>💰 Dashboard</h1>
    <p>Saldo: {saldo}</p>
    <p>Income: {income}</p>
    <p>Expense: {expense}</p>
    """

async def test(update, context):
    await update.message.reply_text("BOT HIDUP 🔥")
# ====== RUN BOT ======
def run_bot():
    print("BOT STARTING...")
    app = ApplicationBuilder().token("8140221752:AAEbxQoryG_RuM44g6XBPUx6-mC56pMEBwU").build()

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("setbudget", setbudget))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("bulanan", bulanan))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_transaksi))
    app.add_handler(CommandHandler("hapus", hapus))  # ✅ pindah ke sini
    app.add_handler(CommandHandler("edit", edit))    # ✅ pindah ke sini
    app.add_handler(CommandHandler("test", test))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

# ====== RUN WEB ======
def run_web():
    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

# ====== JALANKAN BARENG ======
if __name__ == "__main__":
    run_bot()
