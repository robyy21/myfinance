from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import pandas as pd
import matplotlib.pyplot as plt
import os

CATEGORIES = ["🍔 Makan", "🚗 Transport", "☕ Nongkrong", "🛍️ Belanja"]
user_state = {}
FILE = "data.csv"
BUDGET_FILE = "budget.csv"

# INIT FILE
if not os.path.exists(FILE):
    pd.DataFrame(columns=["date","type","amount","category"]).to_csv(FILE,index=False)

if not os.path.exists(BUDGET_FILE):
    pd.DataFrame(columns=["category","budget"]).to_csv(BUDGET_FILE,index=False)

def load_data():
    return pd.read_csv(FILE)

def save_data(df):
    df.to_csv(FILE,index=False)

def load_budget():
    return pd.read_csv(BUDGET_FILE)

def save_budget(df):
    df.to_csv(BUDGET_FILE,index=False)

# ➕ EXPENSE
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        category = context.args[1]

        df = load_data()

        new = pd.DataFrame([{
            "date": pd.Timestamp.now(),
            "type": "expense",
            "amount": amount,
            "category": category
        }])

        df = pd.concat([df,new])
        save_data(df)

        # 🔥 CEK BUDGET
        budget_df = load_budget()
        cat_budget = budget_df[budget_df["category"]==category]

        warning = ""

        if not cat_budget.empty:
            limit = cat_budget["budget"].values[0]
            used = df[df["category"]==category]["amount"].sum()

            if used > limit:
                warning = "\n🚨 Budget terlampaui!"
            elif used > 0.8 * limit:
                warning = "\n⚠️ Budget hampir habis!"

        await update.message.reply_text(f"✅ Pengeluaran: -{amount} ({category}){warning}")

    except:
        await update.message.reply_text("Format: /add 25000 makan")

# 💰 INCOME
async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])

        df = load_data()

        new = pd.DataFrame([{
            "date": pd.Timestamp.now(),
            "type": "income",
            "amount": amount,
            "category": "income"
        }])

        df = pd.concat([df,new])
        save_data(df)

        await update.message.reply_text(f"💰 Pemasukan: +{amount}")

    except:
        await update.message.reply_text("Format: /income 4000000")

# 📊 SALDO
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()

    await update.message.reply_text(
        f"💰 Saldo kamu:\n{income-expense}\n\nIncome: {income}\nExpense: {expense}"
    )

# 📊 LAPORAN
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()

    top = "-"
    if not df.empty:
        top = df.groupby("category")["amount"].sum().idxmax()

    await update.message.reply_text(
        f"📊 Laporan:\nIncome: {income}\nExpense: {expense}\nPaling boros: {top}"
    )

# 🔥 HARI INI
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    today = pd.Timestamp.now().date()

    today_exp = df[
        (df["type"]=="expense") &
        (pd.to_datetime(df["date"]).dt.date == today)
    ]["amount"].sum()

    await update.message.reply_text(f"🔥 Pengeluaran hari ini: {today_exp}")

# 📊 CHART
async def chart(update, context):
    df = load_data()

    summary = df[df["type"]=="expense"].groupby("category")["amount"].sum()

    if summary.empty:
        await update.message.reply_text("Belum ada data")
        return

    plt.figure()
    summary.plot(kind="bar")
    plt.title("Pengeluaran per Kategori")
    plt.savefig("chart.png")

    await update.message.reply_photo(photo=open("chart.png","rb"))

# 🚨 SET BUDGET
async def setbudget(update, context):
    category = context.args[0]
    amount = int(context.args[1])

    df = load_budget()
    df = df[df["category"]!=category]

    df = pd.concat([df, pd.DataFrame([{
        "category": category,
        "budget": amount
    }])])

    save_budget(df)

    await update.message.reply_text(f"✅ Budget {category} = {amount}")

# 📁 EXPORT
async def export(update, context):
    df = load_data()
    file = "laporan.xlsx"
    df.to_excel(file, index=False)

    await update.message.reply_document(document=open(file,"rb"))

