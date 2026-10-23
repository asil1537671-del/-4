import json
import os
import streamlit as st
import streamlit.components.v1 as components

# ملف حفظ البيانات محلياً لضمان عدم ضياعها
DATA_FILE = "debt_data.json"


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return {}
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# تهيئة البيانات
if "db" not in st.session_state:
  st.session_state.db = load_data()

st.set_page_config(
    page_title="تطبيق تسجيل الديون", page_icon="💰", layout="centered"
)

st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("💰 تطبيق تسجيل الديون")

# القائمة الجانبية (جهة اليمين) للبحث وسجل العملاء
st.sidebar.header("🔍 البحث والعملاء")
search_query = st.sidebar.text_input("بحث عن عميل...")

# إضافة عميل جديد (الاسم ورقم الهاتف مباشرة)
with st.expander("➕ إضافة عميل جديد", expanded=False):
  with st.form("add_client_form"):
    client_name = st.text_input("اسم العميل")
    client_phone = st.text_input("رقم الهاتف")
    submitted_client = st.form_submit_button("إضافة العميل")
    if submitted_client:
      if client_name:
        if client_name not in st.session_state.db:
          st.session_state.db[client_name] = {
              "phone": client_phone,
              "transactions": [],
          }
          save_data(st.session_state.db)
          st.success(f"تمت إضافة العميل {client_name} بنجاح!")
          st.rerun()
        else:
          st.warning("اسم العميل موجود مسبقاً!")
      else:
        st.error("يرجى إدخال اسم العميل على الأقل.")

# تصفية العملاء بناءً على البحث
clients = list(st.session_state.db.keys())
if search_query:
  clients = [c for c in clients if search_query in c]

if not clients:
  st.info("لا توجد عملاء مسجلين حالياً أو مطابقة للبحث.")
