from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = 'super_secret'

# Konfigurasi Bot Telegram (Ganti dengan Token & Chat ID asli dari @BotFather)
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'


# --- Setup Database ---
def get_db():
    conn = sqlite3.connect('kos.db')
    conn.row_factory = sqlite3.Row
    return conn


with get_db() as conn:
    # Tabel Pengeluaran
    conn.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Insert Data Dummy jika kosong
    if conn.execute('SELECT COUNT(*) FROM expenses').fetchone()[0] == 0:
        conn.execute("INSERT INTO expenses (title, category, amount) VALUES ('Beras & Sayur', 'Katering', 120000)")
        conn.execute("INSERT INTO expenses (title, category, amount) VALUES ('Ayam Geprek', 'Katering', 60000)")


# --- Telegram Notification ---
def send_telegram_msg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except:
        pass  # Abaikan jika token belum diisi


# --- Template HTML (Tailwind CSS) ---
HTML = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manajemen Kos & Katering</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 p-8 font-sans">
    <div class="max-w-4xl mx-auto space-y-6">

        <div class="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">🏠 Dashboard Kos & Katering</h1>
                <p class="text-slate-500 text-sm">Rekap patungan harian & tagihan bulanan.</p>
            </div>
            <a href="/notify" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition">
                <span>📱</span> Broadcast Telegram
            </a>
        </div>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="bg-green-100 text-green-700 p-4 rounded-lg font-bold border border-green-200">
                    {{ messages[0] }}
                </div>
            {% endif %}
        {% endwith %}

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 col-span-1">
                <h2 class="text-lg font-bold text-slate-700 mb-4">💰 Split Bill Katering</h2>
                <div class="bg-slate-50 p-4 rounded-lg border border-slate-100 mb-4 text-center">
                    <p class="text-xs text-slate-500 uppercase tracking-wider mb-1">Total Katering</p>
                    <p class="text-3xl font-black text-indigo-600">Rp {{ "{:,.0f}".format(total_katering) }}</p>
                </div>
                <div class="bg-indigo-50 p-4 rounded-lg border border-indigo-100 text-center">
                    <p class="text-xs text-indigo-500 uppercase tracking-wider mb-1">Per Orang (4 Anggota)</p>
                    <p class="text-2xl font-bold text-indigo-700">Rp {{ "{:,.0f}".format(total_katering / 4) }}</p>
                </div>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 col-span-2">
                <form action="/add" method="post" class="flex gap-2 mb-6">
                    <input type="text" name="title" placeholder="Nama Tagihan/Bahan" required class="flex-1 p-3 border border-slate-200 rounded-lg bg-slate-50 outline-none focus:border-indigo-500">
                    <select name="category" class="p-3 border border-slate-200 rounded-lg bg-slate-50 outline-none">
                        <option value="Katering">Katering</option>
                        <option value="Kamar">Kamar</option>
                        <option value="Listrik">Listrik</option>
                    </select>
                    <input type="number" name="amount" placeholder="Nominal" required class="w-1/4 p-3 border border-slate-200 rounded-lg bg-slate-50 outline-none focus:border-indigo-500">
                    <button type="submit" class="bg-indigo-600 text-white font-bold px-6 py-3 rounded-lg hover:bg-indigo-700">Catat</button>
                </form>

                <div class="overflow-y-auto max-h-64">
                    <table class="w-full text-left text-sm border-collapse">
                        <tr class="bg-slate-100 text-slate-500 uppercase">
                            <th class="p-3 border-b">Tanggal</th>
                            <th class="p-3 border-b">Item</th>
                            <th class="p-3 border-b">Kategori</th>
                            <th class="p-3 border-b text-right">Nominal</th>
                        </tr>
                        {% for e in expenses %}
                        <tr class="hover:bg-slate-50">
                            <td class="p-3 border-b">{{ e.date[:10] }}</td>
                            <td class="p-3 border-b font-bold">{{ e.title }}</td>
                            <td class="p-3 border-b">
                                <span class="px-2 py-1 bg-slate-200 rounded text-xs">{{ e.category }}</span>
                            </td>
                            <td class="p-3 border-b text-right font-bold text-slate-700">Rp {{ "{:,.0f}".format(e.amount) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            </div>

        </div>
    </div>
</body>
</html>
'''


# --- Routes ---
@app.route('/')
def index():
    conn = get_db()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY id DESC').fetchall()

    # Hitung total khusus katering
    total_katering = sum(e['amount'] for e in expenses if e['category'] == 'Katering')

    conn.close()
    return render_template_string(HTML, expenses=expenses, total_katering=total_katering)


@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    category = request.form['category']
    amount = float(request.form['amount'])

    conn = get_db()
    conn.execute('INSERT INTO expenses (title, category, amount) VALUES (?, ?, ?)', (title, category, amount))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/notify')
def notify():
    conn = get_db()
    total_katering = conn.execute('SELECT SUM(amount) FROM expenses WHERE category="Katering"').fetchone()[0] or 0
    conn.close()

    split = total_katering / 4

    # Format Pesan Telegram
    msg = f"🔔 <b>Pengingat Patungan Katering</b>\n\n"
    msg += f"Total Pengeluaran: <b>Rp {total_katering:,.0f}</b>\n"
    msg += f"Tagihan per orang (4 orang): <b>Rp {split:,.0f}</b>\n\n"
    msg += f"Harap segera transfer ke rekening DANA atau BCA ya! 💸"

    send_telegram_msg(msg)

    flash('Notifikasi Telegram berhasil dikirim!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)