# 📅 BULANAN
async def bulanan(update, context):
    df = load_data()

    df["date"] = pd.to_datetime(df["date"])
    now = pd.Timestamp.now()

    df = df[
        (df["date"].dt.month == now.month) &
        (df["date"].dt.year == now.year)
    ]

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()

    await update.message.reply_text(
        f"📅 Bulan ini:\nIncome: {income}\nExpense: {expense}\nSisa: {income-expense}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💰 Income", "💸 Expense"],
        ["📊 Saldo", "📈 Laporan"],
        ["📊 Chart", "📅 Bulanan"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🤖 Selamat datang di Finance Bot!\nPilih menu:",
        reply_markup=reply_markup
    )

#LIST
async def list_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()

    if df.empty:
        await update.message.reply_text("Belum ada transaksi")
        return

    text = "📋 Daftar Transaksi:\n"

    for i, row in df.iterrows():
        sign = "+" if row["type"] == "income" else "-"
        text += f"{i+1}. {sign}{row['amount']} ({row['category']})\n"

    await update.message.reply_text(text)

#HAPUS
async def hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0]) - 1

        df = load_data()

        if df.empty:
            await update.message.reply_text("Tidak ada data")
            return

        if index < 0 or index >= len(df):
            await update.message.reply_text("Nomor tidak valid")
            return

        df = df.drop(index)
        df = df.reset_index(drop=True)

        save_data(df)

        await update.message.reply_text("🗑️ Transaksi berhasil dihapus")

    except:
        await update.message.reply_text("Format: /hapus 1")

#EDIT'
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0]) - 1
        amount = int(context.args[1])
        category = context.args[2]

        df = load_data()

        if df.empty:
            await update.message.reply_text("Tidak ada data")
            return

        if index < 0 or index >= len(df):
            await update.message.reply_text("Nomor tidak valid")
            return

        df.loc[index, "amount"] = amount
        df.loc[index, "category"] = category

        save_data(df)

        await update.message.reply_text(f"✏️ Transaksi {index+1} diupdate")

    except:
        await update.message.reply_text("Format: /edit 1 30000 makan")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # ===== STATE FLOW =====
    if user_id in user_state:
        state = user_state[user_id]

        # STEP 1: INPUT AMOUNT EXPENSE
        if state["step"] == "expense_amount":
            try:
                state["amount"] = int(text)
            except:
                await update.message.reply_text("Masukkan angka yang benar!")
                return

            state["step"] = "expense_category"

            keyboard = [[cat] for cat in CATEGORIES]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                "Pilih kategori:",
                reply_markup=reply_markup
            )
            return

        # STEP 2: PILIH CATEGORY
        elif state["step"] == "expense_category":
            amount = state["amount"]
            category = text

            category_clean = category.split(" ", 1)[-1]

            df = load_data()

            new = pd.DataFrame([{
                "date": pd.Timestamp.now(),
                "type": "expense",
                "amount": amount,
                "category": category_clean
            }])

            df = pd.concat([df, new])
            save_data(df)

            user_state.pop(user_id)

            await update.message.reply_text(f"✅ Pengeluaran: -{amount} ({category_clean})")
            return

        # STEP: INCOME
        elif state["step"] == "income_amount":
            try:
                amount = int(text)
            except:
                await update.message.reply_text("Masukkan angka yang benar!")
                return

            df = load_data()

            new = pd.DataFrame([{
                "date": pd.Timestamp.now(),
                "type": "income",
                "amount": amount,
                "category": "income"
            }])

            df = pd.concat([df, new])
            save_data(df)

            user_state.pop(user_id)

            await update.message.reply_text(f"💰 Pemasukan: +{amount}")
            return

    # ===== MENU BUTTON =====
    if text == "💰 Income":
        user_state[user_id] = {"step": "income_amount"}
        await update.message.reply_text("Masukkan jumlah pemasukan:")

    elif text == "💸 Expense":
        user_state[user_id] = {"step": "expense_amount"}
        await update.message.reply_text("Masukkan jumlah pengeluaran:")

    elif text == "📊 Saldo":
        await saldo(update, context)

    elif text == "📈 Laporan":
        await laporan(update, context)

    elif text == "📊 Chart":
        await chart(update, context)

    elif text == "📅 Bulanan":
        await bulanan(update, context)

# 🚀 RUN
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
app.add_handler(CommandHandler("hapus", hapus))
app.add_handler(CommandHandler("edit", edit))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
