import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import re
import time

# --- 1. الروابط (ضع روابط الشيتات الـ 3 هنا) ---
GRADE_URLS = {
    "الصف الاول الاعدادى": "رابط_شيت_اولى_اعدادي",
    "الصف الثانى الاعدادى": "رابط_شيت_ثانية_اعدادي",
    "الصف الثالث الاعدادى": "رابط_شيت_ثالثة_اعدادي"
}

# --- 2. الإخفاء والستايل الاحترافي ---
st.markdown("""
    <style>
    [data-testid="stHeaderActionElements"], header[data-testid="stHeader"], .stAppDeployButton, #MainMenu, footer { display: none !important; }
    div.stButton > button { width: 100% !important; height: 70px !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. اختيار الصف (Router) ---
if "SHEET_URL" not in st.session_state:
    st.set_page_config(page_title="منصة المعمل", layout="wide")
    st.title("🎓 بوابة الطالب التعليمية")
    chosen_grade = st.selectbox("يرجى اختيار الصف الدراسي:", list(GRADE_URLS.keys()))
    if st.button("تأكيد الصف"):
        st.session_state.SHEET_URL = GRADE_URLS[chosen_grade]
        st.session_state.grade_name = chosen_grade
        st.rerun()
    st.stop()

# --- 4. المتغيرات والدوال ---
SHEET_URL = st.session_state.SHEET_URL
LESSONS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=lessons&v={int(time.time())}")
QUIZZES_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=quizzes&v={int(time.time())}")
ANSWERS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=student_results&v={int(time.time())}")
WHITELIST_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=whitelist&v={int(time.time())}")
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxIpDlNRgzsf_SamtDEzJfggmSBK6y7UhmShuyhNIKK89R4EH_8O2tjGYYrYuSNkLGr/exec"

def clean_date_string(date_str):
    if not date_str or pd.isna(date_str) or str(date_str).lower() == 'nan': return None
    s = str(date_str).strip().replace('/', '-')
    is_pm, is_am = 'م' in s, 'ص' in s
    s = s.replace('م', '').replace('ص', '').strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(s, fmt)
            if is_pm and dt.hour < 12: dt = dt.replace(hour=dt.hour + 12)
            elif is_am and dt.hour == 12: dt = dt.replace(hour=0)
            return dt
        except: pass
    return None

def force_string(val): return "" if pd.isna(val) or str(val).lower() == 'nan' else str(val).strip()

def verify_student_credentials(student_name, password):
    try:
        df = pd.read_csv(WHITELIST_CSV, dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        for _, row in df.iterrows():
            if "".join(force_string(row.get('name', '')).split()).lower() == "".join(student_name.split()).lower() and force_string(row.get('password', '')) == str(password).strip():
                return "granted", "تم الدخول"
        return "denied", "خطأ في الاسم أو الباسورد"
    except: return "error", "تعذر الاتصال بالشيت"

def load_data():
    courses, quizzes = {}, {}
    # تحميل الدروس
    try:
        df = pd.read_csv(LESSONS_CSV, dtype=str)
        for _, row in df.iterrows():
            c = force_string(row.get('course', ''))
            if c:
                if c not in courses: courses[c] = []
                courses[c].append({"title": force_string(row.get('lesson', '')), "video": force_string(row.get('video', '')), "pdf": force_string(row.get('pdf', ''))})
    except: pass
    # تحميل الاختبارات
    try:
        df = pd.read_csv(QUIZZES_CSV, dtype=str)
        for _, row in df.iterrows():
            qt = force_string(row.get('quiz', ''))
            if qt:
                if qt not in quizzes: quizzes[qt] = []
                quizzes[qt].append({"question": force_string(row.get('question', '')), "options": [force_string(row.get('a','')), force_string(row.get('b','')), force_string(row.get('c','')), force_string(row.get('d',''))], "correct": force_string(row.get('correct', '')), "degree": float(row.get('degree', 1)), "start_at": row.get('startat'), "end_at": row.get('endat')})
    except: pass
    return courses, quizzes

# --- 5. المنطق الرئيسي ---
if "access_granted" not in st.session_state: st.session_state.access_granted = False

if not st.session_state.access_granted:
    st.subheader(f"تسجيل دخول: {st.session_state.grade_name}")
    with st.form("login"):
        name = st.text_input("الاسم:")
        pw = st.text_input("الباسورد:", type="password")
        if st.form_submit_button("دخول"):
            status, msg = verify_student_credentials(name, pw)
            if status == "granted":
                st.session_state.update({"access_granted": True, "student_name": name})
                st.rerun()
            else: st.error(msg)
    st.stop()

st.sidebar.success(f"مرحباً {st.session_state.student_name}")
if st.sidebar.button("🔄 تغيير الصف"):
    del st.session_state.SHEET_URL
    st.rerun()

# هنا عرض المحتوى (الشرح والامتحانات كما كنت تستخدمه)
courses_db, quizzes_db = load_data()
st.header(f"أهلاً بك في {st.session_state.grade_name}")
# أكمل كود العرض الخاص بك هنا...
