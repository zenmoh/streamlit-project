import streamlit as st
import pandas as pd
import plotly.express as px
import io

# إعداد صفحة التطبيق
st.set_page_config(page_title="تحليل Excel المتقدم", layout="wide")

# عرض الشعار والاسم بتصميم جميل
st.markdown("""
    <style>
    @keyframes fadeInRight {
        0% {opacity: 0; transform: translateX(50px);}
        100% {opacity: 1; transform: translateX(0);}
    }
    .header-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 20px;
        background-color: #e6f0fa;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        animation: fadeInRight 1.5s ease-out;
    }
    .header-text {
        color: #4B8BBE;
        font-size: 26px;
        font-weight: bold;
        margin-right: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: right;
    }
    </style>
    <div class="header-container">
        <div class="header-text">
            📊 أداة تحليل وتنظيف ملفات Excel / CSV<br>إعداد: Zen Mohammedad
        </div>
    </div>
""", unsafe_allow_html=True)

@st.cache_data
def load_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file, parse_dates=True)

def clean_data(df, remove_duplicates=True, duplicate_subset=None, drop_empty_rows=True, fillna_method=''):
    original_rows = df.shape[0]
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    if remove_duplicates:
        if duplicate_subset:
            df = df.drop_duplicates(subset=duplicate_subset)
        else:
            df = df.drop_duplicates()

    if drop_empty_rows:
        df.dropna(how='all', inplace=True)

    if fillna_method != '':
        df.fillna(fillna_method, inplace=True)

    removed = original_rows - df.shape[0]
    return df, removed

def analyze_custom_words_with_rows(df, word_dict):
    results = []
    for col, words in word_dict.items():
        if col in df.columns:
            col_lower = df[col].astype(str).str.lower()
            mask = col_lower.str.contains('|'.join(words), case=False, na=False)
            df = df[mask]
    results.append(df)
    return pd.concat(results)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📥 رفع ملف", "🧹 التنظيف", "📈 تحليل رقمي", "📝 تحليل كلمات", "📊 رسم بياني", "🔍 فلترة السير الذاتية"
])

with tab1:
    file = st.file_uploader("ارفع ملف Excel أو CSV للسير الذاتية", type=["xlsx", "csv"])
    if file:
        df = load_file(file)
        st.session_state["df"] = df
        st.success("✅ تم تحميل الملف بنجاح")
        if df.shape[0] > 100000:
            st.warning("⚠️ الملف يحتوي على أكثر من 100 ألف صف، قد يؤثر ذلك على الأداء.")

