import threading
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot import *

from flask import Flask
import pandas as pd

app_web = Flask(__name__)

def load_data_web():
    return pd.read_csv("data.csv")

@app_web.route("/")
def index():
    print("WEB KEAKSES")

    df = load_data_web()

    if df.empty:
        return "<h2>Belum ada data</h2>"

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()
    saldo = income - expense

    # HTML + CSS + Chart.js
    return f"""
    <html>
    <head>
        <title>💰 Dashboard Keuangan</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                padding: 20px;
            }}
            .card {{
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                padding: 30px;
                margin: 10px;
                text-align: center;
                width: 300px;
            }}
            h1 {{
                color: #2c3e50;
            }}
            .value {{
                font-size: 24px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .income {{ color: green; }}
            .expense {{ color: red; }}
            .saldo {{ color: #2980b9; }}
            canvas {{
                margin-top: 30px;
                max-width: 500px;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>💰 Dashboard Keuangan</h1>
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

        <canvas id="myChart"></canvas>

        <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            const myChart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: ['Income', 'Expense'],
                    datasets: [{{
                        label: 'Amount',
                        data: [{income}, {expense}],
                        backgroundColor: ['green', 'red']
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }},
                        title: {{
                            display: true,
                            text: 'Income vs Expense'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
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
