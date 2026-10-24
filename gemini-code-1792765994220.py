import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from pathlib import Path
from datetime import datetime, date, time

APP_DIR = Path(file).resolve().parent
DB_PATH = APP_DIR / "daftar_deyoon.db"
CURRENCIES = ["ريال يمني", "ريال سعودي", "دولار أمريكي"]

st.set_page_config(
page_title="دفتر ديوني",
page_icon="📒",
layout="wide",
initial_sidebar_state="collapsed",
)

---------- Database ----------

def get_conn():
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
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

init_db()

---------- Modern teal / pink design ----------

st.markdown("""

<style>  
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');  
html, body, [class*="css"], [data-testid="stAppViewContainer"] {  
    font-family: 'Cairo', sans-serif;  
}  
.stApp {  
    background: #f8fafb;  
    color: #303b55;  
}  
[data-testid="stHeader"] { background: transparent; }  
.block-container {  
    max-width: 1180px;  
    padding-top: 1.2rem;  
    padding-bottom: 6rem;  
}  
h1, h2, h3 { color: #303b55; font-weight: 800; }  
.app-header {  
    background: #ffffff;  
    border: 1px solid #e7ecef;  
    border-radius: 20px;  
    padding: 18px 22px;  
    margin-bottom: 16px;  
    box-shadow: 0 4px 18px rgba(34, 66, 80, .04);  
}  
.app-title { color: #159b8b; font-size: 1.8rem; font-weight: 800; }  
.app-subtitle { color: #8b95a7; font-size: .92rem; }  
.metric-card {  
    background: #fff;  
    border: 1px solid #e6ecee;  
    border-radius: 20px;  
    padding: 16px 14px;  
    min-height: 112px;  
    box-shadow: 0 5px 18px rgba(34, 66, 80, .045);  
}  
.metric-label { color: #8791a2; font-size: .86rem; font-weight: 700; }  
.metric-value { font-size: 1.3rem; font-weight: 800; line-height: 1.5; margin-top: 5px; overflow-wrap: anywhere; }  
.metric-sub { color: #9aa3b1; font-size: .72rem; margin-top: 4px; }  
.section-label {  
    color: #159b8b; font-weight: 800; font-size: 1.08rem;  
    background: #e7f6f3; border: 1px solid #bfe5df;  
    display: inline-block; border-radius: 14px; padding: 7px 13px;  
}  
.customer-card {  
    background: #fff; border: 1px solid #e7ecef; border-radius: 18px;  
    padding: 15px 17px; box-shadow: 0 4px 15px rgba(34,66,80,.04);  
}  
div.stButton > button, div.stFormSubmitButton > button {  
    border-radius: 13px; min-height: 2.75rem; font-weight: 800;  
    border: 1px solid #dce7e8; transition: all .15s ease;  
}  
div.stButton > button:hover, div.stFormSubmitButton > button:hover {  
    border-color: #159b8b; color: #118b7e;  
}  
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {  
    background: #08ad8b; border-color: #08ad8b; color: white;  
}  
div[data-testid="stExpander"] {  
    background: #fff; border: 1px solid #e6ecee; border-radius: 16px;  
}  
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,  
[data-testid="stSelectbox"] div[data-baseweb="select"],  
[data-testid="stTextArea"] textarea {  
    border-radius: 13px !important;  
}  
[data-testid="stDialog"] > div {  
    border-radius: 24px !important;  
}  
hr { border-color: #e7ecef; }  
.small-muted { color: #8b95a7; font-size: .85rem; }  
</style>  """, unsafe_allow_html=True)

def money(value):
return f"{float(value):,.2f}".rstrip("0").rstrip(".")

def metric_card(label, value, accent="#159b8b", sub=""):
sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
st.markdown(
f"""<div class="metric-card">
<div class="metric-label">{label}</div>
<div class="metric-value" style="color:{accent}">{value}</div>
{sub_html}</div>""",
unsafe_allow_html=True,
)