if "df" in st.session_state:
    df = st.session_state["df"]

    with tab2:
        st.subheader("🧹 إعدادات التنظيف")

        remove_duplicates = st.checkbox("حذف الصفوف المكررة", value=True)
        duplicate_subset = None
        if remove_duplicates:
            duplicate_subset = st.multiselect("حدد الأعمدة التي تريد اعتبارها لتحديد التكرارات:", df.columns.tolist())

        drop_empty_rows = st.checkbox("حذف الصفوف الفارغة تمامًا", value=True)
        fillna_option = st.selectbox("كيف تملأ القيم المفقودة؟", ["", "قيمة فارغة ''", "0", "N/A"])
        fillna_value = ''
        if fillna_option == "0":
            fillna_value = 0
        elif fillna_option == "N/A":
            fillna_value = "N/A"

        if st.button("🚀 ابدأ التنظيف"):
            df_clean, removed = clean_data(df.copy(), remove_duplicates, duplicate_subset, drop_empty_rows, fillna_value)
            st.session_state["df_clean"] = df_clean
            st.subheader("✅ البيانات بعد التنظيف")
            st.dataframe(df_clean.head(100), use_container_width=True)

            if st.checkbox("عرض كل البيانات بعد التنظيف (قد يكون بطيئًا)"):
                st.dataframe(df_clean, use_container_width=True)

            if remove_duplicates:
                if duplicate_subset:
                    subset_info = f"حسب الأعمدة: {', '.join(duplicate_subset)}"
                else:
                    subset_info = "حسب كل الأعمدة"
                st.info(f"🗑️ تم حذف {removed} صف مكرر ({subset_info}).")
            else:
                st.info("🔄 لم يتم حذف صفوف مكررة.")

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_clean.to_excel(writer, index=False, sheet_name='بيانات_منظفة')
            st.download_button(
                label="⬇️ تحميل البيانات بعد التنظيف",
                data=buffer.getvalue(),
                file_name="بيانات_منظفة.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with tab3:
        st.subheader("📐 إحصائيات الأعمدة الرقمية")
        df_clean = st.session_state.get("df_clean", df)
        numeric_cols = df_clean.select_dtypes(include='number')
        if not numeric_cols.empty:
            st.dataframe(numeric_cols.describe().transpose(), use_container_width=True)
        else:
            st.info("لا توجد أعمدة رقمية في البيانات.")

    with tab4:
        st.subheader("🔍 تحليل كلمات مخصصة مع الصفوف")
        df_clean = st.session_state.get("df_clean", df)
        word_dict = {}
        columns_to_search = st.multiselect("اختر الأعمدة التي تريد البحث فيها:", df_clean.columns.tolist())

        for col in columns_to_search:
            words = st.text_area(f"أدخل الكلمات المراد البحث عنها في عمود {col} (مفصولة بفاصلة):", height=100)
            word_dict[col] = [w.strip() for w in words.split(',') if w.strip()]

        if st.button("🔎 تحليل الكلمات في الأعمدة"):
            result = analyze_custom_words_with_rows(df_clean, word_dict)
            if not result.empty:
                st.subheader("الصفوف التي تحتوي على الكلمات المدخلة:")
                st.dataframe(result.head(100), use_container_width=True)

                if st.checkbox("عرض كل النتائج (قد يكون بطيئًا)"):
                    st.dataframe(result, use_container_width=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    result.to_excel(writer, index=False, sheet_name='تحليل_كلمات')
                st.download_button(
                    label="⬇️ تحميل نتائج الكلمات",
                    data=buffer.getvalue(),
                    file_name="تحليل_كلمات.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("❗ لم يتم العثور على أي من الكلمات المحددة.")

    with tab5:
        st.subheader("📊 الرسم البياني التفاعلي")
        df_clean = st.session_state.get("df_clean", df)
        col = st.selectbox("اختر عمودًا للرسم:", df_clean.columns)
        if col:
            if df_clean[col].dtype == 'object':
                value_counts_df = df_clean[col].value_counts().head(20).reset_index()
                value_counts_df.columns = [col, 'count']
                fig = px.bar(value_counts_df, x=col, y='count', labels={col: col, 'count': 'العدد'}, title=f"🔢 تكرار القيم في العمود: {col}")
            else:
                fig = px.histogram(df_clean, x=col, title=f"Histogram للعمود: {col}")
            st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.subheader("🔍 فلترة السير الذاتية")
        dropdown_filters = {
            "الجنس": "اختر الجنس",
            "محافظة الإقامة الحالية": "اختر المحافظة",
            "مهارات الحاسوب [Excel]": "اختر مستوى إكسل",
            "سنوات خبرة العمل الإجمالية": "اختر سنوات الخبرة",
            "المستوى التعليمي": "اختر المستوى التعليمي",
            "هل سبق لك إدارة فريق؟": "اختر نعم/لا",
            "إذاكان الإجابة على السؤال السابق نعم، كم عدد الموظفين الذين تديرهم؟": "عدد الموظفين"
        }

        filtered_df = df.copy()

        for column, placeholder in dropdown_filters.items():
            if column in df.columns:
                options = df[column].dropna().unique().tolist()
                selected_options = st.multiselect(f"{column}:", [""] + sorted(options), key=column)
                if selected_options and "" not in selected_options:
                    filtered_df = filtered_df[filtered_df[column].isin(selected_options)]

        # فلترة الاختصاص التعليمي ككلمات مفتاحية (وليس قائمة منسدلة)
        if "اختصاص التعليمي" in df.columns:
            edu_keywords = st.text_input("🔎 أدخل كلمات مفتاحية لـ: اختصاص التعليمي (مفصولة بفاصلة)")
            if edu_keywords:
                # تقسيم الكلمات المدخلة بناءً على الفاصلة
                keyword_list = [keyword.strip() for keyword in edu_keywords.split(",")]

                # فلترة البيانات بناءً على أي كلمة من الكلمات المدخلة
                filtered_df = filtered_df[
                    filtered_df["اختصاص التعليمي"].astype(str).apply(
                        lambda x: any(keyword.lower() in x.lower() for keyword in keyword_list)
                    )
                ]

        st.markdown("### 📋 النتائج بعد الفلترة")
        st.write(filtered_df)

        def convert_df_to_excel(df):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtered')
            return buffer.getvalue()

        if not filtered_df.empty:
            st.download_button(
                label="📥 تحميل النتائج كملف Excel",
                data=convert_df_to_excel(filtered_df),
                file_name='filtered_cv_data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.info("لم يتم العثور على نتائج مطابقة للفلاتر المحددة.")
