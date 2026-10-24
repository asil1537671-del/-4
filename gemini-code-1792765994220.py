import streamlit as st
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
    background: linear-gradient(180deg, #f5f8ff 0%, #f8fafc 48%, #f3f6fb 100%);
    color: #172033;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1.2rem; padding-bottom: 5rem; max-width: 1400px; }
h1, h2, h3 { color: #14213d; }
div.stButton > button, div.stFormSubmitButton > button {
    border-radius: 12px;
    min-height: 2.7rem;
    font-weight: 700;
    border: 1px solid #d7e0ef;
    transition: all .15s ease;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    border-color: #2563eb;
    color: #1d4ed8;
}
.metric-card {
    background: white;
    border: 1px solid #e5eaf3;
    border-radius: 18px;
    padding: 14px 12px;
    box-shadow: 0 4px 15px rgba(25, 45, 85, .04);
    min-height: 90px;
}
.metric-label { color: #64748b; font-size: .85rem; font-weight: 600; }
.metric-value { color: #14213d; font-size: 1.35rem; font-weight: 800; margin-top: 4px; }
.panel {
    background: white;
    border: 1px solid #e5eaf3;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 6px 20px rgba(25, 45, 85, .04);
}
div[data-testid="stExpander"] {
    background: rgba(255,255,255,.82);
    border: 1px solid #e5eaf3;
    border-radius: 14px;
}
[data-testid="stSidebar"] { background: #eef3fb; }
</style>
""", unsafe_allow_html=True)

def money(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")

def metric_card(label, value, accent="#2563eb"):
    st.markdown(
        f"""<div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="color:{accent}">{value}</div>
        </div>""",
        unsafe_allow_html=True
    )

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

def add_record(customer_id, kind, amount, currency, note):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO records(customer_id, type, amount, currency, note, created_at)
               VALUES(?, ?, ?, ?, ?, ?)""",
            (customer_id, kind, float(amount), currency, note.strip(),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

# ---------- Floating Bubble Calculator (Works everywhere) ----------
def floating_calculator():
    st.markdown("""
    <style>
    .floating-calc-btn {
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 999999;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 50%;
        width: 55px;
        height: 55px;
        font-size: 24px;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
    }
    .floating-calc-btn:hover {
        transform: scale(1.1);
    }
    .floating-calc-box {
        position: fixed;
        bottom: 95px;
        left: 25px;
        z-index: 999999;
        width: 280px;
        background: #172033;
        color: white;
        padding: 15px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        display: none;
    }
    .floating-calc-box input {
        box-sizing: border-box;
        width: 100%;
        height: 45px;
        border: 0;
        border-radius: 8px;
        background: #0b1220;
        color: #67e8f9;
        text-align: right;
        font-size: 22px;
        padding: 7px;
        margin-bottom: 10px;
    }
    .floating-calc-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
    }
    .floating-calc-grid button {
        border: 0;
        border-radius: 8px;
        padding: 10px;
        background: #334155;
        color: white;
        font-size: 16px;
        cursor: pointer;
    }
    .floating-calc-grid button:hover {
        background: #475569;
    }
    </style>

    <button class="floating-calc-btn" onclick="toggleCalc()" title="الحاسبة العائمة">🧮</button>

    <div class="floating-calc-box" id="floatingCalcBox" dir="ltr">
      <input id="calc-display" readonly value="">
      <div class="floating-calc-grid">
        <button onclick="add('7')">7</button><button onclick="add('8')">8</button>
        <button onclick="add('9')">9</button><button onclick="add('/')">÷</button>
        <button onclick="add('4')">4</button><button onclick="add('5')">5</button>
        <button onclick="add('6')">6</button><button onclick="add('*')">×</button>
        <button onclick="add('1')">1</button><button onclick="add('2')">2</button>
        <button onclick="add('3')">3</button><button onclick="add('-')">−</button>
        <button onclick="add('0')">0</button><button onclick="add('.')">.</button>
        <button onclick="calc()">=</button><button onclick="add('+')">+</button>
        <button onclick="clr()" style="grid-column:span 4;background:#dc2626;color:white">مسح C</button>
      </div>
    </div>

    <script>
    function toggleCalc() {
        const box = document.getElementById('floatingCalcBox');
        box.style.display = box.style.display === 'block' ? 'none' : 'block';
    }
    const d = document.getElementById('calc-display');
    function add(v) { d.value += v; }
    function clr() { d.value = ''; }
    function calc() {
      try {
        if(!/^[0-9+\\-*/.() ]+$/.test(d.value)) throw 0;
        d.value = Function('"use strict";return (' + d.value + ')')();
      } catch(e) { d.value = 'خطأ'; }
    }
    </script>
    """, unsafe_allow_html=True)

# ---------- Header / navigation ----------
if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown("# 📒 دفتر ديوني")
    st.caption("إدارة الديون والتسديدات بطريقة مرتبة وواضحة")
with top_right:
    st.markdown("<div style='text-align:left;padding-top:15px;color:#64748b'>نسخة مطوّرة</div>", unsafe_allow_html=True)

# تشغيل فقاعة الحاسبة العائمة في كل مكان
floating_calculator()

selected_id = st.session_state.selected_customer_id

# ---------- Customer details ----------
if selected_id is not None:
    customer = get_customer(selected_id)
    if customer is None:
        st.session_state.selected_customer_id = None
        st.rerun()

    if st.button("⬅️ العودة إلى قائمة العملاء", key="back_customers"):
        st.session_state.selected_customer_id = None
        st.rerun()

    st.markdown(f"## 👤 سجل العميل: {customer['name']}")
    records = get_records(selected_id)
    summary = currency_summary(records)

    metric_cols = st.columns(3)
    total_records = len(records)
    metric_cols[0].metric("عدد العمليات", total_records)
    metric_cols[1].metric("الديون", sum(1 for r in records if r["type"] == "دين"))
    metric_cols[2].metric("التسديدات", sum(1 for r in records if r["type"] == "تسديد"))

    st.markdown("### 💱 الرصيد حسب العملة")
    cols = st.columns(3)
    for i, currency in enumerate(CURRENCIES):
        s = summary[currency]
        with cols[i]:
            metric_card(f"المتبقي — {currency}", money(s["remaining"]), "#dc2626" if s["remaining"] > 0 else "#059669")
            st.caption(f"الدين: {money(s['debt'])} · المسدد: {money(s['paid'])}")

    st.markdown("---")
    add_col, pay_col = st.columns(2)
    with add_col:
        with st.form("add_debt_form", clear_on_submit=True):
            st.subheader("➕ إضافة دين")
            d_amount_str = st.text_input("المبلغ", placeholder="اكتب المبلغ مثل 250 أو 250.75", key="debt_amount_str")
            d_currency = st.selectbox("العملة", CURRENCIES, key="debt_currency")
            d_note = st.text_input("البيان / الملاحظة", key="debt_note")
            if st.form_submit_button("حفظ الدين", use_container_width=True):
                try:
                    d_amount = float(d_amount_str.strip())
                    if d_amount <= 0:
                        raise ValueError
                    add_record(selected_id, "دين", d_amount, d_currency, d_note)
                    st.success("تم حفظ الدين.")
                    st.rerun()
                except ValueError:
                    st.error("الرجاء إدخال مبلغ صحيح أكبر من صفر.")
    with pay_col:
        with st.form("add_payment_form", clear_on_submit=True):
            st.subheader("💵 تسجيل تسديد")
            p_amount_str = st.text_input("مبلغ التسديد", placeholder="اكتب المبلغ مثل 250 أو 250.75", key="pay_amount_str")
            p_currency = st.selectbox("عملة التسديد", CURRENCIES, key="pay_currency")
            p_note = st.text_input("بيان التسديد", key="pay_note")
            if st.form_submit_button("حفظ التسديد", use_container_width=True):
                try:
                    p_amount = float(p_amount_str.strip())
                    if p_amount <= 0:
                        raise ValueError
                    add_record(selected_id, "تسديد", p_amount, p_currency, p_note)
                    st.success("تم تسجيل التسديد.")
                    st.rerun()
                except ValueError:
                    st.error("الرجاء إدخال مبلغ صحيح أكبر من صفر.")

    st.markdown("---")
    st.markdown("### 📋 سجل العمليات")
    if not records:
        st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")
    else:
        for rec in records:
            is_payment = rec["type"] == "تسديد"
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**:{'green' if is_payment else 'red'}[{rec['type']}]** · **{money(rec['amount'])} {rec['currency']}**")
                    st.caption(f"{rec['created_at']}  ·  {rec['note'] or 'بدون ملاحظة'}")
                with right:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        with st.popover("✏️"):
                            with st.form(f"edit_record_{rec['id']}"):
                                edit_type = st.selectbox("نوع العملية", ["دين", "تسديد"],
                                    index=0 if rec["type"] == "دين" else 1, key=f"etype_{rec['id']}")
                                edit_amount_str = st.text_input("المبلغ",
                                    value=str(rec["amount"]), key=f"eamount_{rec['id']}")
                                edit_currency = st.selectbox("العملة", CURRENCIES,
                                    index=CURRENCIES.index(rec["currency"]) if rec["currency"] in CURRENCIES else 0,
                                    key=f"ecurr_{rec['id']}")
                                edit_note = st.text_input("الملاحظة", value=rec["note"] or "", key=f"enote_{rec['id']}")
                                if st.form_submit_button("حفظ التعديل"):
                                    try:
                                        edit_amount = float(edit_amount_str.strip())
                                        with get_conn() as conn:
                                            conn.execute("""UPDATE records SET type=?, amount=?, currency=?, note=?
                                                            WHERE id=? AND customer_id=?""",
                                                (edit_type, edit_amount, edit_currency, edit_note, rec["id"], selected_id))
                                        st.success("تم تعديل العملية.")
                                        st.rerun()
                                    except ValueError:
                                        st.error("مبلغ غير صحيح.")
                    with btn_col2:
                        if st.button("🗑️", key=f"delete_record_{rec['id']}", help="حذف العملية"):
                            st.session_state[f"confirm_delete_record_{rec['id']}"] = True

                if st.session_state.get(f"confirm_delete_record_{rec['id']}", False):
                    st.warning("هل تريد حذف هذه العملية نهائيًا؟")
                    yes, no = st.columns(2)
                    if yes.button("نعم، احذف", key=f"yes_del_rec_{rec['id']}"):
                        with get_conn() as conn:
                            conn.execute("DELETE FROM records WHERE id=?", (rec["id"],))
                        st.session_state.pop(f"confirm_delete_record_{rec['id']}", None)
                        st.rerun()
                    if no.button("إلغاء", key=f"no_del_rec_{rec['id']}"):
                        st.session_state.pop(f"confirm_delete_record_{rec['id']}", None)
                        st.rerun()

    with st.expander("⚠️ حذف العميل بالكامل"):
        st.warning("سيتم حذف العميل وجميع سجلاته من قاعدة البيانات. لا يمكن التراجع عن هذا الإجراء.")
        if st.button("حذف العميل وسجلاته", type="primary", key="delete_customer"):
            st.session_state.confirm_delete_customer = selected_id
        if st.session_state.get("confirm_delete_customer") == selected_id:
            st.error("تأكيد أخير: حذف العميل وكل سجلاته؟")
            yes, no = st.columns(2)
            if yes.button("نعم، احذف العميل", key="confirm_customer_delete"):
                with get_conn() as conn:
                    conn.execute("DELETE FROM records WHERE customer_id=?", (selected_id,))
                    conn.execute("DELETE FROM customers WHERE id=?", (selected_id,))
                st.session_state.selected_customer_id = None
                st.session_state.pop("confirm_delete_customer", None)
                st.rerun()
            if no.button("إلغاء", key="cancel_customer_delete"):
                st.session_state.pop("confirm_delete_customer", None)
                st.rerun()

# ---------- Main dashboard ----------
else:
    customers = get_customers()
    all_records = []
    for c in customers:
        all_records.extend(get_records(c["id"]))

    st.markdown("### 📊 نظرة عامة")
    total_debt_count = sum(1 for r in all_records if r["type"] == "دين")
    total_payment_count = sum(1 for r in all_records if r["type"] == "تسديد")
    
    overview_cols = st.columns(3)
    with overview_cols[0]:
        metric_card("عدد العملاء", str(len(customers)), "#2563eb")
    with overview_cols[1]:
        metric_card("عمليات الديون", str(total_debt_count), "#dc2626")
    with overview_cols[2]:
        metric_card("عمليات التسديد", str(total_payment_count), "#059669")

    st.markdown("### 💱 إجمالي الأرصدة حسب العملة")
    overall = currency_summary(all_records)
    currency_cols = st.columns(3)
    for i, currency in enumerate(CURRENCIES):
        s = overall[currency]
        with currency_cols[i]:
            metric_card(currency, f"المتبقي: {money(s['remaining'])}", "#dc2626" if s["remaining"] > 0 else "#059669")
            st.caption(f"الديون {money(s['debt'])} · التسديدات {money(s['paid'])}")

    st.markdown("---")
    with st.expander("➕ إضافة عميل جديد", expanded=not bool(customers)):
        with st.form("new_customer_form", clear_on_submit=True):
            new_name = st.text_input("اسم العميل", placeholder="اكتب اسم العميل هنا")
            if st.form_submit_button("حفظ العميل", use_container_width=True):
                if not new_name.strip():
                    st.error("اكتب اسم العميل أولًا.")
                else:
                    try:
                        add_customer(new_name)
                        st.success("تمت إضافة العميل بنجاح.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("هذا الاسم موجود مسبقًا.")

    st.markdown("### 👥 العملاء")
    search = st.text_input("🔎 ابحث عن عميل", placeholder="اكتب جزءًا من الاسم...")
    shown_customers = get_customers(search)

    if not shown_customers:
        st.info("لا يوجد عملاء مطابقون للبحث. أضف عميلًا جديدًا من الأعلى.")
    else:
        for customer in shown_customers:
            records = get_records(customer["id"])
            summary = currency_summary(records)
            with st.container(border=True):
                name_col, balance_col, action_col = st.columns([3, 3, 1.5])
                with name_col:
                    st.markdown(f"**👤 {customer['name']}**")
                    st.caption(f"عدد العمليات: {len(records)}")
                with balance_col:
                    parts = [f"{money(summary[cur]['remaining'])} {cur}" for cur in CURRENCIES
                             if summary[cur]["debt"] != 0 or summary[cur]["paid"] != 0]
                    st.markdown("**المتبقي:** " + (" · ".join(parts) if parts else "لا توجد ديون"))
                with action_col:
                    if st.button("فتح السجل", key=f"open_customer_{customer['id']}", use_container_width=True):
                        st.session_state.selected_customer_id = customer["id"]
                        st.rerun()

    st.caption("تُحفظ البيانات محليًا في ملف SQLite بجانب ملف البرنامج. خذ نسخة احتياطية من ملف daftar_deyoon.db بشكل دوري.")
