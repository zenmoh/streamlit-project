import streamlit as st
import pandas as pd
import plotly.express as px
import io

# إعداد صفحة التطبيق
st.set_page_config(page_title="تحليل Excel المتقدم", layout="wide")

# عنوان رئيسي مع اسمك
st.markdown(
    "<h1 style='text-align: right; color: #4B8BBE;'>📊 أداة تحليل وتنظيف ملفات Excel / CSV - إعداد: zen mohammdad</h1>",
    unsafe_allow_html=True)


# دالة لتنظيف البيانات
def clean_data(df):
    original_rows = df.shape[0]
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df_cleaned = df.drop_duplicates()
    duplicates_removed = original_rows - df_cleaned.shape[0]
    df_cleaned.dropna(how='all', inplace=True)
    df_cleaned.fillna('', inplace=True)
    return df_cleaned, duplicates_removed


# دالة لتحليل الكلمات مع تطابق كل الشروط في نفس الصف
def analyze_custom_words_with_rows(df, word_dict):
    # أنشئ قائمة لتخزين الصفوف المطابقة
    results = []

    # لكل عمود والكلمات المدخلة الخاصة به
    for col, words in word_dict.items():
        if col in df.columns:
            col_lower = df[col].astype(str).str.lower()
            # ابتكار ماسك (فلتر) لكل الكلمات التي تم البحث عنها
            mask = col_lower.str.contains('|'.join(words), case=False, na=False)
            df = df[mask]  # ترشيح البيانات تبعاً للعمود المحدد

    # إضافة الصفوف التي تتطابق مع جميع الشروط
    results.append(df)

    # دمج الصفوف المطابقة في نتيجة واحدة
    return pd.concat(results)


# علامات التبويب
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 رفع الملف", "🧹 التنظيف", "📈 تحليل رقمي", "📝 تحليل كلمات", "📊 رسم بياني"
])

# تبويب رفع الملف
with tab1:
    file = st.file_uploader("ارفع ملف Excel أو CSV", type=["xlsx", "csv"])
    if file:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file, parse_dates=True)
        st.session_state["df"] = df
        st.success("✅ تم تحميل الملف بنجاح")

# باقي التبويبات
if "df" in st.session_state:
    df = st.session_state["df"]

    with tab2:
        st.subheader("🧹 البيانات الأصلية")
        st.dataframe(df, use_container_width=True)

        df_clean, removed = clean_data(df.copy())
        st.session_state["df_clean"] = df_clean

        st.subheader("✅ البيانات بعد التنظيف")
        st.dataframe(df_clean, use_container_width=True)
        st.info(f"🗑️ تم حذف {removed} صف مكرر.")

        # زر تحميل البيانات بعد التنظيف
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
        # يمكن حذف هذه السطور إذا لم تكن بحاجة لتحليل البيانات الرقمية
        # numeric_df = analyze_numeric(df_clean)
        # st.dataframe(numeric_df, use_container_width=True)

        # buffer = io.BytesIO()
        # with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        #     numeric_df.to_excel(writer, index=False, sheet_name='تحليل_رقمي')
        # st.download_button(
        #     label="⬇️ تحميل نتائج التحليل الرقمي",
        #     data=buffer.getvalue(),
        #     file_name="تحليل_رقمي.xlsx",
        #     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # )

    with tab4:
        st.subheader("🔍 تحليل كلمات مخصصة مع الصفوف")

        # إدخال الكلمات من المستخدم لكل عمود
        word_dict = {}
        columns_to_search = st.multiselect("اختر الأعمدة التي تريد البحث فيها:", df_clean.columns.tolist())

        for col in columns_to_search:
            words = st.text_area(f"أدخل الكلمات المراد البحث عنها في عمود {col} (مفصولة بفاصلة):", height=100)
            word_dict[col] = [w.strip() for w in words.split(',') if w.strip()]

        if st.button("🔎 تحليل الكلمات في الأعمدة"):
            result = analyze_custom_words_with_rows(df_clean, word_dict)

            if not result.empty:
                st.subheader("الصفوف التي تحتوي على الكلمات المدخلة في الأعمدة المحددة:")
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
        col = st.selectbox("اختر عمودًا للرسم:", df_clean.columns)
        if col:
            if df_clean[col].dtype == 'object':
                value_counts_df = df_clean[col].value_counts().head(20).reset_index()
                value_counts_df.columns = [col, 'count']
                fig = px.bar(value_counts_df,
                             x=col, y='count',
                             labels={col: col, 'count': 'العدد'},
                             title=f"🔢 تكرار القيم في العمود: {col}")
            else:
                fig = px.histogram(df_clean, x=col, title=f"Histogram للعمود: {col}")
            st.plotly_chart(fig, use_container_width=True)