else:
  selected_client = st.selectbox("اختر العميل لعرض حسابه:", clients)

  if selected_client:
    client_data = st.session_state.db[selected_client]
    st.subheader(f"حساب العميل: {selected_client}")
    if client_data.get("phone"):
      st.write(f"📱 رقم الهاتف: {client_data['phone']}")

    # حساب الإجماليات
    total_debt = sum(
        t["amount"]
        for t in client_data["transactions"]
        if t["type"] == "دين"
    )
    total_paid = sum(
        t["amount"]
        for t in client_data["transactions"]
        if t["type"] == "تسديد"
    )
    remaining = total_debt - total_paid

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الديون", f"{total_debt:,.2f}")
    col2.metric("إجمالي المدفوعات", f"{total_paid:,.2f}")
    col3.metric("المتبقي", f"{remaining:,.2f}")

    # --- الحاسبة العائمة والمتنقلة في صفحة العميل ---
    with st.expander("🧮 الحاسبة السريعة", expanded=False):
      calculator_html = """
            <div style="background: #ffffff; padding: 15px; border-radius: 12px; max-width: 280px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ddd;">
                <input type="text" id="calc-display" style="width: 100%; height: 45px; font-size: 22px; text-align: right; margin-bottom: 10px; padding: 5px; border-radius: 6px; border: 1px solid #ccc; background: #f9f9f9;" readonly>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;">
                    <button onclick="clearDisp()" style="padding: 12px; font-size: 16px; background: #ff6b6b; color: white; border: none; border-radius: 6px; font-weight: bold;">C</button>
                    <button onclick="appendVal('/')" style="padding: 12px; font-size: 16px; background: #e0e0e0; border: none; border-radius: 6px; font-weight: bold;">/</button>
                    <button onclick="appendVal('*')" style="padding: 12px; font-size: 16px; background: #e0e0e0; border: none; border-radius: 6px; font-weight: bold;">*</button>
                    <button onclick="appendVal('-')" style="padding: 12px; font-size: 16px; background: #e0e0e0; border: none; border-radius: 6px; font-weight: bold;">-</button>
                    <button onclick="appendVal('7')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">7</button>
                    <button onclick="appendVal('8')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">8</button>
                    <button onclick="appendVal('9')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">9</button>
                    <button onclick="appendVal('+')" style="padding: 12px; font-size: 16px; background: #e0e0e0; border: none; border-radius: 6px; font-weight: bold;" rowspan="2">+</button>
                    <button onclick="appendVal('4')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">4</button>
                    <button onclick="appendVal('5')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">5</button>
                    <button onclick="appendVal('6')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">6</button>
                    <button onclick="appendVal('1')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">1</button>
                    <button onclick="appendVal('2')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">2</button>
                    <button onclick="appendVal('3')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">3</button>
                    <button onclick="calculate()" style="padding: 12px; font-size: 16px; background: #4caf50; color: white; border: none; border-radius: 6px; font-weight: bold; grid-column: span 2;">=</button>
                    <button onclick="appendVal('0')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px; grid-column: span 2;">0</button>
                    <button onclick="appendVal('.')" style="padding: 12px; font-size: 16px; background: #fff; border: 1px solid #ddd; border-radius: 6px;">.</button>
                </div>
            </div>
            <script>
                function appendVal(val) { document.getElementById('calc-display').value += val; }
                function clearDisp() { document.getElementById('calc-display').value = ''; }
                function calculate() {
                    try { document.getElementById('calc-display').value = eval(document.getElementById('calc-display').value); }
                    catch(e) { document.getElementById('calc-display').value = 'خطأ'; }
                }
            </script>
            """
      components.html(calculator_html, height=320)

    # قسم تسجيل دين جديد (بدون الدين العام، مبلغ يقبل الكسور العشرية)
    with st.expander("➕ تسجيل دين جديد", expanded=False):
      with st.form(f"add_debt_{selected_client}"):
        debt_amount = st.number_input(
            "مبلغ الدين", min_value=0.0, step=0.01, format="%.2f"
        )
        debt_currency = st.selectbox(
            "العملة", ["ريال يمني", "دولار أمريكي"]
        )
        debt_notes = st.text_area("ملاحظات (اختياري)")
        submit_debt = st.form_submit_button("حفظ الدين")
        if submit_debt and debt_amount > 0:
          client_data["transactions"].append({
              "type": "دين",
              "amount": debt_amount,
              "currency": debt_currency,
              "notes": debt_notes,
          })
          save_data(st.session_state.db)
          st.success("تم تسجيل الدين بنجاح!")
          st.rerun()

    # قسم تسجيل تسديد (تمت إزالة خيار "اختر الدين" ومطابقة الحقول)
    with st.expander("💵 تسجيل تسديد دفعة", expanded=False):
      with st.form(f"add_payment_{selected_client}"):
        pay_amount = st.number_input(
            "مبلغ التسديد", min_value=0.0, step=0.01, format="%.2f"
        )
        pay_currency = st.selectbox(
            "عملة التسديد", ["ريال يمني", "دولار أمريكي"]
        )
        pay_notes = st.text_area("ملاحظات التسديد (اختياري)")
        submit_pay = st.form_submit_button("حفظ التسديد")
        if submit_pay and pay_amount > 0:
          client_data["transactions"].append({
              "type": "تسديد",
              "amount": pay_amount,
              "currency": pay_currency,
              "notes": pay_notes,
          })
          save_data(st.session_state.db)
          st.success("تم تسجيل التسديد بنجاح!")
          st.rerun()

    # سجل العمليات مع الملاحظات وخيار الحذف
    st.markdown("---")
    st.subheader("📋 سجل العمليات")
    if not client_data["transactions"]:
      st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")
    else:
      for idx, tx in enumerate(client_data["transactions"]):
        cols = st.columns([2, 3, 2, 1])
        tx_type_color = (
            "🔴 دين" if tx["type"] == "دين" else "🟢 تسديد"
        )
        cols[0].write(f"**{tx_type_color}**")
        cols[1].write(
            f"المبلغ: {tx['amount']:,.2f} {tx.get('currency', '')}"
        )
        cols[2].write(f"ملاحظات: {tx.get('notes', 'لا توجد')}")

        if cols[3].button("🗑️", key=f"del_{selected_client}_{idx}"):
          client_data["transactions"].pop(idx)
          save_data(st.session_state.db)
          st.success("تم حذف السجل بنجاح!")
          st.rerun()