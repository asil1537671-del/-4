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

# ---------- الحاسبة السوداء الاحترافية ----------
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
        position: fixed; bottom: 20px; left: 20px; z-index: 999999;
        width: 50px; height: 50px; border: none; border-radius: 50%;
        background: #000; color: #fff; font-size: 22px; cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        display: flex; align-items: center; justify-content: center;
      }
      #fcalc-box {
        position: fixed; bottom: 80px; left: 20px; z-index: 999999;
        width: 270px; padding: 15px; border-radius: 18px;
        background: #000; color: #fff; display: none;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 1px solid #222;
      }
      #fcalc-box.open { display: block; }
      #fcalc-display {
        box-sizing: border-box; width: 100%; height: 50px; border: 0;
        border-radius: 8px; background: #000; color: #fff;
        text-align: right; font-size: 26px; padding: 5px; margin-bottom: 10px;
        direction: ltr; font-family: sans-serif;
      }
      #fcalc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
      #fcalc-grid button {
        border: 0; border-radius: 50%; width: 50px; height: 50px;
        background: #333; color: #fff; font-size: 18px; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
      }
      #fcalc-grid button.op { background: #fe9e09; }
      #fcalc-grid button.fn { background: #a5a5a5; color: #000; }
      #fcalc-grid button.zero { grid-column: span 2; width: 100px; border-radius: 25px; justify-content: flex-start; padding-left: 20px; }
    `;
    hostDoc.head.appendChild(style);

    var root = hostDoc.createElement("div");
    root.id = "fcalc-root";
    root.innerHTML =
      '<button id="fcalc-btn" type="button">🧮</button>' +
      '<div id="fcalc-box" dir="ltr">' +
      '  <input id="fcalc-display" readonly value="">' +
      '  <div id="fcalc-grid"></div>' +
      '</div>';
    hostDoc.body.appendChild(root);

    var box = hostDoc.getElementById("fcalc-box");
    var btn = hostDoc.getElementById("fcalc-btn");
    var display = hostDoc.getElementById("fcalc-display");
    var grid = hostDoc.getElementById("fcalc-grid");

    var buttons = [
      {t:"C", c:"fn", k:"C"}, {t:"()", c:"fn", k:"()"}, {t:"%", c:"fn", k:"%"}, {t:"÷", c:"op", k:"/"},
      {t:"7", c:"", k:"7"}, {t:"8", c:"", k:"8"}, {t:"9", c:"", k:"9"}, {t:"×", c:"op", k:"*"},
      {t:"4", c:"", k:"4"}, {t:"5", c:"", k:"5"}, {t:"6", c:"", k:"6"}, {t:"−", c:"op", k:"-"},
      {t:"1", c:"", k:"1"}, {t:"2", c:"", k:"2"}, {t:"3", c:"", k:"3"}, {t:"+", c:"op", k:"+"},
      {t:"0", c:"zero", k:"0"}, {t:".", c:"", k:"."}, {t:"=", c:"op", k:"="}
    ];

    buttons.forEach(function(b) {
      var btnEl = hostDoc.createElement("button");
      btnEl.textContent = b.t;
      if(b.c) btnEl.className = b.c;
      btnEl.setAttribute("data-k", b.k);
      grid.appendChild(btnEl);
    });

    btn.addEventListener("click", function () { box.classList.toggle("open"); });

    grid.addEventListener("click", function (e) {
      var t = e.target;
      if (t.tagName !== "BUTTON") return;
      var k = t.getAttribute("data-k");
      if (k === "C") { display.value = ""; return; }
      if (k === "=") {
        try { display.value = eval(display.value.replace(/×/g, '*').replace(/÷/g, '/')); }
        catch(err) { display.value = "خطأ"; }
        return;
      }
      display.value += k;
    });
  }

  var s = hostDoc.createElement("script");
  s.id = "fcalc-script";
  s.textContent = "(" + init.toString() + ")();";
  hostDoc.body.appendChild(s);
})();
</script>
"""

components.html(CALC_HTML, height=0)

# ---------- State Management ----------
if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

selected_id = st.session_state.selected_customer_id

st.title("📒 دفتر ديوني")

# ---------- الصفحة الرئيسية ----------
if selected_id is None:
    customers = get_customers()
    all_records = []
    for c in customers:
        all_records.extend(get_records(c["id"]))

    # الإحصائيات جنبًا إلى جنب تماماً
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">إجمالي العملاء</div><div class="metric-value" style="color:#2563eb">{len(customers)}</div></div>', unsafe_allow_html=True)
    with col2:
        total_debt = sum(1 for r in all_records if r["type"] == "دين")
        st.markdown(f'<div class="metric-card"><div class="metric-label">عمليات الديون</div><div class="metric-value" style="color:#ef4444">{total_debt}</div></div>', unsafe_allow_html=True)
    with col3:
        total_pay = sum(1 for r in all_records if r["type"] == "تسديد")
        st.markdown(f'<div class="metric-card"><div class="metric-label">عمليات التسديد</div><div class="metric-value" style="color:#10b981">{total_pay}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("➕ إضافة عميل جديد"):
        with st.form("add_cust_form", clear_on_submit=True):
            c_name = st.text_input("اسم العميل")
            if st.form_submit_button("حفظ العميل", use_container_width=True):
                if c_name.strip():
                    try:
                        add_customer(c_name)
                        st.success("تمت الإضافة")
                        st.rerun()
                    except:
                        st.error("الاسم موجود مسبقاً")

    st.subheader("👥 سجل العملاء")
    for customer in customers:
        records = get_records(customer["id"])
        summary = currency_summary(records)
        with st.container(border=True):
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                st.markdown(f"### 👤 {customer['name']}")
                parts = [f"{money(summary[cur]['remaining'])} {cur}" for cur in CURRENCIES if summary[cur]["debt"] > 0 or summary[cur]["paid"] > 0]
                st.caption("المتبقي: " + (" | ".join(parts) if parts else "0"))
            with c_col2:
                if st.button("عرض السجل", key=f"cust_{customer['id']}", use_container_width=True):
                    st.session_state.selected_customer_id = customer["id"]
                    st.rerun()

# ---------- واجهة تفاصيل العميل ----------
else:
    customer = get_customer(selected_id)
    if st.button("⬅️ العودة للعملاء"):
        st.session_state.selected_customer_id = None
        st.rerun()

    st.subheader(f"👤 العميل: {customer['name']}")
    records = get_records(selected_id)
    summary = currency_summary(records)

    btn_col1, btn_col2 = st.columns(2)
    
    # زر التسديد (أخضر) - الترتيب: المبلغ -> العملة -> الملاحظات -> التاريخ والوقت
    with btn_col1:
        with st.popover("🟢 تسجيل تسديد", use_container_width=True):
            with st.form("pay_form", clear_on_submit=True):
                p_amount = st.text_input("المبلغ")
                p_curr = st.selectbox("العملة", CURRENCIES)
                p_note = st.text_input("الملاحظات (اختياري)")
                p_date = st.text_input("تاريخ الحركة", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
                if st.form_submit_button("↓ تسديد", use_container_width=True):
                    try:
                        add_record(selected_id, "تسديد", float(p_amount), p_curr, p_note, p_date)
                        st.success("تم الحفظ")
                        st.rerun()
                    except:
                        st.error("أدخل مبلغ صحيح")

    # زر إضافة دين (أحمر) - الترتيب: المبلغ -> العملة -> الملاحظات -> التاريخ والوقت
    with btn_col2:
        with st.popover("🔴 إضافة دين", use_container_width=True):
            with st.form("debt_form", clear_on_submit=True):
                d_amount = st.text_input("المبلغ")
                d_curr = st.selectbox("العملة", CURRENCIES)
                d_note = st.text_input("الملاحظات (اختياري)")
                d_date = st.text_input("تاريخ الحركة", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
                if st.form_submit_button("↑ إضافة دين", use_container_width=True):
                    try:
                        add_record(selected_id, "دين", float(d_amount), d_curr, d_note, d_date)
                        st.success("تم الحفظ")
                        st.rerun()
                    except:
                        st.error("أدخل مبلغ صحيح")

    st.markdown("---")
    st.markdown("### المعاملات")
    for r in records:
        color = "#10b981" if r["type"] == "تسديد" else "#ef4444"
        with st.container(border=True):
            r_col1, r_col2 = st.columns([4, 1])
            with r_col1:
                st.markdown(f"<h4 style='color:{color}; margin:0;'>{r['type']} : {money(r['amount'])} {r['currency']}</h4>", unsafe_allow_html=True)
                st.caption(f"{r['created_at']} | {r['note']}")
            with r_col2:
                if st.button("🗑️", key=f"del_{r['id']}"):
                    with get_conn() as conn:
                        conn.execute("DELETE FROM records WHERE id=?", (r["id"],))
                    st.rerun()
