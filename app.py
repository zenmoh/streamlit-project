import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="تحليل Excel المتقدم", layout="wide")

def clean_data(df):
    original_rows = df.shape[0]
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df_cleaned = df.drop_duplicates()
    duplicates_removed = original_rows - df_cleaned.shape[0]
    df_cleaned.dropna(how='all', inplace=True)
    df_cleaned.fillna('', inplace=True)
    return df_cleaned, duplicates_removed

def analyze_custom_words_with_rows(df, words):
    results = []
    word_list = [w.strip() for w in words if w.strip()]
    text_cols = df.select_dtypes(include='object').columns
    for word in word_list:
        for col in text_cols:
            col_lower = df[col].astype(str).str.lower()
            mask = col_lower.str.contains(word.lower())
            matched_rows = df[mask]
            for idx, row in matched_rows.iterrows():
                results.append({
                    'الكلمة': word,
                    'العمود': col,
                    'رقم الصف': idx,
                    'محتوى الصف': row.to_dict()
                })
    return pd.DataFrame(results)

def analyze_numeric(df):
    rows = []
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        col_data = df[col]
        rows.append({
            'العمود': col,
            'عدد القيم': col_data.count(),
            'المتوسط': col_data.mean(),
            'الحد الأدنى': col_data.min(),
            'الحد الأقصى': col_data.max(),
            'الانحراف المعياري': col_data.std()
        })
    return pd.DataFrame(rows)

st.title("📊 أداة تحليل وتنظيف ملفات Excel / CSV")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 رفع الملف", "🧹 التنظيف", "📈 تحليل رقمي", "📝 تحليل كلمات", "📊 رسم بياني"
])

with tab1:
    file = st.file_uploader("ارفع ملف Excel أو CSV", type=["xlsx", "csv"])
    if file:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file, parse_dates=True)
        st.session_state["df"] = df
        st.success("✅ تم تحميل الملف بنجاح")

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

    with tab3:
        st.subheader("📐 تحليل الأعمدة الرقمية")
        st.dataframe(analyze_numeric(st.session_state["df_clean"]), use_container_width=True)

    with tab4:
        st.subheader("🔍 تحليل كلمات مخصصة مع الصفوف")
        custom_words = st.text_area("أدخل الكلمات المطلوب تحليلها (سطر لكل كلمة أو مفصولة بفاصلة):", height=150)
        if st.button("🔎 تحليل الكلمات في الأعمدة"):
            word_list = [w for line in custom_words.splitlines() for w in line.split(',')]
            result = analyze_custom_words_with_rows(st.session_state["df_clean"], word_list)

            if not result.empty:
                expanded_rows = []
                for _, row in result.iterrows():
                    base = {
                        'الكلمة': row['الكلمة'],
                        'العمود': row['العمود'],
                        'رقم الصف': row['رقم الصف']
                    }
                    base.update(row['محتوى الصف'])
                    expanded_rows.append(base)

                result_expanded = pd.DataFrame(expanded_rows)
                st.dataframe(result_expanded, use_container_width=True)
            else:
                st.warning("❗ لم يتم العثور على أي من الكلمات المحددة.")

    with tab5:
        df_clean = st.session_state["df_clean"]
        st.subheader("📊 الرسم البياني التفاعلي")
        col = st.selectbox("اختر عمودًا للرسم:", df_clean.columns)
        if col:
            if df_clean[col].dtype == 'object':
                fig = px.bar(df_clean[col].value_counts().head(20), title=f"تكرار القيم في العمود: {col}")
            else:
                fig = px.histogram(df_clean, x=col, title=f"Histogram للعمود: {col}")
            st.plotly_chart(fig, use_container_width=True)
