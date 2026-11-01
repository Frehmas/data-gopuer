import streamlit as st

# تعريف فئة الحاوية الذكية (SmartContainer)
class SmartContainer:
    def __init__(self, initial_number=None, max_overflow_ratio=0.12):
        self.numbers = []

        self.max_overflow_ratio = max_overflow_ratio
        if initial_number is not None:
            self.numbers.append(initial_number)

    @property
    def ceiling(self):
        if not self.numbers:
            return 0
        return max(self.numbers)

    @property
    def current_sum(self):
        return sum(self.numbers)

    @property
    def limit_sum(self):
        return self.ceiling * len(self.numbers)

    def can_add(self, number) -> bool:

        if not self.numbers:
            return True
        if number < self.ceiling:
            return False

        temp_numbers = self.numbers + [number]
        temp_ceiling = max(temp_numbers)
        temp_limit_sum = temp_ceiling * len(temp_numbers)
        temp_real_sum = sum(temp_numbers)
        max_allowed_limit = temp_real_sum * (1 + self.max_overflow_ratio)

        return temp_limit_sum <= max_allowed_limit

    def add(self, number):
        if self.can_add(number):
            self.numbers.append(number)
            return self

        else:
            new_container = SmartContainer(
                initial_number=number, 
                max_overflow_ratio=self.max_overflow_ratio
            )
            return new_container

# تصميم واجهة المستخدم باستخدام Streamlit
st.set_page_config(page_title="توزيع الحاويات الذكية", layout="wide")

st.title("🧠 نظام توزيع البيانات في الحاويات الذكية")
st.markdown("أدخل مجموعة الأرقام، وحدد نسبة التجاوز المسموح بها، لتقوم الفئة بتوزيعها تلقائياً على الحاويات.")

with st.sidebar:
    st.header("إعدادات التوزيع")

    overflow_input = st.slider("نسبة التجاوز المسموحة (%)", min_value=0, max_value=50, value=12, step=1)
    max_overflow_ratio = overflow_input / 100.0
    
    st.markdown("---")
    st.markdown("**شروط القبول:**")
    st.markdown("1. الرقم الجديد $\\ge$ سقف الحاوية الحالي.")
    st.markdown("2. المجموع السقفي لا يتجاوز المجموع الحقيقي بالإضافة إلى النسبة المحددة.")

# حقل إدخال الأرقام
default_text = "777, 810, 874, 1269, 1371"
user_input = st.text_area("أدخل الأرقام مفصولة بفواصل (`,`) أو مسافات:", value=default_text)

if st.button("🚀 تشغيل التوزيع وعرض النتائج", type="primary"):
    try:

        # معالجة المدخلات وتحويلها إلى قائمة أرقام مرتبة تصاعدياً لضمان التسلسل الصحيح
        raw_numbers = [float(x.strip()) for x in user_input.replace(",", " ").split() if x.strip()]
        
        if not raw_numbers:
            st.warning("الرجاء إدخال أرقام صحيحة.")
        else:
            # ترتيب الأرقام تصاعدياً لضمان عمل منطق السقف بشكل صحيح
            numbers = sorted(raw_numbers)
            
            # تنفيذ عملية التوزيع على الحاويات
            containers = []
            if numbers:
                current_container = SmartContainer(initial_number=numbers[0], max_overflow_ratio=max_overflow_ratio)
                containers.append(current_container)
                

                for num in numbers[1:]:
                    result = current_container.add(num)
                    if result is current_container:
                        pass # تمت الإضافة لنفس الحاوية
                    else:
                        containers.append(result)
                        current_container = result

            # عرض النتائج في الواجهة
            st.success(f"تمت معالجة {len(numbers)} رقماً، وتوزيعها على **{len(containers)}** حاويات ذكية.")
            
            st.markdown("---")
            st.subheader("📦 نتائج التوزيع التفصيلية:")
            
            cols = st.columns(min(len(containers), 3))
            for idx, container in enumerate(containers):


                col_idx = idx % 3
                with cols[col_idx]:
                    st.info(f"**الحاوية رقم {idx + 1}**")
                    st.write(f"• **العناصر:** `{container.numbers}`")
                    st.write(f"• **السقف (أكبر رقم):** `{container.ceiling}`")
                    st.write(f"• **المجموع الحقيقي:** `{container.current_sum}`")
                    st.write(f"• **المجموع السقفي:** `{container.limit_sum}`")
                    
    except ValueError:
        st.error("حدث خطأ في قراءة الأرقام. تأكد من إدخال أرقام صالحة مفصولة بفواصل أو مسافات.")
