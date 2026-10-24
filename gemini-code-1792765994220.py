import sqlite3
from datetime import datetime
from pathlib import Path
 
import streamlit as st
import streamlit.components.v1 as components
 
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "daftar_deyoon.db"
 
DEBT = "دين"
PAYMENT = "تسديد"
CURRENCIES = ["ريال يمني", "ريال سعودي", "دولار أمريكي"]
 
st.set_page_config(
    page_title="دفتر ديوني",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
 
# ---------- Database ----------
@st.cache_resource
def get_conn() -> sqlite3.Connection:
    """اتصال واحد مشترك (يُنشأ مرة واحدة) مع تفعيل المفاتيح الأجنبية."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('{DEBT}', '{PAYMENT}')),
            amount REAL NOT NULL CHECK(amount >= 0),
            currency TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_records_customer ON records(customer_id);
        """
    )
    conn.commit()
    return conn
 
 
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
 
 
def query(sql: str, params: tuple = ()):
    return get_conn().execute(sql, params).fetchall()
 
 
def execute(sql: str, params: tuple = ()):
    conn = get_conn()
    with conn:  # commit / rollback تلقائي
        conn.execute(sql, params)
 
 
def get_customers(search: str = ""):
    search = search.strip()
    if search:
        return query(
            "SELECT * FROM customers WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
            (f"%{search}%",),
        )
    return query("SELECT * FROM customers ORDER BY name COLLATE NOCASE")
 
 
def get_customer(customer_id):
    rows = query("SELECT * FROM customers WHERE id=?", (customer_id,))
    return rows[0] if rows else None
 
 
def get_records(customer_id):
    return query(
        "SELECT * FROM records WHERE customer_id=? ORDER BY id DESC", (customer_id,)
    )
 
 
def totals_by_customer():
    """ملخص كل العملاء باستعلام واحد بدل استعلام لكل عميل."""
    rows = query(
        """SELECT customer_id, currency, type, SUM(amount) AS total, COUNT(*) AS n
           FROM records GROUP BY customer_id, currency, type"""
    )
    result = {}
    for r in rows:
        entry = result.setdefault(r["customer_id"], {"count": 0, "summary": {}})
        entry["count"] += r["n"]
        s = entry["summary"].setdefault(r["currency"], {"debt": 0.0, "paid": 0.0})
        s["debt" if r["type"] == DEBT else "paid"] += float(r["total"])
    return result
 
 
def summarize(records):
    summary = {c: {"debt": 0.0, "paid": 0.0, "remaining": 0.0} for c in CURRENCIES}
    for r in records:
        if r["currency"] in summary:
            key = "debt" if r["type"] == DEBT else "paid"
            summary[r["currency"]][key] += float(r["amount"])
    for s in summary.values():
        s["remaining"] = s["debt"] - s["paid"]
    return summary
 
 
def add_customer(name: str):
    execute(
        "INSERT INTO customers(name, created_at) VALUES(?, ?)",
        (name.strip(), now_str()),
    )
 
 
def add_record(customer_id, kind, amount, currency, note):
    execute(
        """INSERT INTO records(customer_id, type, amount, currency, note, created_at)
           VALUES(?, ?, ?, ?, ?, ?)""",
        (customer_id, kind, float(amount), currency, note.strip(), now_str()),
    )
 
 
# ---------- Helpers ----------
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬،", "0123456789.,,")
 
 
def parse_amount(text: str) -> float:
    """يقبل الأرقام العربية والفاصلة؛ يرفع ValueError إن لم يكن المبلغ > 0."""
    cleaned = (text or "").strip().translate(_AR_DIGITS).replace(",", "")
    value = float(cleaned)
    if value <= 0 or value != value or value == float("inf"):
        raise ValueError
    return round(value, 2)
 
 
def money(value: float) -> str:
    text = f"{value:,.2f}"
    return text.rstrip("0").rstrip(".") if "." in text else text
 
 
def clear_search():
    st.session_state["customer_search"] = ""
 
 
# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Cairo', sans-serif; }
.stApp {
    background: linear-gradient(180deg, #f5f8ff 0%, #f8fafc 48%, #f3f6fb 100%);
    color: #172033;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1.2rem; padding-bottom: 5rem; max-width: 1400px; }
h1, h2, h3 { color: #14213d; }
div.stButton > button, div.stFormSubmitButton > button {
    border-radius: 12px; min-height: 2.7rem; font-weight: 700;
    border: 1px solid #d7e0ef; transition: all .15s ease;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    border-color: #2563eb; color: #1d4ed8;
}
/* زر حفظ الدين: أحمر */
.st-key-add_debt_form div.stFormSubmitButton > button {
    background: #dc2626; color: #fff; border-color: #dc2626;
}
.st-key-add_debt_form div.stFormSubmitButton > button:hover {
    background: #b91c1c; border-color: #b91c1c; color: #fff;
}
/* زر حفظ التسديد: أخضر */
.st-key-add_payment_form div.stFormSubmitButton > button {
    background: #059669; color: #fff; border-color: #059669;
}
.st-key-add_payment_form div.stFormSubmitButton > button:hover {
    background: #047857; border-color: #047857; color: #fff;
}
.metric-card {
    background: white; border: 1px solid #e5eaf3; border-radius: 12px;
    padding: 8px 10px; box-shadow: 0 2px 8px rgba(25,45,85,.04); min-height: 72px;
    display: flex; flex-direction: column; justify-content: center;
}
.metric-label { color: #64748b; font-size: .74rem; font-weight: 600; line-height: 1.2; }
.metric-value { font-size: 1.05rem; font-weight: 800; margin-top: 2px; line-height: 1.25; }
.metric-sub { color: #94a3b8; font-size: .66rem; margin-top: 2px; line-height: 1.2; }
div[data-testid="stExpander"] {
    background: rgba(255,255,255,.82); border: 1px solid #e5eaf3; border-radius: 14px;
}
[data-testid="stSidebar"] { background: #eef3fb; }
</style>
""",
    unsafe_allow_html=True,
)
 
 
def metric_card(label, value, accent="#2563eb", sub=""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""<div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="color:{accent}">{value}</div>
          {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )
 
 
def remaining_color(value):
    return "#dc2626" if value > 0 else "#059669"
 
 
# ---------- Floating Calculator ----------
# تُحقن مرة واحدة في صفحة Streamlit الأم، ويراقبها "حارس" (setInterval + MutationObserver)
# يعيد إنشاء الزر فورًا لو اختفى بعد أي تنقّل أو إعادة رسم، فيظهر في كل الواجهات.
CALC_HTML = r"""
<script>
(function () {
  var hostDoc = window.parent.document;
  if (hostDoc.getElementById("fcalc-script")) return;
 
  function boot() {
    var doc = document;
 
    function build() {
      if (doc.getElementById("fcalc-root")) return;
 
      if (!doc.getElementById("fcalc-style")) {
        var style = doc.createElement("style");
        style.id = "fcalc-style";
        style.textContent = `
          #fcalc-btn { position: fixed; bottom: 25px; left: 25px; z-index: 2147483000;
            width: 55px; height: 55px; border: none; border-radius: 50%;
            background: #2563eb; color: #fff; font-size: 24px; cursor: pointer;
            box-shadow: 0 4px 20px rgba(37,99,235,.4); display: flex;
            align-items: center; justify-content: center; transition: transform .2s; }
          #fcalc-btn:hover { transform: scale(1.1); }
          #fcalc-box { position: fixed; bottom: 95px; left: 25px; z-index: 2147483000;
            width: 280px; padding: 15px; border-radius: 16px; background: #172033;
            color: #fff; display: none; box-shadow: 0 10px 30px rgba(0,0,0,.4); }
          #fcalc-box.open { display: block; }
          #fcalc-display { box-sizing: border-box; width: 100%; height: 45px; border: 0;
            border-radius: 8px; background: #0b1220; color: #67e8f9; text-align: right;
            font-size: 22px; padding: 7px; margin-bottom: 10px; direction: ltr; }
          #fcalc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
          #fcalc-grid button { border: 0; border-radius: 8px; padding: 10px;
            background: #334155; color: #fff; font-size: 16px; cursor: pointer; }
          #fcalc-grid button:hover { background: #475569; }
          #fcalc-grid button.op { background: #2563eb; }
          #fcalc-grid button.op:hover { background: #1d4ed8; }
          #fcalc-grid button.clr { background: #dc2626; grid-column: span 2; }
          #fcalc-grid button.clr:hover { background: #b91c1c; }
        `;
        doc.head.appendChild(style);
      }
 
      var root = doc.createElement("div");
      root.id = "fcalc-root";
      root.innerHTML =
        '<button id="fcalc-btn" type="button" title="الحاسبة">🧮</button>' +
        '<div id="fcalc-box" dir="ltr">' +
        '  <input id="fcalc-display" readonly value="">' +
        '  <div id="fcalc-grid"></div>' +
        '</div>';
      doc.body.appendChild(root);
 
      var box = doc.getElementById("fcalc-box");
      var display = doc.getElementById("fcalc-display");
      var grid = doc.getElementById("fcalc-grid");
 
      var keys = [
        ["C","مسح","clr"],["⌫","⌫",""],["/","÷","op"],
        ["7","7",""],["8","8",""],["9","9",""],["*","×","op"],
        ["4","4",""],["5","5",""],["6","6",""],["-","−","op"],
        ["1","1",""],["2","2",""],["3","3",""],["+","+","op"],
        ["0","0",""],[".",".",""],["=","=","op"]
      ];
      keys.forEach(function (k) {
        var b = doc.createElement("button");
        b.type = "button";
        b.textContent = k[1];
        b.setAttribute("data-k", k[0]);
        if (k[2]) b.className = k[2];
        grid.appendChild(b);
      });
 
      doc.getElementById("fcalc-btn").addEventListener("click", function () {
        box.classList.toggle("open");
      });
 
      function calculate() {
        try {
          var expr = display.value;
          if (!/^[0-9+\-*\/.() ]+$/.test(expr)) throw 0;
          var r = Function('"use strict";return (' + expr + ')')();
          if (typeof r !== "number" || !isFinite(r)) throw 0;
          display.value = String(parseFloat(r.toFixed(10)));
        } catch (e) { display.value = "خطأ"; }
      }
 
      function press(k) {
        if (display.value === "خطأ") display.value = "";
        if (k === "C") display.value = "";
        else if (k === "⌫") display.value = display.value.slice(0, -1);
        else if (k === "=") calculate();
        else display.value += k;
      }
 
      grid.addEventListener("click", function (e) {
        var k = e.target.getAttribute("data-k");
        if (k) press(k);
      });
 
      // دعم لوحة المفاتيح عند فتح الحاسبة (بدون التعارض مع حقول الإدخال)
      doc.addEventListener("keydown", function (e) {
        if (!box.classList.contains("open")) return;
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" && e.target.id !== "fcalc-display") return;
        if (tag === "textarea" || tag === "select") return;
        if (/^[0-9+\-*\/.]$/.test(e.key)) press(e.key);
        else if (e.key === "Enter" || e.key === "=") { e.preventDefault(); press("="); }
        else if (e.key === "Backspace") press("⌫");
        else if (e.key === "Escape") box.classList.remove("open");
      });
    }
 
    build();
    // حارس: يعيد بناء الحاسبة إن حُذفت من الصفحة لأي سبب
    setInterval(build, 1000);
    new MutationObserver(build).observe(doc.body, { childList: true });
  }
 
  var s = hostDoc.createElement("script");
  s.id = "fcalc-script";
  s.textContent = "(" + boot.toString() + ")();";
  hostDoc.body.appendChild(s);
})();
</script>
"""
 
 
def floating_calculator():
    components.html(CALC_HTML, height=0)
 
 
# ---------- Reusable UI ----------
def record_form(form_key, title, kind, amount_label, currency_label, note_label,
                button_label, success_msg, customer_id):
    with st.container(key=form_key):
        with st.form(f"{form_key}_inner", clear_on_submit=True):
            st.subheader(title)
            amount_str = st.text_input(amount_label, placeholder="مثل 250 أو 250.75")
            currency = st.selectbox(currency_label, CURRENCIES)
            note = st.text_input(note_label)
            if st.form_submit_button(button_label, use_container_width=True):
                try:
                    add_record(customer_id, kind, parse_amount(amount_str), currency, note)
                except ValueError:
                    st.error("الرجاء إدخال مبلغ صحيح أكبر من صفر.")
                else:
                    st.toast(success_msg, icon="✅")
                    st.rerun()
 
 
def confirm_dialog(state_key, message, yes_label, yes_key, no_key, on_yes):
    if not st.session_state.get(state_key):
        return
    st.warning(message)
    yes, no = st.columns(2)
    if yes.button(yes_label, key=yes_key):
        on_yes()
        st.session_state.pop(state_key, None)
        st.rerun()
    if no.button("إلغاء", key=no_key):
        st.session_state.pop(state_key, None)
        st.rerun()
 
 
# ---------- Header / navigation ----------
st.session_state.setdefault("selected_customer_id", None)
selected_id = st.session_state.selected_customer_id
 
top_left, top_right = st.columns([9, 1])
with top_left:
    st.markdown("# 📒 دفتر ديوني")
    st.caption("إدارة الديون والتسديدات بطريقة مرتبة وواضحة")
with top_right:
    if selected_id is None:
        st.markdown("<div style='padding-top:14px'></div>", unsafe_allow_html=True)
        with st.popover("🔎", use_container_width=True, help="بحث عن عميل"):
            st.text_input("ابحث عن عميل", placeholder="اكتب جزءًا من الاسم...",
                          key="customer_search")
 
floating_calculator()  # تظهر في كل الواجهات
 
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
    summary = summarize(records)
 
    stat_cols = st.columns(6)
    with stat_cols[0]:
        metric_card("عدد العمليات", str(len(records)))
    with stat_cols[1]:
        metric_card("الديون", str(sum(r["type"] == DEBT for r in records)), "#dc2626")
    with stat_cols[2]:
        metric_card("التسديدات", str(sum(r["type"] == PAYMENT for r in records)), "#059669")
    for i, cur in enumerate(CURRENCIES):
        s = summary[cur]
        with stat_cols[3 + i]:
            metric_card(f"المتبقي — {cur}", money(s["remaining"]),
                        remaining_color(s["remaining"]),
                        f"دين {money(s['debt'])} · مسدد {money(s['paid'])}")
 
    st.markdown("---")
    add_col, pay_col = st.columns(2)
    with add_col:
        record_form("add_debt_form", "➕ إضافة دين", DEBT, "المبلغ", "العملة",
                    "البيان / الملاحظة", "حفظ الدين", "تم حفظ الدين.", selected_id)
    with pay_col:
        record_form("add_payment_form", "💵 تسجيل تسديد", PAYMENT, "مبلغ التسديد",
                    "عملة التسديد", "بيان التسديد", "حفظ التسديد",
                    "تم تسجيل التسديد.", selected_id)
 
    st.markdown("---")
    st.markdown("### 📋 سجل العمليات")
    if not records:
        st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")
    for rec in records:
        rid = rec["id"]
        is_payment = rec["type"] == PAYMENT
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                color = "green" if is_payment else "red"
                st.markdown(f"**:{color}[{rec['type']}]** · **{money(rec['amount'])} {rec['currency']}**")
                st.caption(f"{rec['created_at']}  ·  {rec['note'] or 'بدون ملاحظة'}")
            with right:
                b1, b2 = st.columns(2)
                with b1:
                    with st.popover("✏️"):
                        with st.form(f"edit_record_{rid}"):
                            e_type = st.selectbox("نوع العملية", [DEBT, PAYMENT],
                                                  index=1 if is_payment else 0)
                            e_amount = st.text_input("المبلغ", value=money(rec["amount"]).replace(",", ""))
                            e_cur = st.selectbox(
                                "العملة", CURRENCIES,
                                index=CURRENCIES.index(rec["currency"]) if rec["currency"] in CURRENCIES else 0)
                            e_note = st.text_input("الملاحظة", value=rec["note"] or "")
                            if st.form_submit_button("حفظ التعديل"):
                                try:
                                    amt = parse_amount(e_amount)
                                except ValueError:
                                    st.error("مبلغ غير صحيح.")
                                else:
                                    execute(
                                        """UPDATE records SET type=?, amount=?, currency=?, note=?
                                           WHERE id=? AND customer_id=?""",
                                        (e_type, amt, e_cur, e_note.strip(), rid, selected_id))
                                    st.toast("تم تعديل العملية.", icon="✅")
                                    st.rerun()
                with b2:
                    if st.button("🗑️", key=f"delete_record_{rid}", help="حذف العملية"):
                        st.session_state[f"confirm_delete_record_{rid}"] = True
 
            confirm_dialog(
                f"confirm_delete_record_{rid}",
                "هل تريد حذف هذه العملية نهائيًا؟",
                "نعم، احذف", f"yes_del_rec_{rid}", f"no_del_rec_{rid}",
                lambda rid=rid: execute("DELETE FROM records WHERE id=?", (rid,)),
            )
 
    with st.expander("⚠️ حذف العميل بالكامل"):
        st.warning("سيتم حذف العميل وجميع سجلاته من قاعدة البيانات. لا يمكن التراجع عن هذا الإجراء.")
        if st.button("حذف العميل وسجلاته", type="primary", key="delete_customer"):
            st.session_state["confirm_delete_customer"] = True
 
        def _delete_customer():
            execute("DELETE FROM customers WHERE id=?", (selected_id,))  # CASCADE يحذف السجلات
            st.session_state.selected_customer_id = None
 
        confirm_dialog(
            "confirm_delete_customer",
            "تأكيد أخير: حذف العميل وكل سجلاته؟",
            "نعم، احذف العميل", "confirm_customer_delete", "cancel_customer_delete",
            _delete_customer,
        )
 
# ---------- Main dashboard ----------
else:
    customers = get_customers()
    totals = totals_by_customer()
 
    with st.expander("➕ إضافة عميل جديد", expanded=not customers):
        with st.form("new_customer_form", clear_on_submit=True):
            new_name = st.text_input("اسم العميل", placeholder="اكتب اسم العميل هنا")
            if st.form_submit_button("حفظ العميل", use_container_width=True):
                if not new_name.strip():
                    st.error("اكتب اسم العميل أولًا.")
                else:
                    try:
                        add_customer(new_name)
                    except sqlite3.IntegrityError:
                        st.error("هذا الاسم موجود مسبقًا.")
                    else:
                        st.toast("تمت إضافة العميل بنجاح.", icon="✅")
                        st.rerun()
 
    all_records = query("SELECT type, amount, currency FROM records")
    overall = summarize(all_records)
    debt_ops = sum(r["type"] == DEBT for r in all_records)
    pay_ops = len(all_records) - debt_ops
 
    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.caption("📊 نظرة عامة")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("عدد العملاء", str(len(customers)))
        with c2:
            metric_card("عمليات الديون", str(debt_ops), "#dc2626")
        with c3:
            metric_card("عمليات التسديد", str(pay_ops), "#059669")
    with g2:
        st.caption("💱 الإجماليات حسب العملة (المتبقي)")
        cols = st.columns(3)
        for i, cur in enumerate(CURRENCIES):
            s = overall[cur]
            with cols[i]:
                metric_card(cur, money(s["remaining"]), remaining_color(s["remaining"]),
                            f"ديون {money(s['debt'])} · تسديدات {money(s['paid'])}")
 
    st.markdown("---")
    st.markdown("### 👥 العملاء")
 
    search = st.session_state.get("customer_search", "")
    if search.strip():
        info_col, clear_col = st.columns([5, 1])
        info_col.caption(f"نتائج البحث عن: «{search.strip()}»")
        clear_col.button("✖ إلغاء البحث", on_click=clear_search, use_container_width=True)
 
    shown = get_customers(search)
    if not shown:
        st.info("لا يوجد عملاء مطابقون. أضف عميلًا جديدًا من الأعلى.")
    for customer in shown:
        info = totals.get(customer["id"], {"count": 0, "summary": {}})
        with st.container(border=True):
            name_col, balance_col, action_col = st.columns([3, 3, 1.5])
            with name_col:
                st.markdown(f"**👤 {customer['name']}**")
                st.caption(f"عدد العمليات: {info['count']}")
            with balance_col:
                parts = [
                    f"{money(s['debt'] - s['paid'])} {cur}"
                    for cur in CURRENCIES
                    if (s := info["summary"].get(cur)) and (s["debt"] or s["paid"])
                ]
                st.markdown("**المتبقي:** " + (" · ".join(parts) if parts else "لا توجد ديون"))
            with action_col:
                if st.button("فتح السجل", key=f"open_customer_{customer['id']}",
                             use_container_width=True):
                    st.session_state.selected_customer_id = customer["id"]
                    st.rerun()
 
    st.caption("تُحفظ البيانات محليًا في ملف SQLite بجانب ملف البرنامج. "
               "خذ نسخة احتياطية من ملف daftar_deyoon.db بشكل دوري.")
 
