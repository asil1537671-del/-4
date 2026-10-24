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
/* بطاقات الإحصائيات المصغّرة */
.metric-card {
    background: white;
    border: 1px solid #e5eaf3;
    border-radius: 12px;
    padding: 10px 12px;
    box-shadow: 0 2px 8px rgba(25, 45, 85, .04);
    min-height: 75px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric-label { color: #64748b; font-size: .78rem; font-weight: 600; line-height: 1.2; }
.metric-value { color: #14213d; font-size: 1.1rem; font-weight: 800; margin-top: 3px; line-height: 1.25; }
.metric-sub { color: #94a3b8; font-size: .7rem; margin-top: 3px; line-height: 1.2; }
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

def metric_card(label, value, accent="#2563eb", sub=""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""<div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="color:{accent}">{value}</div>
          {sub_html}
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
        background: #2563eb; color: #fff; font-size: 24px; cursor: pointer;
        box-shadow: 0 4px 20px rgba(37,99,235,.4);
        display: flex; align-items: center; justify-content: center;
        transition: transform .2s;
      }
      #fcalc-btn:hover { transform: scale(1.1); }
      #fcalc-box {
        position: fixed; bottom: 95px; left: 25px; z-index: 999999;
        width: 280px; padding: 15px; border-radius: 16px;
        background: #172033; color: #fff; display: none;
        box-shadow: 0 10px 30px rgba(0,0,0,.4);
      }
      #fcalc-box.open { display: block; }
      #fcalc-display {
        box-sizing: border-box; width: 100%; height: 45px; border: 0;
        border-radius: 8px; background: #0b1220; color: #67e8f9;
        text-align: right; font-size: 22px; padding: 7px; margin-bottom: 10px;
        direction: ltr;
      }
      #fcalc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
      #fcalc-grid button, #fcalc-clear {
        border: 0; border-radius: 8px; padding: 10px; background: #334155;
        color: #fff; font-size: 16px; cursor: pointer;
      }
      #fcalc-grid button:hover { background: #475569; }
      #fcalc-clear { grid-column: span 4; background: #dc2626; }
    `;
    document.head.appendChild(style);

    var root = document.createElement("div");
    root.id = "fcalc-root";
    root.innerHTML =
      '<button id="fcalc-btn" type="button" title="الحاسبة">🧮</button>' +
      '<div id="fcalc-box" dir="ltr">' +
      '  <input id="fcalc-display" readonly value="">' +
      '  <div id="fcalc-grid"></div>' +
      '</div>';
    document.body.appendChild(root);

    var box = document.getElementById("fcalc-box");
    var btn = document.getElementById("fcalc-btn");
    var display = document.getElementById("fcalc-display");
    var grid = document.getElementById("fcalc-grid");

    var keys = [
      ["7","7"],["8","8"],["9","9"],["/","÷"],
      ["4","4"],["5","5"],["6","6"],["*","×"],
      ["1","1"],["2","2"],["3","3"],["-","−"],
      ["0","0"],[".","."],["=","="],["+","+"]
    ];
    keys.forEach(function (k) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = k[1];
      b.setAttribute("data-k", k[0]);
      grid.appendChild(b);
    });
    var clr = document.createElement("button");
    clr.type = "button";
    clr.id = "fcalc-clear";
    clr.textContent = "مسح C";
    grid.appendChild(clr);

    btn.addEventListener("click", function () {
      box.classList.toggle("open");
    });

    function calculate() {
      try {
        var expr = display.value;
        if (!/^[0-9+\-*\/.() ]+$/.test(expr)) throw 0;
        var result = Function('"use strict";return (' + expr + ')')();
        if (typeof result !== "number" || !isFinite(result)) throw 0;
        display.value = String(parseFloat(result.toFixed(10)));
      } catch (e) {
        display.value = "خطأ";
      }
    }

    grid.addEventListener("click", function (e) {
      var t = e.target;
      if (t.id === "fcalc-clear") { display.value = ""; return; }
      var k = t.getAttribute("data-k");
      if (!k) return;
      if (display.value === "خطأ") display.value = "";
      if (k === "=") calculate();
      else display.value += k;
    });
  }

  var s = hostDoc.createElement("script");
  s.id = "fcalc-script";
  s.textContent = "(" + init.toString() + ")();";
  hostDoc.body.appendChild(s);
})();
</script>
"""

def floating_calculator():
    components.html(CALC_HTML, height=0)

# ---------- Header / navigation ----------
if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

selected_id = st.session_state.selected_customer_id

# العنوان الرئيسي
st.markdown("# 📒 دفتر ديوني")
st.caption("إدارة الديون والتسديدات بطريقة مرتبة وواضحة")

# تشغيل الحاسبة العائمة في كل الصفحات
floating_calculator()

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

    stat_cols = st.columns(6)
    with stat_cols[0]:
        metric_card("عدد العمليات", str(len(records)), "#2563eb")
    with stat_cols[1]:
        metric_card("الديون", str(sum(1 for r in records if r["type"] == "دين")), "#dc2626")
    with stat_cols[2]:
        metric_card("التسديدات", str(sum(1 for r in records if r["type"] == "تسديد")), "#059669")
    for i, currency in enumerate(CURRENCIES):
        s = summary[currency]
        with stat_cols[3 + i]:
            metric_card(
                f"المتبقي — {currency}",
                money(s["remaining"]),
                "#dc2626" if s["remaining"] > 0 else "#059669",
                f"دين {money(s['debt'])} · مسدد {money(s['paid'])}",
            )

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
    # شريط البحث البارز في الأعلى تماماً مثل الصورة المطلوبة
    st.text_input(
        "بحث شامل...",
        placeholder="🔍 ابحث عن اسم عميل...",
        key="customer_search",
    )

    customers = get_customers()
    all_records = []
    for c in customers:
        all_records.extend(get_records(c["id"]))

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

    total_debt_count = sum(1 for r in all_records if r["type"] == "دين")
    total_payment_count = sum(1 for r in all_records if r["type"] == "تسديد")
    overall = currency_summary(all_records)

    st.markdown("### 📊 ملخص الإحصائيات")
    group_overview, group_totals = st.columns(2, gap="large")
    with group_overview:
        st.caption("نظرة عامة")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("عدد العملاء", str(len(customers)), "#2563eb")
        with c2:
            metric_card("عمليات الديون", str(total_debt_count), "#dc2626")
        with c3:
            metric_card("عمليات التسديد", str(total_payment_count), "#059669")
    with group_totals:
        st.caption("الإجماليات حسب العملة (المتبقي)")
        currency_cols = st.columns(3)
        for i, currency in enumerate(CURRENCIES):
            s = overall[currency]
            with currency_cols[i]:
                metric_card(
                    currency,
                    money(s["remaining"]),
                    "#dc2626" if s["remaining"] > 0 else "#059669",
                    f"ديون {money(s['debt'])} · تسديدات {money(s['paid'])}",
                )

    st.markdown("---")
    st.markdown("### 👥 العملاء")

    search = st.session_state.get("customer_search", "")
    if search.strip():
        info_col, clear_col = st.columns([5, 1])
        info_col.caption(f"نتائج
