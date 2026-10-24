import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "daftar_deyoon.db"

st.set_page_config(
    page_title="دفتر ديوني",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Database ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('دين', 'تسديد')),
                amount REAL NOT NULL CHECK(amount >= 0),
                currency TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        """)
        conn.execute("PRAGMA foreign_keys = ON")

init_db()

CURRENCIES = ["ريال يمني", "ريال سعودي", "دولار أمريكي"]

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Cairo', sans-serif;
}
.stApp {
    background: #f8fafc;
    color: #172033;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 1400px; }

.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric-label { color: #64748b; font-size: 0.85rem; font-weight: 600; }
.metric-value { font-size: 1.25rem; font-weight: 800; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

def money(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")

def get_customers(search=""):
    with get_conn() as conn:
        if search.strip():
            return conn.execute(
                "SELECT * FROM customers WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
                (f"%{search.strip()}%",)
            ).fetchall()
        return conn.execute("SELECT * FROM customers ORDER BY name COLLATE NOCASE").fetchall()

def get_customer(customer_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()

def get_records(customer_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM records WHERE customer_id=? ORDER BY id DESC", (customer_id,)
        ).fetchall()

def currency_summary(records):
    summary = {}
    for currency in CURRENCIES:
        debt = sum(float(r["amount"]) for r in records
                   if r["currency"] == currency and r["type"] == "دين")
        paid = sum(float(r["amount"]) for r in records
                   if r["currency"] == currency and r["type"] == "تسديد")
        summary[currency] = {"debt": debt, "paid": paid, "remaining": debt - paid}
    return summary

def add_customer(name):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO customers(name, created_at) VALUES(?, ?)",
            (name.strip(), datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

def add_record(customer_id, kind, amount, currency, note, created_at):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO records(customer_id, type, amount, currency, note, created_at)
               VALUES(?, ?, ?, ?, ?, ?)""",
            (customer_id, kind, float(amount), currency, note.strip(), created_at)
        )

# ---------- الحاسبة السوداء الاحترافية المحدثة ----------
CALC_HTML = r"""
<script>
(function () {
  var host = window.parent;
  var hostDoc = host.document;
  if (hostDoc.getElementById("fcalc-script")) return;

  function init() {
    if (hostDoc.getElementById("fcalc-root")) return;

    var style = hostDoc.createElement("style");
    style.id = "fcalc-style";
    style.textContent = `
      #fcalc-btn {
        position: fixed; bottom: 25px; left: 25px; z-index: 999999;
        width: 55px; height: 55px; border: none; border-radius: 50%;
        background: #000000; color: #fff; font-size: 24px; cursor: pointer;
        box-shadow: 0 4px 20px rgba(0,0,0,.5);
        display: flex; align-items: center; justify-content: center;
        transition: transform .2s;
      }
      #fcalc-btn:hover { transform: scale(1.1); }
      #fcalc-box {
        position: fixed; bottom: 95px; left: 25px; z-index: 999999;
        width: 280px; padding: 20px; border-radius: 20px;
        background: #000000; color: #fff; display: none;
        box-shadow: 0 10px 30px rgba(0,0,0,.5);
        border: 1px solid #333;
      }
