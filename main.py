import threading
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot import *

from flask import Flask, request
import pandas as pd
import json

app_web = Flask(__name__)

def load_data_web():
    df = pd.read_csv("data.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

@app_web.route("/")
def index():
    print("WEB KEAKSES")

    # Ambil filter bulan dari query params, default = semua
    month = request.args.get('month')
    df = load_data_web()
    if month:
        try:
            month_int = int(month)
            df = df[df['date'].dt.month == month_int]
        except:
            pass

    if df.empty:
        return "<h2>Belum ada data</h2>"

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()
    saldo = income - expense

    # Trend line saldo harian
    df_trend = df.groupby('date').apply(lambda x: (x[x["type"]=="income"]["amount"].sum() - x[x["type"]=="expense"]["amount"].sum())).cumsum()
    dates = df_trend.index.strftime("%Y-%m-%d").tolist()
    saldo_trend = df_trend.values.tolist()

    # Total per kategori
    category_data = df.groupby('category')['amount'].sum().to_dict()

    # Filter bulan options
    months_options = ''.join([f'<option value="{m}" {"selected" if month==str(m) else ""}>{m}</option>' for m in range(1,13)])

    return f"""
    <html>
    <head>
        <title>💰 Dashboard Interaktif</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f2f5;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }}
            .cards {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
            }}
            .card {{
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                padding: 30px;
                margin: 10px;
                text-align: center;
                width: 200px;
            }}
            .value {{
                font-size: 24px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .income {{ color: green; }}
            .expense {{ color: red; }}
            .saldo {{ color: #2980b9; }}
            canvas {{ margin-top: 30px; max-width: 600px; }}
            select {{ padding: 5px; margin-bottom: 20px; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>💰 Dashboard Interaktif</h1>

        <form method="get">
            <label for="month">Filter Bulan:</label>
            <select id="month" name="month" onchange="this.form.submit()">
                <option value="">Semua</option>
                {months_options}
            </select>
        </form>

        <div class="cards">
            <div class="card saldo">
                <p>Saldo</p>
                <div class="value">{saldo}</div>
            </div>
            <div class="card income">
                <p>Income</p>
                <div class="value">+{income}</div>
            </div>
            <div class="card expense">
                <p>Expense</p>
                <div class="value">-{expense}</div>
            </div>
        </div>

        <canvas id="pieChart"></canvas>
        <canvas id="lineChart"></canvas>
        <canvas id="categoryChart"></canvas>

        <script>
            const pieCtx = document.getElementById('pieChart').getContext('2d');
            const pieChart = new Chart(pieCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Income','Expense'],
                    datasets:[{{data:[{income},{expense}], backgroundColor:['green','red']}}]
                }},
                options: {{ plugins: {{ title: {{ display:true, text:'Income vs Expense' }} }} }}
            }});

            const lineCtx = document.getElementById('lineChart').getContext('2d');
            const lineChart = new Chart(lineCtx, {{
                type:'line',
                data:{{
                    labels: {dates},
                    datasets:[{{ label:'Saldo Harian', data:{saldo_trend}, borderColor:'#2980b9', fill:false, tension:0.3 }}]
                }},
                options: {{ plugins: {{ title: {{ display:true, text:'Trend Saldo Harian' }} }} }}
            }});

            const categoryCtx = document.getElementById('categoryChart').getContext('2d');
            const categoryChart = new Chart(categoryCtx, {{
                type:'bar',
                data:{{
                    labels: {list(category_data.keys())},
                    datasets:[{{ label:'Total per Kategori', data:{list(category_data.values())}, backgroundColor:'#8e44ad' }}]
                }},
                options: {{ plugins: {{ title: {{ display:true, text:'Total per Kategori' }} }} }}
            }});
        </script>
    </body>
    </html>
    """

# ===== BOT =====
def run_bot():
    token = os.getenv("BOT_TOKEN")
    print("BOT STARTING...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

# ===== WEB =====
def run_web():
    port = int(os.environ.get("PORT", 5000))
    print("WEB RUNNING ON PORT", port)
    app_web.run(host="0.0.0.0", port=port)

# ===== RUN BARENG =====
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
