import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "daftar_deyoon.db"

st.set_page_config(
    page_title="لوحة التحكم - دفتر ديوني",
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

CURRENCIES = ["IQD", "ريال يمني", "ريال سعودي", "دولار أمريكي"]

# ---------- Styling (Matching the exact design theme) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Cairo', sans-serif;
}
.stApp {
    background: #f4f7f6;
    color: #172033;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 600px; }

/* بطاقة العضوية الخضراء */
.sub-card {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
    border-radius: 20px;
    padding: 20px;
    color: white;
    box-shadow: 0 10px 25px rgba(13, 148, 136, 0.2);
    margin-bottom: 15px;
}
.sub-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.sub-badge { background: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.sub-name { font-size: 1.4rem; font-weight: 800; }
.sub-email { font-size: 0.85rem; opacity: 0.9; margin-bottom: 15px; }
.sub-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 12px; font-size: 0.8rem; opacity: 0.95; }

/* بطاقة الترحيب والتحصيلات */
.welcome-card {
    background: white;
    border-radius: 16px;
    padding: 15px 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.welcome-text { font-weight: 700; color: #1e293b; font-size: 1rem; }
.collection-tag { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; padding: 6px 12px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; }

/* قسم الإحصائيات */
.stat-box-red {
    background: #fff5f5;
    border: 1px solid #fed7d7;
    border-radius: 16px;
    padding: 15px;
    text-align: center;
    margin-bottom: 10px;
}
.stat-box-green {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 16px;
    padding: 15px;
    text-align: center;
    margin-bottom: 10px;
}
.stat-title { font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 5px; }
.stat-val { font-size: 1.2rem; font-weight: 800; color: #1e293b; }

div.stButton > button {
    border-radius: 12px;
    min-height: 2.7rem;
    font-weight: 700;
    border: 1px solid #e2e8f0;
    background: white;
}
</style>
""", unsafe_allow_html=True)

def money(value):
    return f"{value:,.0f}"

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

def add_customer(name):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO customers(name, created_at) VALUES(?, ?)",
            (name.strip(), datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

def add_record(customer_id, kind, amount, currency, note):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO records(customer_id, type, amount, currency, note, created_at)
               VALUES(?, ?, ?, ?, ?, ?)""",
            (customer_id, kind, float(amount), currency, note.strip(),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

def clear_search():
    st.session_state["customer_search"] = ""

# ---------- Floating Calculator ----------
CALC_HTML = r"""
<script>
(function () {
  var host = window.parent;
  var hostDoc = host.document;
  if (hostDoc.getElementById("fcalc-script")) return;

  function init() {
    if (document.getElementById("fcalc-root")) return;
    var style = document.createElement("style");
    style.id = "fcalc-style";
    style.textContent = `
      #fcalc-btn {
        position: fixed; bottom: 25px; left: 25px; z-index: 999999;
        width: 55px; height: 55px; border: none; border-radius: 50%;
        background: #0d9488; color: #fff; font-size: 24px; cursor: pointer;
        box-shadow: 0 4px 20px rgba(13,148,136,.4);
        display: flex; align-items: center; justify-content: center;
      }
      #fcalc-box {
        position: fixed; bottom: 95px; left: 25px; z-index: 999999;
        width: 280px; padding: 15px; border-radius: 16px;
        background: #172033; color: #fff; display: none;
        box-shadow: 0 10px 30px rgba(0,0,0,.4);
      }
      #fcalc-box.open { display: block; }
      #fcalc-display {
        width: 100%; height: 45px; border: 0; border-radius: 8px;
        background: #0b1220; color: #67e8f9; text-align: right;
        font-size: 22px; padding: 7px; margin-bottom: 10px; direction: ltr;
      }
      #fcalc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
      #fcalc-grid button, #fcalc-clear {
        border: 0; border-radius: 8px; padding: 10px; background: #334155;
        color: #fff; font-size: 16px; cursor: pointer;
      }
      #fcalc-clear { grid-column: span 4; background: #dc2626; }
    `;
    document.head.appendChild(style);

    var root = document.createElement("div");
    root.id = "fcalc-root";
    root.innerHTML = '<button id="fcalc-btn" type="button">🧮</button><div id="fcalc-box" dir="ltr"><input id="fcalc-display" readonly><div id="fcalc-grid"></div></div>';
    document.body.appendChild(root);

    var box = document.getElementById("fcalc-box");
    var btn = document.getElementById("fcalc-btn");
    var display = document.getElementById("fcalc-display");
    var grid = document.getElementById("fcalc-grid");

    ["7","8","9","/","4","5","6","*","1","2","3","-","0",".","=","+"].forEach(function (k) {
      var b = document.createElement("button");
      b.type = "button"; b.textContent = k; b.setAttribute("data-k", k);
      grid.appendChild(b);
    });
    var clr = document.createElement("button"); clr.type = "button"; clr.id = "fcalc-clear"; clr.textContent = "مسح C";
    grid.appendChild(clr);

    btn.addEventListener("click", function () { box.classList.toggle("open"); });
    grid.addEventListener("click", function (e) {
      var t = e.target;
      if (t.id === "fcalc-clear") { display.value = ""; return; }
      var k = t.getAttribute("data-k");
      if (!k) return;
      if (k === "=") {
        try { display.value = String(eval(display.value)); } catch(e) { display.value = "خطأ"; }
      } else { display.value += k; }
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

if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

selected_id = st.session_state.selected_customer_id

# ---------- Customer Details View ----------
if selected_id is not None:
    customer = get_customer(selected_id)
    if customer is None:
        st.session_state.selected_customer_id = None
        st.rerun()

    if st.button("⬅️ العودة إلى لوحة التحكم"):
        st.session_state.selected_customer_id = None
        st.rerun()

    st.markdown(f"## 👤 سجل العميل: {customer['name']}")
    records = get_records(selected_id)

    add_col, pay_col = st.columns(2)
    with add_col:
        with st.form("add_debt_form", clear_on_submit=True):
            st.subheader("➕ إضافة دين")
            d_amount_str = st.text_input("المبلغ", placeholder="اكتب المبلغ", key="d_amt")
            d_currency = st.selectbox("العملة", CURRENCIES, key="d_curr")
            d_note = st.text_input("البيان", key="d_note")
            if st.form_submit_button("حفظ الدين", use_container_width=True):
                try:
                    amt = float(d_amount_str.strip())
                    if amt > 0:
                        add_record(selected_id, "دين", amt, d_currency, d_note)
                        st.success("تم الحفظ")
                        st.rerun()
                except: st.error("خطأ في المبلغ")
    with pay_col:
        with st.form("add_pay_form", clear_on_submit=True):
            st.subheader("💵 تسجيل تسديد")
            p_amount_str = st.text_input("مبلغ التسديد", placeholder="اكتب المبلغ", key="p_amt")
            p_currency = st.selectbox("العملة", CURRENCIES, key="p_curr")
            p_note = st.text_input("البيان", key="p_note")
            if st.form_submit_button("حفظ التسديد", use_container_width=True):
                try:
                    amt = float(p_amount_str.strip())
                    if amt > 0:
                        add_record(selected_id, "تسديد", amt, p_currency, p_note)
                        st.success("تم الحفظ")
                        st.rerun()
                except: st.error("خطأ في المبلغ")

    st.markdown("### 📋 العمليات المسجلة")
    for rec in records:
        with st.container(border=True):
            st.markdown(f"**{rec['type']}** · **{money(rec['amount'])} {rec['currency']}**")
            st.caption(f"{rec['created_at']} | {rec['note'] or 'بدون ملاحظة'}")

# ---------- Main Dashboard View ----------
else:
    # 1. شريط البحث العلوي
    st.text_input("بحث شامل...", placeholder="🔍 ابحث عن عميل...", key="customer_search")

    # 2. بطاقة العضوية الخضراء تماماً مثل الصورة
    st.markdown("""
        <div class="sub-card">
            <div class="sub-header">
                <span class="sub-name">اصيل الحبيشي</span>
                <span class="sub-badge">قريب الانتهاء 🟠</span>
            </div>
            <div class="sub-email">asil1537671@gmail.com</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 4px;">باقة النسخة الكاملة</div>
            <div class="sub-footer">
                <span>الأيام المتبقية: 17 يوم</span>
                <span>تاريخ الانتهاء: 2026/11/10</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. بطاقة التحصيلات اليومية والترحيب
    st.markdown("""
        <div class="welcome-card">
            <div class="welcome-text">مساء الخير, اصيل الحبيشي 👋</div>
            <div class="collection-tag">✔ تحصيلات اليوم: 1,000 IQD</div>
        </div>
    """, unsafe_allow_html=True)

    # 4. قسم الإحصائيات (4 مربعات تماماً كالصورة)
    customers = get_customers()
    all_records = []
    for c in customers:
        all_records.extend(get_records(c["id"]))

    total_debtors = sum(1 for c in customers if any(r["type"] == "دين" for r in get_records(c["id"])))
    total_customers_count = len(customers)

    total_debt_amount = sum(r["amount"] for r in all_records if r["type"] == "دين")
    total_paid_amount = sum(r["amount"] for r in all_records if r["type"] == "تسديد")
    net_amount = total_debt_amount - total_paid_amount

    st.markdown("<div style='font-weight:700; margin-bottom:8px; color:#1e293b;'>📊 ملخص الاحصائيات</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div class="stat-box-red">
                <div class="stat-title">إجمالي المدينين</div>
                <div class="stat-val">{total_debtors} 👥</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="stat-box-green">
                <div class="stat-title">إجمالي العملاء</div>
                <div class="stat-val">{total_customers_count} 👥</div>
            </div>
        """, unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"""
            <div class="stat-box-red">
                <div class="stat-title">مبالغ المدينين</div>
                <div class="stat-val">IQD {money(net_amount)} 🏛️</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="stat-box-green">
                <div class="stat-title">مبالغ العملاء</div>
                <div class="stat-val">IQD {money(total_paid_amount)} 💳</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 5. إضافة عميل جديد
    with st.expander("➕ إضافة عميل جديد"):
        with st.form("new_cust_form", clear_on_submit=True):
            new_name = st.text_input("اسم العميل")
            if st.form_submit_button("حفظ العميل", use_container_width=True):
                if new_name.strip():
                    try:
                        add_customer(new_name)
                        st.success("تمت الإضافة بنجاح")
                        st.rerun()
                    except:
                        st.error("الاسم موجود مسبقاً")

    # 6. قائمة العملاء والبحث
    st.markdown("### 👥 قائمة العملاء")
    search = st.session_state.get("customer_search", "")
    if search.strip():
        if st.button("✖ إلغاء البحث"):
            st.session_state["customer_search"] = ""
            st.rerun()

    shown_customers = get_customers(search)
    if not shown_customers:
        st.info("لا يوجد عملاء حالياً.")
    else:
        for customer in shown_customers:
            with st.container(border=True):
                c_name, c_btn = st.columns([3, 1])
                with c_name:
                    st.markdown(f"**👤 {customer['name']}**")
                with c_btn:
                    if st.button("فتح السجل", key=f"cust_{customer['id']}", use_container_width=True):
                        st.session_state.selected_customer_id = customer["id"]
                        st.rerun()
