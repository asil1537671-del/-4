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
        st.title("👥 إجمالي العملاء واللوحة العامة")
        
        # حساب الإجماليات العامة للكل
        total_all_debts = 0
        total_all_paids = 0
        for c_data in st.session_state.customers.values():
            for r in c_data["records"]:
                if r['type'] == 'دين':
                    total_all_debts += r['amount']
                else:
                    total_all_paids += r['amount']
        
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.markdown(f"<div class='metric-card'><h5>إجمالي المدينين</h5><h3>{total_all_debts}</h3></div>", unsafe_allow_html=True)
        col_g2.markdown(f"<div class='metric-card'><h5>إجمالي المسددين</h5><h3>{total_all_paids}</h3></div>", unsafe_allow_html=True)
        col_g3.markdown(f"<div class='metric-card'><h5>عدد العملاء</h5><h3>{len(st.session_state.customers)}</h3></div>", unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("➕ إضافة عميل جديد"):
            new_cust_name = st.text_input("اسم العميل الجديد")
            if st.button("حفظ العميل"):
                if new_cust_name and new_cust_name not in st.session_state.customers:
                    st.session_state.customers[new_cust_name] = {"records": []}
                    st.success(f"تم إضافة العميل {new_cust_name} بنجاح!")
                    st.rerun()
                else:
                    st.warning("الاسم موجود مسبقاً أو فارغ!")

        st.markdown("### قائمة العملاء")
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
                col2.markdown(f"إجمالي الدين: `{total_debt}`")
                col3.markdown(f"المتبقي: **`{remaining}`**")
                
                if col4.button("عرض السجل", key=f"btn_{cust}"):
                    st.session_state.selected_customer = cust
                    st.rerun()
                st.markdown("---")

    else:
        cust = st.session_state.selected_customer
        if st.button("⬅️ العودة إلى قائمة العملاء"):
            st.session_state.selected_customer = None
            st.rerun()

        st.title(f"📁 سجل ديون العميل: {cust}")

        records = st.session_state.customers[cust]["records"]
        currencies = ["ريال يمني", "ريال سعودي", "دولار أمريكي"]

        total_debt = sum(r['amount'] for r in records if r['type'] == 'دين')
        total_paid = sum(r['amount'] for r in records if r['type'] == 'تسديد')
        remaining = total_debt - total_paid

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.markdown(f"<div class='metric-card'><h5>إجمالي الدين</h5><h3>{total_debt}</h3></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='metric-card'><h5>إجمالي التسديد</h5><h3>{total_paid}</h3></div>", unsafe_allow_html=True)
        col_m3.markdown(f"<div class='metric-card'><h5>المتبقي عليه</h5><h3>{remaining}</h3></div>", unsafe_allow_html=True)

        st.markdown("---")
        col_add1, col_add2 = st.columns(2)

        with col_add1:
            with st.form(key="add_debt_form"):
                st.subheader("➕ أضف دين جديد")
                d_amount = st.number_input("المبلغ", min_value=0.0, step=10.0, key="d_amt")
                d_currency = st.selectbox("تحديد العملة", currencies, key="d_curr")
                d_note = st.text_input("ملاحظة / البيان", key="d_note")
                submit_debt = st.form_submit_button("حفظ الدين")
                if submit_debt:
                    records.append({"type": "دين", "amount": d_amount, "currency": d_currency, "note": d_note})
                    st.success("تم إضافة الدين بنجاح")
                    st.rerun()

        with col_add2:
            with st.form(key="add_pay_form"):
                st.subheader("💵 تسجيل تسديد")
                p_amount = st.number_input("مبلغ التسديد", min_value=0.0, step=10.0, key="p_amt")
                p_currency = st.selectbox("تحديد العملة", currencies, key="p_curr")
                p_note = st.text_input("ملاحظة التسديد", key="p_note")
                submit_pay = st.form_submit_button("حفظ التسديد")
                if submit_pay:
                    records.append({"type": "تسديد", "amount": p_amount, "currency": p_currency, "note": p_note})
                    st.success("تم تسجيل التسديد بنجاح")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 السجلات الكاملة (تعديل وحذف)")

        if not records:
            st.info("لا توجد سجلات مسجلة لهذا العميل بعد")
        else:
            for idx, rec in enumerate(reversed(records)):
                actual_idx = len(records) - 1 - idx
                type_color = "#10b981" if rec['type'] == 'تسديد' else "#ef4444"
                
                st.markdown(f"""
                <div class='record-card'>
                    <span style='color: {type_color}; font-weight: bold;'>{rec['type']}</span> | 
                    <b>المبلغ:</b> {rec['amount']} {rec.get('currency', 'ريال يمني')} | 
                    <b>ملاحظة:</b> {rec['note']}
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار التعديل والحذف لكل عملية
                c_edit, c_del, _ = st.columns([1, 1, 4])
                with c_edit:
                    if st.button("تعديل", key=f"edit_{actual_idx}"):
                        st.session_state[f"editing_{actual_idx}"] = True
                with c_del:
                    if st.button("حذف", key=f"del_{actual_idx}"):
                        records.pop(actual_idx)
                        st.rerun()

                # نافذة التعديل إذا تم النقر على زر تعديل
                if st.session_state.get(f"editing_{actual_idx}", False):
                    with st.form(key=f"edit_form_{actual_idx}"):
                        st.write(f"تعديل السجل رقم {actual_idx + 1}")
                        new_amt = st.number_input("المبلغ الجديد", value=float(rec['amount']), key=f"e_amt_{actual_idx}")
                        new_curr = st.selectbox("العملة الجديدة", currencies, index=currencies.index(rec.get('currency', 'ريال يمني')) if rec.get('currency', 'ريال يمني') in currencies else 0, key=f"e_curr_{actual_idx}")
                        new_note = st.text_input("الملاحظة الجديدة", value=rec['note'], key=f"e_note_{actual_idx}")
                        
                        if st.form_submit_button("حفظ التعديلات"):
                            records[actual_idx]['amount'] = new_amt
                            records[actual_idx]['currency'] = new_curr
                            records[actual_idx]['note'] = new_note
                            st.session_state[f"editing_{actual_idx}"] = False
                            st.success("تم التعديل بنجاح!")
                            st.rerun()

        st.markdown("---")
        if st.button("🗑️ حذف العميل وسجلاته بالكامل", type="primary"):
            del st.session_state.customers[cust]
            st.session_state.selected_customer = None
            st.success("تم حذف العميل بنجاح")
            st.rerun()

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
