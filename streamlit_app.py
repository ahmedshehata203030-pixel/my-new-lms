import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import time

# --- 1. إعدادات الروابط (ضع روابط شيتاتك هنا) ---
GRADE_SHEETS = {
    "الصف الاول الاعدادى": "https://docs.google.com/spreadsheets/d/11sa1GDAYCez4b17aI1hDPKJDtfj953ySj8OMYOxbzTI/edit?usp=sharing",
    "الصف الثانى الاعدادى": "https://docs.google.com/spreadsheets/d/1PInF4O2hFmc7kY430bL_n4KliezblGyk3peBMN4VJ9U/edit?usp=sharing",
    "الصف الثالث الاعدادى": "https://docs.google.com/spreadsheets/d/1btzo6mPj0GtCdHgvz5tTTKUe_3kgPit3YitobAj01Lc/edit?usp=sharing"
}

# --- 2. دوال مساعدة ---
def fetch_sheet(url, sheet_name):
    csv_url = url.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={sheet_name}")
    return pd.read_csv(csv_url, dtype=str)

def verify_student(name, password):
    for grade_name, sheet_url in GRADE_SHEETS.items():
        try:
            df = fetch_sheet(sheet_url, "whitelist")
            df.columns = [str(c).strip().lower() for c in df.columns]
            for _, row in df.iterrows():
                # تأكد أن أسماء الأعمدة في الشيت هي name و password
                if str(row.get('name', '')).strip() == name.strip() and \
                   str(row.get('password', '')).strip() == password.strip():
                    return "granted", grade_name, sheet_url
        except: continue
    return "denied", None, None

# --- 3. واجهة البرنامج ---
st.set_page_config(page_title="منصة المعمل التعليمية", layout="wide")

if "access_granted" not in st.session_state: st.session_state.access_granted = False

if not st.session_state.access_granted:
    st.title("🎓 بوابة الطالب التعليمية")
    with st.form("login_form"):
        name = st.text_input("✍️ اسم الطالب:")
        pw = st.text_input("🔑 الرقم السري:", type="password")
        if st.form_submit_button("دخول"):
            status, grade, url = verify_student(name, pw)
            if status == "granted":
                st.session_state.update({"access_granted": True, "grade": grade, "url": url, "name": name})
                st.rerun()
            else: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# --- 4. عرض المحتوى (بعد الدخول) ---
url = st.session_state.url
lessons_df = fetch_sheet(url, "lessons")
quizzes_df = fetch_sheet(url, "quizzes")

st.sidebar.success(f"مرحباً {st.session_state.name} | {st.session_state.grade}")
if st.sidebar.button("🔒 تسجيل الخروج"):
    st.session_state.access_granted = False
    st.rerun()

tab1, tab2 = st.tabs(["📺 الشرح", "📝 الامتحانات"])

with tab1:
    st.subheader("📺 قسم الدروس")
    # هنا ضع المنطق الخاص بعرض الدروس الذي كان في كودك القديم
    # استخدم lessons_df للفلترة والعرض
    st.write("بيانات الدروس محملة وجاهزة للعرض...")

with tab2:
    st.subheader("📝 الاختبارات")
    # هنا ضع المنطق الخاص بعرض الامتحانات الذي كان في كودك القديم
    # استخدم quizzes_df للفلترة والعرض
    st.write("بيانات الامتحانات محملة وجاهزة للعرض...")
