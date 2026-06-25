import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import re
import time

# 🔗 رابط الجوجل شيت الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/11sa1GDAYCez4b17aI1hDPKJDtfj953ySj8OMYOxbzTI/edit?usp=sharing"

# كسر كاش السيرفر لضمان قراءة البيانات اللحظية
LESSONS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=lessons&v={int(time.time())}")
QUIZZES_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=quizzes&v={int(time.time())}")
ANSWERS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=student_results&v={int(time.time())}")
WHITELIST_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=whitelist&v={int(time.time())}")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxIpDlNRgzsf_SamtDEzJfggmSBK6y7UhmShuyhNIKK89R4EH_8O2tjGYYrYuSNkLGr/exec"

def clean_date_string(date_str):
    if not date_str or pd.isna(date_str) or str(date_str).lower() == 'nan' or str(date_str).strip() == '': return None
    s = str(date_str).strip().replace('/', '-').replace('م', '').replace('ص', '').strip()
    s = re.sub(r'\s+', ' ', s)
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try: return datetime.strptime(s, fmt)
        except: pass
    return None

def force_string(val):
    return "" if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '' else str(val).strip()

def verify_student_credentials(student_name, password):
    try:
        df = pd.read_csv(WHITELIST_CSV, dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        name_col = next((c for c in df.columns if "name" in c or "اسم" in c), None)
        pass_col = next((c for c in df.columns if "pass" in c or "رقم" in c or "سري" in c), None)
        for _, row in df.iterrows():
            if "".join(force_string(row.get(name_col, '')).split()).lower() == "".join(student_name.split()).lower() and force_string(row.get(pass_col, '')) == str(password).strip():
                return "granted", "تم تسجيل الدخول بنجاح."
        return "denied", "❌ الاسم أو الرقم السري غير صحيح."
    except: return "error", "⚠️ خطأ في الاتصال."

def has_submitted_before(student_name, quiz_title):
    try:
        df = pd.read_csv(ANSWERS_CSV, dtype=str)
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        for _, row in df.iterrows():
            if "".join(force_string(row.get('studentname', '')).split()).lower() == "".join(student_name.split()).lower() and "".join(force_string(row.get('quiztitle', '')).split()).lower() == "".join(quiz_title.split()).lower():
                return True
    except: pass
    return False

def load_data():
    try:
        q_df = pd.read_csv(QUIZZES_CSV, dtype=str)
        raw_q_cols = [str(c).strip() for c in q_df.columns]
        norm_q_cols = [c.lower().replace("_", "").replace(" ", "") for c in raw_q_cols]
        q_title_col = raw_q_cols[norm_q_cols.index(next(c for c in norm_q_cols if "quiz" in c or "امتحان" in c))]
        q_text_col = raw_q_cols[norm_q_cols.index(next(c for c in norm_q_cols if "question" in c or "سؤال" in c))]
        deg_col = next((raw_q_cols[i] for i, c in enumerate(norm_q_cols) if "degree" in c or "درج" in c), None)
        corr_col = next((raw_q_cols[i] for i, c in enumerate(norm_q_cols) if "correct" in c or "إجابة" in c), None)
        
        quizzes = {}
        for _, row in q_df.iterrows():
            q_title = force_string(row.get(q_title_col, ''))
            if not q_title: continue
            if q_title not in quizzes: quizzes[q_title] = []
            
            try: 
                q_deg = float(row.get(deg_col, 1.0))
                if q_deg <= 0: q_deg = 1.0
            except: q_deg = 1.0
            
            quizzes[q_title].append({
                "question": force_string(row.get(q_text_col, '')),
                "options": [force_string(row.get(c, '')) for c in raw_q_cols if re.match(r'opt[a-d]', c.lower().replace("_", ""))],
                "correct": force_string(row.get(corr_col, '')).upper(),
                "degree": q_deg,
                "start": row.get('startat'), "end": row.get('endat')
            })
        return quizzes
    except: return {}

st.set_page_config(page_title="منصتي التعليمية", layout="wide")
st.markdown("<style>[data-testid='stHeader']{display:none} .stButton>button{width:100%; height:80px; font-size:20px; font-weight:bold;}</style>", unsafe_allow_html=True)

if "access_granted" not in st.session_state: st.session_state.access_granted = False

if not st.session_state.access_granted:
    with st.form("login"):
        name = st.text_input("اسم الطالب:")
        pw = st.text_input("الرقم السري:", type="password")
        if st.form_submit_button("دخول"):
            status, msg = verify_student_credentials(name, pw)
            if status == "granted":
                st.session_state.update({"access_granted": True, "student_name": name})
                st.rerun()
            else: st.error(msg)
    st.stop()

quizzes = load_data()
st.sidebar.success(f"مرحباً {st.session_state.student_name}")
if st.sidebar.button("خروج"): st.session_state.access_granted = False; st.rerun()

st.header("📝 قسم الامتحانات")
chosen_quiz = st.selectbox("اختر الامتحان:", list(quizzes.keys()))

if has_submitted_before(st.session_state.student_name, chosen_quiz):
    st.error("لقد أديت هذا الاختبار مسبقاً!")
else:
    with st.form("quiz_form"):
        ans = {}
        for i, q in enumerate(quizzes[chosen_quiz]):
            st.markdown(f"**{i+1}: {q['question']}** *[الدرجة: {int(q['degree']) if q['degree'].is_integer() else q['degree']}]*")
            ans[i] = st.radio(f"سؤال {i+1}", q['options'], key=f"q{i}", index=None, horizontal=True)
            st.markdown("---")
        
        if st.form_submit_button("إرسال الإجابات"):
            if None in ans.values(): st.warning("يجب الإجابة على كل الأسئلة!")
            else:
                total_earned = 0.0
                total_deg = 0.0
                for i, q in enumerate(quizzes[chosen_quiz]):
                    total_deg += q['degree']
                    if ans[i] == q['correct']: total_earned += q['degree']
                
                final_score = int(total_earned) if total_earned.is_integer() else total_earned
                requests.post(WEB_APP_URL, json={
                    "action": "submit_quiz", "student_name": st.session_state.student_name, 
                    "quiz_title": chosen_quiz, "score": final_score
                })
                st.success(f"تم الإرسال! درجتك: {final_score} من {int(total_deg)}")
                st.balloons()
