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
    month = request.args.get('month')
    search = request.args.get('search', '').lower()
    df = load_data_web()
    if month:
        try:
            month_int = int(month)
            df = df[df['date'].dt.month == month_int]
        except:
            pass
    if search:
        df = df[df.apply(lambda row: search in str(row['category']).lower() or 
                                    search in str(row['type']).lower() or 
                                    search in str(row['date']).lower(), axis=1)]

    if df.empty:
        return "<h2>Belum ada data</h2>"

    income = df[df["type"]=="income"]["amount"].sum()
    expense = df[df["type"]=="expense"]["amount"].sum()
    saldo = income - expense

    # Trend line saldo harian
    df_trend = df.groupby('date').apply(lambda x: (x[x["type"]=="income"]["amount"].sum() - x[x["type"]=="expense"]["amount"].sum())).cumsum()
    dates = df_trend.index.strftime("%Y-%m-%d").tolist()
    saldo_trend = df_trend.values.tolist()

    # Data kategori & detail transaksi
    category_group = df.groupby('category')
    category_totals = category_group['amount'].sum().to_dict()
    category_details = {cat: group.to_dict(orient='records') for cat, group in category_group}

    months_options = ''.join([f'<option value="{m}" {"selected" if month==str(m) else ""}>{m}</option>' for m in range(1,13)])
    category_details_json = json.dumps(category_details, default=str)

    return f"""
    <html>
    <head>
        <title>💰 Dashboard Finance PDF</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f2f5;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }}
            .cards {{ display:flex; flex-wrap:wrap; justify-content:center; }}
            .card {{
                background-color: white;
                border-radius:10px;
                box-shadow:0 4px 8px rgba(0,0,0,0.1);
                padding:30px;
                margin:10px;
                text-align:center;
                width:200px;
            }}
            .value {{ font-size:24px; font-weight:bold; margin:10px 0; }}
            .income {{ color:green; }} .expense {{ color:red; }} .saldo {{ color:#2980b9; }}
            canvas {{ margin-top:30px; max-width:600px; }}
            select, input[type="text"], button {{ padding:5px; margin:5px; }}
            table {{
                border-collapse: collapse;
                width: 90%;
                margin-top: 20px;
                background-color:white;
                box-shadow:0 4px 8px rgba(0,0,0,0.1);
            }}
            th, td {{ border:1px solid #ddd; padding:8px; text-align:center; }}
            th {{ background-color:#2980b9; color:white; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    </head>
    <body>
        <h1>💰 Dashboard Finance PDF</h1>

        <form method="get">
            <label>Bulan:</label>
            <select name="month" onchange="this.form.submit()">
                <option value="">Semua</option>
                {months_options}
            </select>
            <label>Cari:</label>
            <input type="text" name="search" value="{search}" placeholder="kategori, tipe, tanggal">
            <button type="submit">Search</button>
        </form>

        <div class="cards">
            <div class="card saldo"><p>Saldo</p><div class="value">{saldo}</div></div>
            <div class="card income"><p>Income</p><div class="value">+{income}</div></div>
            <div class="card expense"><p>Expense</p><div class="value">-{expense}</div></div>
        </div>

        <canvas id="pieChart"></canvas>
        <canvas id="lineChart"></canvas>
        <canvas id="categoryChart"></canvas>

        <h2>Detail Transaksi Kategori: <span id="selectedCategory">Semua</span></h2>
        <button onclick="exportCSV()">Export CSV</button>
        <button onclick="exportPDF()">Export PDF</button>

        <table id="transactionTable">
            <thead><tr><th>Tanggal</th><th>Kategori</th><th>Tipe</th><th>Jumlah</th></tr></thead>
            <tbody></tbody>
        </table>

        <script>
            const categoryDetails = {category_details_json};

            function populateTable(category) {{
                const tbody = document.querySelector('#transactionTable tbody');
                tbody.innerHTML = '';
                let rows = [];
                if(category==='Semua') {{
                    for(let cat in categoryDetails) {{
                        categoryDetails[cat].forEach(d => {{
                            rows.push(`<tr><td>${{d.date}}</td><td>${{d.category}}</td><td>${{d.type}}</td><td>${{d.amount}}</td></tr>`);
                        }});
                    }}
                }} else {{
                    categoryDetails[category].forEach(d => {{
                        rows.push(`<tr><td>${{d.date}}</td><td>${{d.category}}</td><td>${{d.type}}</td><td>${{d.amount}}</td></tr>`);
                    }});
                }}
                tbody.innerHTML = rows.join('');
                document.getElementById('selectedCategory').innerText = category;
            }}

            function exportCSV() {{
                let rows = [['Tanggal','Kategori','Tipe','Jumlah']];
                document.querySelectorAll('#transactionTable tbody tr').forEach(r => {{
                    let cols = r.querySelectorAll('td');
                    rows.push([cols[0].innerText, cols[1].innerText, cols[2].innerText, cols[3].innerText]);
                }});
                let csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\\n");
                const link = document.createElement("a");
                link.setAttribute("href", encodeURI(csvContent));
                link.setAttribute("download", "transaksi.csv");
                document.body.appendChild(link); link.click(); link.remove();
            }}

            async function exportPDF() {{
                const {{ jsPDF }} = window.jspdf;
                const doc = new jsPDF('p','pt','a4');
                const element = document.body;
                await html2canvas(element).then(canvas => {{
                    const imgData = canvas.toDataURL('image/png');
                    const imgProps= doc.getImageProperties(imgData);
                    const pdfWidth = doc.internal.pageSize.getWidth();
                    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
                    doc.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
                    doc.save("dashboard.pdf");
                }});
            }}

            populateTable('Semua');

            const pieChart = new Chart(document.getElementById('pieChart').getContext('2d'), {{
                type:'pie',
                data:{{ labels:['Income','Expense'], datasets:[{{data:[{income},{expense}], backgroundColor:['green','red']}}] }},
                options:{{ plugins:{{ title:{{ display:true, text:'Income vs Expense' }} }} }}
            }});

            const lineChart = new Chart(document.getElementById('lineChart').getContext('2d'), {{
                type:'line',
                data:{{ labels:{dates}, datasets:[{{label:'Saldo Harian', data:{saldo_trend}, borderColor:'#2980b9', fill:false, tension:0.3}}] }},
                options:{{ plugins:{{ title:{{ display:true, text:'Trend Saldo Harian' }} }} }}
            }});

            const categoryChart = new Chart(document.getElementById('categoryChart').getContext('2d'), {{
                type:'bar',
                data:{{ labels:{list(category_totals.keys())}, datasets:[{{label:'Total per Kategori', data:{list(category_totals.values())}, backgroundColor:'#8e44ad'}}] }},
                options:{{
                    plugins:{{ title:{{ display:true, text:'Total per Kategori (Klik untuk detail)' }} }},
                    responsive:true,
                    scales:{{y:{{beginAtZero:true}}}},
                    onClick:(e,elements) => {{
                        if(elements.length>0){{
                            const index = elements[0].index;
                            populateTable(categoryChart.data.labels[index]);
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