def get_customers(search=""):
with get_conn() as conn:
if search.strip():
return conn.execute(
"SELECT * FROM customers WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
(f"%{search.strip()}%",),
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
(name.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
)

def add_record(customer_id, kind, amount, currency, note, created_at):
with get_conn() as conn:
conn.execute(
"""INSERT INTO records(customer_id, type, amount, currency, note, created_at)
VALUES(?, ?, ?, ?, ?, ?)""",
(customer_id, kind, float(amount), currency, note.strip(), created_at),
)

def clear_search():
st.session_state["customer_search"] = ""

---------- Floating calculator: light, teal, modern ----------

CALC_HTML = r"""

<div id="calc-app">  
  <button id="calc-toggle" aria-label="فتح الحاسبة">🧮</button>  
  <section id="calc-panel" aria-label="الحاسبة">  
    <div class="calc-head"><span>الحاسبة</span><button id="calc-close" aria-label="إغلاق">×</button></div>  
    <input id="calc-screen" value="0" readonly aria-label="نتيجة الحساب">  
    <div class="calc-grid">  
      <button data-key="clear" class="calc-soft">AC</button><button data-key="(" class="calc-soft">(</button>  
      <button data-key=")" class="calc-soft">)</button><button data-key="/" class="calc-op">÷</button>  
      <button data-key="7">7</button><button data-key="8">8</button><button data-key="9">9</button><button data-key="*" class="calc-op">×</button>  
      <button data-key="4">4</button><button data-key="5">5</button><button data-key="6">6</button><button data-key="-" class="calc-op">−</button>  
      <button data-key="1">1</button><button data-key="2">2</button><button data-key="3">3</button><button data-key="+" class="calc-op">+</button>  
      <button data-key="0" class="calc-zero">0</button><button data-key=".">.</button><button data-key="=" class="calc-equals">=</button>  
    </div>  
  </section>  
</div>  
<style>  
#calc-app { font-family: Arial,sans-serif; }  
#calc-toggle {  
 position:fixed; bottom:24px; left:22px; z-index:99999; width:58px;height:58px;  
 border:0;border-radius:20px;background:linear-gradient(135deg,#18b7a3,#098b80);color:#fff;  
 font-size:26px;box-shadow:0 8px 24px rgba(21,155,139,.28);cursor:pointer;  
}  
#calc-panel {  
 position:fixed;bottom:94px;left:20px;z-index:99999;width:285px;max-width:calc(100vw - 40px);  
 padding:15px;border:1px solid #dcefeb;border-radius:23px;background:#fff;color:#303b55;  
 box-shadow:0 15px 45px rgba(30,60,70,.18);display:none;  
}  
#calc-panel.open {display:block}  
.calc-head {display:flex;justify-content:space-between;align-items:center;font-weight:800;color:#159b8b;margin-bottom:12px}  
#calc-close {border:0;background:#f2f6f7;color:#687386;border-radius:10px;width:30px;height:30px;font-size:22px;cursor:pointer}  
#calc-screen {box-sizing:border-box;width:100%;height:54px;border:1px solid #dcefeb;border-radius:14px;background:#f5fbfa;color:#26354d;text-align:right;font-size:25px;font-weight:700;padding:10px;margin-bottom:12px}  
.calc-grid {display:grid;grid-template-columns:repeat(4,1fr);gap:7px}  
.calc-grid button {height:44px;border:1px solid #edf0f2;border-radius:12px;background:#f7f9fa;color:#303b55;font-size:17px;font-weight:700;cursor:pointer}  
.calc-grid button:hover {filter:brightness(.97)}  
.calc-grid .calc-op {background:#e6f6f2;color:#128d80;border-color:#d4eee8}  
.calc-grid .calc-soft {background:#fff0f4;color:#dc4c78}  
.calc-grid .calc-equals {background:#159b8b;color:#fff;border-color:#159b8b}  
.calc-grid .calc-zero {grid-column:span 2}  
</style>  
<script>  
(function(){  
 const panel=document.getElementById('calc-panel'), toggle=document.getElementById('calc-toggle');  
 const screen=document.getElementById('calc-screen'), close=document.getElementById('calc-close');  
 if(!panel || panel.dataset.ready) return; panel.dataset.ready='1';  
 let expr='';  
 toggle.addEventListener('click',()=>panel.classList.toggle('open'));  
 close.addEventListener('click',()=>panel.classList.remove('open'));  
 panel.querySelector('.calc-grid').addEventListener('click',e=>{  
   const key=e.target.getAttribute('data-key'); if(!key)return;  
   if(key==='clear'){expr='';screen.value='0';return;}  
   if(key==='='){  
     if(!expr)return;  
     if(!/^[0-9+*/(). -]+$/.test(expr)){screen.value='خطأ';expr='';return;}  
     try { const result=Function('"use strict";return ('+expr+')')();  
       if(typeof result!=='number'||!Number.isFinite(result))throw Error();  
       expr=String(Number(result.toFixed(8)));screen.value=expr;  
     } catch(err){screen.value='خطأ';expr='';}  
     return;  
   }  
   if(screen.value==='خطأ'){expr='';}  
   expr+=key;screen.value=expr;  
 });  
})();  
</script>  
"""  
def floating_calculator():  
    # The calculator runs in a small component frame, with its own fixed floating controls.  
    components.html(CALC_HTML, height=0, scrolling=False)  ---------- Session state ----------

if "selected_customer_id" not in st.session_state:
st.session_state.selected_customer_id = None
if "show_customer_list" not in st.session_state:
st.session_state.show_customer_list = False

selected_id = st.session_state.selected_customer_id

st.markdown("""

<div class="app-header">  
  <div class="app-title">📒 دفتر ديوني</div>  
  <div class="app-subtitle">إدارة الديون والتسديدات — بشكل بسيط وواضح</div>  
</div>  
""", unsafe_allow_html=True)  Search is kept compact and visible, with a clear icon.

search_col, add_col = st.columns([4, 1])
with search_col:
search = st.text_input("🔎 بحث عن عميل", placeholder="اكتب اسم العميل للبحث...", key="customer_search")
with add_col:
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
if st.button("＋ عميل جديد", use_container_width=True):
st.session_state.open_add_customer = True

if st.session_state.get("open_add_customer", False):
@st.dialog("إضافة عميل جديد")
def add_customer_dialog():
with st.form("new_customer_form", clear_on_submit=True):
name = st.text_input("اسم العميل", placeholder="مثال: محمد أحمد")
save = st.form_submit_button("حفظ العميل", type="primary", use_container_width=True)
if save:
if not name.strip():
st.error("اكتب اسم العميل أولًا.")
else:
try:
add_customer(name)
st.session_state.open_add_customer = False
st.success("تمت إضافة العميل بنجاح.")
st.rerun()
except sqlite3.IntegrityError:
st.error("هذا الاسم موجود مسبقًا.")
add_customer_dialog()

---------- Customer details ----------

if selected_id is not None:
customer = get_customer(selected_id)
if customer is None:
st.session_state.selected_customer_id = None
st.rerun()

if st.button("← العودة إلى سجل العملاء", use_container_width=False):  
    st.session_state.selected_customer_id = None  
    st.rerun()  

st.markdown(f"## 👤 {customer['name']}")  
records = get_records(selected_id)  
summary = currency_summary(records)  

stat_cols = st.columns(3)  
with stat_cols[0]:  
    metric_card("عدد العمليات", str(len(records)), "#159b8b")  
with stat_cols[1]:  
    metric_card("عمليات الديون", str(sum(1 for r in records if r["type"] == "دين")), "#e94d79")  
with stat_cols[2]:  
    metric_card("عمليات التسديد", str(sum(1 for r in records if r["type"] == "تسديد")), "#08ad8b")  

st.markdown("#### 💱 الرصيد حسب العملة")  
curr_cols = st.columns(3)  
for i, currency in enumerate(CURRENCIES):  
    s = summary[currency]  
    with curr_cols[i]:  
        metric_card(currency, money(s["remaining"]), "#e94d79" if s["remaining"] > 0 else "#08ad8b",  
                    f"ديون {money(s['debt'])} · مسدد {money(s['paid'])}")  

# Form dialog is styled pink for debt and green for payment, like the reference.  
def transaction_dialog(kind):  
    color = "#e94d79" if kind == "دين" else "#08ad8b"  
    title = "إضافة دين" if kind == "دين" else "تسجيل تسديد"  
    @st.dialog(title)  
    def dialog():  
        st.markdown(f"<div style='color:{color};font-size:1.2rem;font-weight:800;margin-bottom:10px'>{'↑' if kind == 'دين' else '↓'} {title}</div>", unsafe_allow_html=True)  
        with st.form(f"transaction_{kind}_{selected_id}", clear_on_submit=True):  
            amount = st.text_input("المبلغ", placeholder="مثال: 250 أو 250.75")  
            currency = st.selectbox("نوع العملة", CURRENCIES)  
            note = st.text_area("الملاحظة (اختياري)", placeholder="اكتب تفاصيل العملية إن وجدت...", height=90)  
            c1, c2 = st.columns(2)  
            with c1:  
                transaction_date = st.date_input("تاريخ العملية", value=date.today())  
            with c2:  
                transaction_time = st.time_input("وقت العملية", value=datetime.now().time().replace(second=0, microsecond=0))  
            st.markdown(f"<div style='border-radius:14px;background:{'#fff0f4' if kind == 'دين' else '#e6f7f2'};padding:10px;color:{color};font-weight:700;margin:8px 0'>● {'لون وردي لإضافة الدين' if kind == 'دين' else 'لون أخضر لتسجيل التسديد'}</div>", unsafe_allow_html=True)  
            submitted = st.form_submit_button(title, type="primary", use_container_width=True)  
            if submitted:  
                try:  
                    value = float(amount.strip().replace(",", ""))  
                    if value <= 0:  
                        raise ValueError  
                    created_at = datetime.combine(transaction_date, transaction_time).strftime("%Y-%m-%d %H:%M")  
                    add_record(selected_id, kind, value, currency, note, created_at)  
                    st.success("تم الحفظ بنجاح.")  
                    st.rerun()  
                except (ValueError, AttributeError):  
                    st.error("أدخل مبلغًا صحيحًا أكبر من صفر.")  
    dialog()  

action1, action2 = st.columns(2)  
with action1:  
    if st.button("↑  إضافة دين", type="primary", use_container_width=True):  
        transaction_dialog("دين")  
with action2:  
    if st.button("↓  تسديد", type="primary", use_container_width=True):  
        transaction_dialog("تسديد")  

st.markdown("---")  
st.markdown('<div class="section-label">📋 سجل العمليات</div>', unsafe_allow_html=True)  
if not records:  
    st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")  
else:  
    for rec in records:  
        is_payment = rec["type"] == "تسديد"  
        accent = "#08ad8b" if is_payment else "#e94d79"  
        soft = "#e6f7f2" if is_payment else "#fff0f4"  
        with st.container(border=True):  
            top, amount_col = st.columns([3, 2])  
            with top:  
                st.markdown(f"<span style='background:{soft};color:{accent};padding:5px 10px;border-radius:10px;font-weight:800'>{'تسديد' if is_payment else 'إضافة دين'}</span>", unsafe_allow_html=True)  
                st.caption(f"📅 {rec['created_at']}")  
                if rec["note"]:  
                    st.markdown(f"**الملاحظة:** {rec['note']}")  
            with amount_col:  
                st.markdown(f"<div style='text-align:left;color:{accent};font-size:1.25rem;font-weight:800'>{money(rec['amount'])}</div><div style='text-align:left;color:#7d8798'>{rec['currency']}</div>", unsafe_allow_html=True)  
            edit_col, delete_col = st.columns(2)  
            with edit_col:  
                if st.button("✏️ تعديل", key=f"edit_{rec['id']}", use_container_width=True):  
                    st.session_state[f"edit_record_{rec['id']}"] = True  
            with delete_col:  
                if st.button("🗑️ حذف", key=f"delete_{rec['id']}", use_container_width=True):  
                    st.session_state[f"confirm_delete_{rec['id']}"] = True  

            if st.session_state.get(f"edit_record_{rec['id']}", False):  
                with st.form(f"edit_form_{rec['id']}"):  
                    new_type = st.selectbox("نوع العملية", ["دين", "تسديد"], index=0 if rec["type"] == "دين" else 1, key=f"edit_type_{rec['id']}")  
                    new_amount = st.text_input("المبلغ", value=str(rec["amount"]), key=f"edit_amount_{rec['id']}")  
                    new_currency = st.selectbox("العملة", CURRENCIES, index=CURRENCIES.index(rec["currency"]) if rec["currency"] in CURRENCIES else 0, key=f"edit_currency_{rec['id']}")  
                    new_note = st.text_input("الملاحظة", value=rec["note"] or "", key=f"edit_note_{rec['id']}")  
                    save_edit, cancel_edit = st.columns(2)  
                    with save_edit:  
                        save = st.form_submit_button("حفظ التعديل", use_container_width=True)  
                    with cancel_edit:  
                        cancel = st.form_submit_button("إلغاء", use_container_width=True)  
                    if save:  
                        try:  
                            val = float(new_amount.strip().replace(",", ""))  
                            if val <= 0: raise ValueError  
                            with get_conn() as conn:  
                                conn.execute("UPDATE records SET type=?, amount=?, currency=?, note=? WHERE id=? AND customer_id=?",  
                                             (new_type, val, new_currency, new_note, rec["id"], selected_id))  
                            st.session_state[f"edit_record_{rec['id']}"] = False  
                            st.rerun()  
                        except ValueError:  
                            st.error("أدخل مبلغًا صحيحًا أكبر من صفر.")  
                    if cancel:  
                        st.session_state[f"edit_record_{rec['id']}"] = False  
                        st.rerun()  

            if st.session_state.get(f"confirm_delete_{rec['id']}", False):  
                st.warning("هل تريد حذف هذه العملية نهائيًا؟")  
                yes, no = st.columns(2)  
                with yes:  
                    if st.button("نعم، احذف", key=f"yes_delete_{rec['id']}", type="primary", use_container_width=True):  
                        with get_conn() as conn:  
                            conn.execute("DELETE FROM records WHERE id=? AND customer_id=?", (rec["id"], selected_id))  
                        st.session_state[f"confirm_delete_{rec['id']}"] = False  
                        st.rerun()  
                with no:  
                    if st.button("إلغاء", key=f"no_delete_{rec['id']}", use_container_width=True):  
                        st.session_state[f"confirm_delete_{rec['id']}"] = False  
                        st.rerun()  

with st.expander("⚠️ حذف العميل بالكامل"):  
    st.warning("سيتم حذف العميل وجميع سجلاته. لا يمكن التراجع عن هذا الإجراء.")  
    if st.button("حذف العميل وسجلاته", type="primary", key="delete_customer"):  
        st.session_state.confirm_delete_customer = selected_id  
    if st.session_state.get("confirm_delete_customer") == selected_id:  
        yes, no = st.columns(2)  
        with yes:  
            if st.button("نعم، احذف العميل", key="confirm_customer_delete", type="primary"):  
                with get_conn() as conn:  
                    conn.execute("DELETE FROM records WHERE customer_id=?", (selected_id,))  
                    conn.execute("DELETE FROM customers WHERE id=?", (selected_id,))  
                st.session_state.selected_customer_id = None  
                st.session_state.pop("confirm_delete_customer", None)  
                st.rerun()  
        with no:  
            if st.button("إلغاء", key="cancel_customer_delete"):  
                st.session_state.pop("confirm_delete_customer", None)  
                st.rerun()

---------- Dashboard ----------

else:
customers = get_customers()
all_records = []
for c in customers:
all_records.extend(get_records(c["id"]))

total_debt_count = sum(1 for r in all_records if r["type"] == "دين")  
total_payment_count = sum(1 for r in all_records if r["type"] == "تسديد")  
overall = currency_summary(all_records)  

st.markdown('<div class="section-label">📊 ملخص الإحصائيات</div>', unsafe_allow_html=True)  
overview_cols = st.columns(3)  
with overview_cols[0]:  
    if st.button(f"👥 إجمالي العملاء  ·  {len(customers)}", use_container_width=True):  
        st.session_state.show_customer_list = not st.session_state.show_customer_list  
with overview_cols[1]:  
    metric_card("إجمالي عمليات الديون", str(total_debt_count), "#e94d79")  
with overview_cols[2]:  
    metric_card("إجمالي التسديدات", str(total_payment_count), "#08ad8b")  

currency_cols = st.columns(3)  
for i, currency in enumerate(CURRENCIES):  
    s = overall[currency]  
    with currency_cols[i]:  
        metric_card(currency, money(s["remaining"]), "#e94d79" if s["remaining"] > 0 else "#08ad8b",  
                    f"ديون {money(s['debt'])} · مسدد {money(s['paid'])}")  

st.markdown("---")  
show_list = st.session_state.show_customer_list or bool(search.strip())  
st.markdown('<div class="section-label">👥 سجل العملاء</div>', unsafe_allow_html=True)  
if show_list:  
    shown_customers = get_customers(search)  
    if not shown_customers:  
        st.info("لا يوجد عملاء مطابقون. أضف عميلًا جديدًا من الأعلى.")  
    else:  
        for customer in shown_customers:  
            records = get_records(customer["id"])  
            summary = currency_summary(records)  
            with st.container(border=True):  
                name_col, balance_col, action_col = st.columns([2.2, 3, 1.2])  
                with name_col:  
                    st.markdown(f"**👤 {customer['name']}**")  
                    st.caption(f"عدد العمليات: {len(records)}")  
                with balance_col:  
                    parts = [f"{money(summary[cur]['remaining'])} {cur}" for cur in CURRENCIES  
                             if summary[cur]["debt"] != 0 or summary[cur]["paid"] != 0]  
                    st.markdown("**المتبقي:** " + (" · ".join(parts) if parts else "لا توجد ديون"))  
                with action_col:  
                    if st.button("فتح السجل ←", key=f"open_customer_{customer['id']}", use_container_width=True):  
                        st.session_state.selected_customer_id = customer["id"]  
                        st.rerun()  
else:  
    st.info("اضغط على «إجمالي العملاء» لعرض جميع العملاء، أو ابحث عن اسم عميل من مربع البحث.")  

st.caption("تُحفظ البيانات محليًا في ملف daftar_deyoon.db بجانب ملف البرنامج. احتفظ بنسخة احتياطية من هذا الملف دوريًا.")

floating_calculator()
