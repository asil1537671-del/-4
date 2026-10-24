import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime

# Optional dependency for a true floating widget in Streamlit
try:
    from streamlit_float import float_init, float_parent
    FLOAT_AVAILABLE = True
except ImportError:
    FLOAT_AVAILABLE = False

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
    padding: 18px 16px;
    box-shadow: 0 6px 20px rgba(25, 45, 85, .055);
    min-height: 112px;
}
.metric-label { color: #64748b; font-size: .92rem; font-weight: 600; }
.metric-value { color: #14213d; font-size: 1.55rem; font-weight: 800; margin-top: 7px; }
.panel {
    background: white;
    border: 1px solid #e5eaf3;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 6px 20px rgba(25, 45, 85, .04);
}
.customer-card {
    background: white;
    border: 1px solid #e5eaf3;
    border-radius: 16px;
    padding: 15px 17px;
    margin-bottom: 10px;
}
.small-muted { color: #64748b; font-size: .88rem; }
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

# ---------- Floating calculator ----------
def floating_calculator():
    # streamlit-float places this panel above the page. If the optional package
    # is not installed, show a reliable calculator in an expander instead.
    if FLOAT_AVAILABLE:
        try:
            float_init()
            with st.container():
                st.markdown("### 🧮 الحاسبة")
                open_calc = st.toggle("إظهار الحاسبة", key="show_float_calc", value=False)
                if open_calc:
                    st.components.v1.html("""
                    <div dir="ltr" style="font-family:Arial;background:#172033;color:white;
                         padding:12px;border-radius:14px;">
                      <input id="calc-display" readonly value=""
                        style="box-sizing:border-box;width:100%;height:42px;border:0;border-radius:8px;
                        background:#0b1220;color:#67e8f9;text-align:right;font-size:22px;padding:7px;margin-bottom:8px">
                      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px">
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
                    const d=document.getElementById('calc-display');
                    function add(v){d.value+=v}
                    function clr(){d.value=''}
                    function calc(){
                      try {
                        if(!/^[0-9+\\-*/.() ]+$/.test(d.value)) throw 0;
                        d.value=Function('"use strict";return ('+d.value+')')();
                      } catch(e){d.value='خطأ'}
                    }
                    document.querySelectorAll('button').forEach(b=>{
                      b.style.cssText='border:0;border-radius:7px;padding:9px;background:#334155;color:white;font-size:16px;cursor:pointer';
                    });
                    </script>
                    """, height=260, scrolling=False)
            float_parent(css="""
                position: fixed; bottom: 18px; left: 18px; z-index: 999999;
                width: 250px; background: white; border: 1px solid #dbe4f0;
                border-radius: 16px; padding: 10px; box-shadow: 0 10px 35px rgba(15,23,42,.22);
            """)
            return
        except Exception:
            pass

    with st.expander("🧮 الحاسبة", expanded=False):
        st.caption("نسخة بديلة داخل الصفحة. لتفعيل الفقاعة العائمة ثبّت streamlit-float.")
        if "calc_expr" not in st.session_state:
            st.session_state.calc_expr = ""
        st.text_input("العملية الحسابية", key="calc_expr", placeholder="مثال: 120+35*2")
        cc1, cc2 = st.columns(2)
        if cc1.button("احسب", key="calc_eval"):
            try:
                expr = st.session_state.calc_expr.strip()
                if not expr or any(ch not in "0123456789+-*/(). " for ch in expr):
                    raise ValueError
                result = eval(expr, {"__builtins__": {}}, {})
                st.success(f"الناتج: {money(float(result))}")
            except Exception:
                st.error("تحقق من العملية الحسابية.")
        if cc2.button("مسح", key="calc_clear"):
            st.session_state.calc_expr = ""
            st.rerun()

# ---------- Header / navigation ----------
if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown("# 📒 دفتر ديوني")
    st.caption("إدارة الديون والتسديدات بطريقة مرتبة وواضحة")
with top_right:
    st.markdown("<div style='text-align:left;padding-top:15px;color:#64748b'>نسخة مطوّرة</div>", unsafe_allow_html=True)

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
    metric_cols[1].metric("إجمالي الديون (كل عملة منفصلة)", sum(1 for r in records if r["type"] == "دين"))
    metric_cols[2].metric("إجمالي التسديدات (عمليات)", sum(1 for r in records if r["type"] == "تسديد"))

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
            d_amount = st.number_input("المبلغ", min_value=0.0, value=None, step=1.0, format="%.2f", placeholder="اكتب المبلغ مثل 250 أو 250.75", key="debt_amount")
            d_currency = st.selectbox("العملة", CURRENCIES, key="debt_currency")
            d_note = st.text_input("البيان / الملاحظة", key="debt_note")
            if st.form_submit_button("حفظ الدين", use_container_width=True):
                if d_amount is None or d_amount <= 0:
                    st.error("أدخل مبلغًا أكبر من صفر.")
                else:
                    add_record(selected_id, "دين", d_amount, d_currency, d_note)
                    st.success("تم حفظ الدين.")
                    st.rerun()
    with pay_col:
        with st.form("add_payment_form", clear_on_submit=True):
            st.subheader("💵 تسجيل تسديد")
            p_amount = st.number_input("مبلغ التسديد", min_value=0.0, value=None, step=1.0, format="%.2f", placeholder="اكتب المبلغ مثل 250 أو 250.75", key="pay_amount")
            p_currency = st.selectbox("عملة التسديد", CURRENCIES, key="pay_currency")
            p_note = st.text_input("بيان التسديد", key="pay_note")
            if st.form_submit_button("حفظ التسديد", use_container_width=True):
                if p_amount is None or p_amount <= 0:
                    st.error("أدخل مبلغًا أكبر من صفر.")
                else:
                    add_record(selected_id, "تسديد", p_amount, p_currency, p_note)
                    st.success("تم تسجيل التسديد.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 سجل العمليات")
    if not records:
        st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")
    else:
        for rec in records:
            is_payment = rec["type"] == "تسديد"
            title_color = "#059669" if is_payment else "#dc2626"
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**:{'green' if is_payment else 'red'}[{rec['type']}]** · **{money(rec['amount'])} {rec['currency']}**")
                    st.caption(f"{rec['created_at']}  ·  {rec['note'] or 'بدون ملاحظة'}")
                with right:
                    with st.popover("✏️ تعديل"):
                        with st.form(f"edit_record_{rec['id']}"):
                            edit_type = st.selectbox("نوع العملية", ["دين", "تسديد"],
                                index=0 if rec["type"] == "دين" else 1, key=f"etype_{rec['id']}")
                            edit_amount = st.number_input("المبلغ", min_value=0.0,
                                value=float(rec["amount"]), step=10.0, format="%.2f", key=f"eamount_{rec['id']}")
                            edit_currency = st.selectbox("العملة", CURRENCIES,
                                index=CURRENCIES.index(rec["currency"]) if rec["currency"] in CURRENCIES else 0,
                                key=f"ecurr_{rec['id']}")
                            edit_note = st.text_input("الملاحظة", value=rec["note"] or "", key=f"enote_{rec['id']}")
                            if st.form_submit_button("حفظ التعديل"):
                                with get_conn() as conn:
                                    conn.execute("""UPDATE records SET type=?, amount=?, currency=?, note=?
                                                    WHERE id=? AND customer_id=?""",
                                        (edit_type, float(edit_amount), edit_currency, edit_note, rec["id"], selected_id))
                                st.success("تم تعديل العملية.")
                                st.rerun()
                    if st.button("🗑️ حذف", key=f"delete_record_{rec['id']}"):
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

