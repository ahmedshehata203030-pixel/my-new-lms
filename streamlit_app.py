import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import re
import time

# --- روابط الـ 3 شيتات (حط روابطك هنا) ---
GRADE_URLS = {
    "الصف الاول الاعدادى": "رابط_شيت_اولى",
    "الصف الثانى الاعدادى": "رابط_شيت_ثانية",
    "الصف الثالث الاعدادى": "رابط_شيت_ثالثة"
}

# --- نظام اختيار الصف (الراوتر) ---
if "SHEET_URL" not in st.session_state:
    st.set_page_config(page_title="منصة المعمل", layout="wide")
    st.markdown("<style>[data-testid='stHeaderActionElements'] { display: none !important; } header { display: none !important; }</style>", unsafe_allow_html=True)
    st.header("🎓 اختر صفك الدراسي")
    chosen_grade = st.selectbox("يرجى تحديد الصف:", list(GRADE_URLS.keys()))
    if st.button("تأكيد الصف"):
        st.session_state.SHEET_URL = GRADE_URLS[chosen_grade]
        st.session_state.grade_name = chosen_grade
        st.rerun()
    st.stop()

# --- المتغيرات المعتمدة على اختيار الطالب ---
SHEET_URL = st.session_state.SHEET_URL
LESSONS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=lessons&v={int(time.time())}")
QUIZZES_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=quizzes&v={int(time.time())}")
ANSWERS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=student_results&v={int(time.time())}")
WHITELIST_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=whitelist&v={int(time.time())}")
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxIpDlNRgzsf_SamtDEzJfggmSBK6y7UhmShuyhNIKK89R4EH_8O2tjGYYrYuSNkLGr/exec"

# --- [هنا ضع كل دوالك الأصلية: clean_date_string, force_string, verify_student_credentials, has_submitted_before, load_data] ---
# (انسخهم من كودك اللي بعتهولي وحطهم هنا بالظبط)

# --- كود الواجهة والـ UI الأصلي ---
st.markdown("""
    <style>
    [data-testid="stHeaderActionElements"] { display: none !important; }
    header[data-testid="stHeader"] button { display: none !important; }
    div.stButton > button { width: 100% !important; height: 110px !important; font-size: 26px !important; }
    </style>
""", unsafe_allow_html=True)

st.header(f"🎓 منصة {st.session_state.grade_name}")

# --- (باقي كودك الأصلي بتاع الـ Login والـ Tabs والـ Radio buttons) ---

# زر تغيير الصف (عشان لو عايز يرجع يختار صف تاني)
if st.sidebar.button("🔄 تغيير الصف"):
    del st.session_state.SHEET_URL
    st.rerun()
