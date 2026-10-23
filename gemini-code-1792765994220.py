import streamlit as st
import streamlit.components.v1 as components

# إعدادات الصفحة
st.set_page_config(
    page_title="دفتر ديوني",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص الألوان والتصميم ليتطابق مع واجهة الموقع
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #000000;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .record-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# تهيئة بيانات الحالة الافتراضية
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'customers' not in st.session_state:
    st.session_state.customers = {}

if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None

# شاشة تسجيل الدخول
def login_screen():
    st.markdown("<h1 style='text-align: center;'>الدخول - دفتر ديوني</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if username and password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("الرجاء إدخال بيانات صحيحة")

# الآلة الحاسبة العائمة
def floating_calculator():
    calc_html = """
    <div id="floating-calc" style="position: fixed; bottom: 20px; left: 20px; background: #1f2937; padding: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 1000; width: 220px; direction: ltr;">
        <div style="font-size: 14px; color: #fff; margin-bottom: 5px; text-align: center;">الآلة الحاسبة</div>
        <input type="text" id="calc-display" style="width: 100%; height: 35px; font-size: 18px; text-align: right; margin-bottom: 10px; padding: 5px; border-radius: 5px; border: none; background: #111; color: #0ff;" readonly>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px;">
            <button onclick="appendCalc('7')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">7</button>
            <button onclick="appendCalc('8')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">8</button>
            <button onclick="appendCalc('9')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">9</button>
            <button onclick="appendCalc('/')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">/</button>
            <button onclick="appendCalc('4')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">4</button>
            <button onclick="appendCalc('5')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">5</button>
            <button onclick="appendCalc('6')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">6</button>
            <button onclick="appendCalc('*')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">*</button>
            <button onclick="appendCalc('1')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">1</button>
            <button onclick="appendCalc('2')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">2</button>
            <button onclick="appendCalc('3')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">3</button>
            <button onclick="appendCalc('-')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">-</button>
            <button onclick="appendCalc('0')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">0</button>
            <button onclick="clearCalc()" style="background: #ef4444; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">C</button>
            <button onclick="calculateResult()" style="background: #10b981; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">=</button>
            <button onclick="appendCalc('+')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">+</button>
        </div>
    </div>
    <script>
        function appendCalc(val) {
            document.getElementById('calc-display').value += val;
        }
        function clearCalc() {
            document.getElementById('calc-display').value = '';
        }
        function calculateResult() {
            try {
                document.getElementById('calc-display').value = eval(document.getElementById('calc-display').value);
            } catch(e) {
                document.getElementById('calc-display').value = 'خطأ';
            }
        }
    </script>
    """
    components.html(calc_html, height=270)

# التطبيق الرئيسي
def main_app():
    floating_calculator()

    if st.session_state.selected_customer is None:
        st.title("👥 لوحة التحكم العامة")
        
        with st.expander("➕ إضافة عميل جديد"):
            new_cust_name = st.text_input("اسم العميل")
            new_cust_phone = st.text_input("رقم الهاتف (اختياري)")
            if st.button("إضافة العميل"):
                if new_cust_name and new_cust_name not in st.session_state.customers:
                    st.session_state.customers[new_cust_name] = {"phone": new_cust_phone, "records": []}
                    st.success(f"تم إضافة {new_cust_name} بنجاح!")
                    st.rerun()
                else:
                    st.warning("الاسم موجود مسبقاً أو فارغ!")

        st.markdown("### سجلات العملاء")
        if not st.session_state.customers:
            st.info("لا يوجد عملاء مضافين حالياً.")
        else:
            for cust, data in st.session_state.customers.items():
                records = data["records"]
                total_debt = sum(r['amount'] for r in records if r['type'] == 'دين')
                total_paid = sum(r['amount'] for r in records if r['type'] == 'تسديد')
                remaining = total_debt - total_paid

                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                col1.markdown(f"**👤 {cust}**")
                col2.markdown(f"إجمالي الديون: `{total_debt}`")
                col3.markdown(f"المتبقي: **`{remaining}`**")
                
                if col4.button("عرض الحساب", key=f"btn_{cust}"):
                    st.session_state.selected_customer = cust
                    st.rerun()
                st.markdown("---")

    else:
        cust = st.session_state.selected_customer
        if st.button("⬅️ العودة إلى القائمة"):
            st.session_state.selected_customer = None
            st.rerun()

        st.title(f"📁 حساب العميل: {cust}")

        records = st.session_state.customers[cust]["records"]
        currencies = ["ريال يمني", "ريال سعودي", "دولار أمريكي"]

        total_debt = sum(r['amount'] for r in records if r['type'] == 'دين')
        total_paid = sum(r['amount'] for r in records if r['type'] == 'تسديد')
        remaining = total_debt - total_paid

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.markdown(f"<div class='metric-card'><h5>إجمالي الديون</h5><h3>{total_debt}</h3></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='metric-card'><h5>إجمالي المدفوعات</h5><h3>{total_paid}</h3></div>", unsafe_allow_html=True)
        col_m3.markdown(f"<div class='metric-card'><h5>الرصيد المتبقي</h5><h3>{remaining}</h3></div>", unsafe_allow_html=True)

        st.markdown("---")
        col_add1, col_add2 = st.columns(2)

        with col_add1:
            with st.form(key="add_debt_form"):
                st.subheader("➕ إضافة دين جديد")
                d_amount = st.number_input("المبلغ", min_value=0.0, step=10.0, key="d_amt")
                d_currency = st.selectbox("العملة", currencies, key="d_curr")
                d_note = st.text_input("ملاحظات (اختياري)", key="d_note")
                submit_debt = st.form_submit_button("إضافة الدين")
                if submit_debt:
                    records.append({"type": "دين", "amount": d_amount, "currency": d_currency, "note": d_note})
                    st.success("تمت الإضافة بنجاح!")
                    st.rerun()

        with col_add2:
            with st.form(key="add_pay_form"):
                st.subheader("💵 تسجيل تسديد دفعة")
                p_amount = st.number_input("المبلغ المسدد", min_value=0.0, step=10.0, key="p_amt")
                p_currency = st.selectbox("العملة", currencies, key="p_curr")
                p_note = st.text_input("ملاحظات (اختياري)", key="p_note")
                submit_pay = st.form_submit_button("تسديد")
                if submit_pay:
                    records.append({"type": "تسديد", "amount": p_amount, "currency": p_currency, "note": p_note})
                    st.success("تم التسجيل بنجاح!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 سجل العمليات")

        if not records:
            st.info("لا توجد عمليات مسجلة لهذا العميل حتى الآن.")
        else:
            for idx, rec in enumerate(reversed(records)):
                actual_idx = len(records) - 1 - idx
                type_color = "#10b981" if rec['type'] == 'تسديد' else "#ef4444"
                
                rec_html = f"""
                <div class='record-card'>
                    <div>
                        <span style='color: {type_color}; font-weight: bold;'>{rec['type']}</span>
                        <div style='font-size: 18px; font-weight: bold;'>{rec['amount']} {rec['currency']}</div>
                        <div style='color: #6b7280; font-size: 14px;'>{rec['note']}</div>
                    </div>
                </div>
                """
                st.markdown(rec_html, unsafe_allow_html=True)
                
                if st.button("حذف", key=f"del_{actual_idx}"):
                    records.pop(actual_idx)
                    st.rerun()

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
