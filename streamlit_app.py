import streamlit as st
import pandas as pd
import requests
import re
import time
from datetime import datetime
import pytz

# --- 1. الإعدادات الأساسية (يجب أن تكون أول أمر Streamlit) ---
st.set_page_config(page_title="بوابة الطالب التعليمية", layout="wide")

IMAGE_URL = "IMAGE_URL = "https://raw.githubusercontent.com/ahmedshehata203030-pixel/ahm/main/uu.png"

# --- 2. الستايل والإخفاء وتنسيق الأزرار ---
st.markdown(f"""
    <style>
    /* الإخفاء العام للعناصر الافتراضية */
    [data-testid="stHeaderActionElements"], header, .stAppDeployButton, #MainMenu, footer, 
    a[href*="github.com"], button[title="View source"], [class*="viewerBadge"], [data-testid="stActionButton"] {{
        display: none !important; visibility: hidden !important;
    }}
    
    /* خلفية التطبيق */
    [data-testid="stAppViewContainer"] {{
        background-image: url("{IMAGE_URL}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.7); z-index: 0;
    }}

    /* التنسيق الموحد لأزرار التنقل الرئيسية */
    div[data-testid="stHorizontalBlock"] {{
        display: flex !important; justify-content: center !important; gap: 25px !important;
    }}
    div.stButton > button {{ 
        width: 100% !important; 
        height: 110px !important; 
        font-size: 26px !important; 
        font-weight: bold !important; 
        color: black !important; 
        background-color: #d1d5db !important; 
        border: 2px solid #000000 !important; 
        border-radius: 15px !important; 
    }}

    /* ألوان خاصة ومميزة لكل من زر الشرح وزر الامتحان لسهولة التنقل */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) div.stButton > button {{ background-color: #a3bffa !important; }}
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) div.stButton > button {{ background-color: #a7f3d0 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. الروابط وقواعد البيانات ---
GRADE_URLS = {
    "الصف الاول الاعدادى": "https://docs.google.com/spreadsheets/d/11sa1GDAYCez4b17aI1hDPKJDtfj953ySj8OMYOxbzTI/edit?usp=sharing",
    "الصف الثانى الاعدادى": "https://docs.google.com/spreadsheets/d/1PInF4O2hFmc7kY430bL_n4KliezblGyk3peBMN4VJ9U/edit?usp=sharing",
    "الصف الثالث الاعدادى": "https://docs.google.com/spreadsheets/d/1btzo6mPj0GtCdHgvz5tTTKUe_3kgPit3YitobAj01Lc/edit?usp=sharing"
}

WEB_APP_URLS = {
    "الصف الاول الاعدادى": "https://script.google.com/macros/s/AKfycbxIpDlNRgzsf_SamtDEzJfggmSBK6y7UhmShuyhNIKK89R4EH_8O2tjGYYrYuSNkLGr/exec",
    "الصف الثانى الاعدادى": "https://script.google.com/macros/s/AKfycbxZQht0d_wlKmdHTjVSx0H5elEmeMYHcfEPzfSsrcuk7h8V9z3ZsZcQ-_g40oIVABdA/exec",
    "الصف الثالث الاعدادى": "https://script.google.com/macros/s/AKfycbxkkWJjcwa2-O12vm-K86ZvMb8PBl30-vEAZwP-n1FtOldnFU-fgv5PZw9h460Hqvim/exec"
}

# --- 4. نظام اختيار الصف الدراسي ---
if "SHEET_URL" not in st.session_state:
    st.header("🎓 اختر صفك الدراسي للبدء")
    chosen_grade = st.selectbox("يرجى تحديد الصف:", list(GRADE_URLS.keys()))
    if st.button("تأكيد الدخول", key="confirm_btn"):
        st.session_state.SHEET_URL = GRADE_URLS[chosen_grade]
        st.session_state.grade_name = chosen_grade
        st.rerun()
    st.stop()

# --- 5. إعداد روابط الشيت اللحظية (Cache Busting) ---
SHEET_URL = st.session_state.SHEET_URL
ts = int(time.time())
LESSONS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=lessons&v={ts}")
QUIZZES_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=quizzes&v={ts}")
ANSWERS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=student_results&v={ts}")
WHITELIST_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=whitelist&v={ts}")

# --- 6. الدوال المساعدة ---
def clean_date_string(date_str):
    if not date_str or pd.isna(date_str) or str(date_str).lower() == 'nan' or str(date_str).strip() == '':
        return None
    s = str(date_str).strip().replace('/', '-')
    s = re.sub(r'\s+', ' ', s)
    is_pm = 'م' in s
    is_am = 'ص' in s
    s = s.replace('م', '').replace('ص', '').strip()
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            if is_pm and dt.hour < 12: dt = dt.replace(hour=dt.hour + 12)
            elif is_am and dt.hour == 12: dt = dt.replace(hour=0)
            return dt
        except: pass
    return None

def force_string(val):
    if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '':
        return ""
    return str(val).strip()

def verify_student_credentials(student_name, password):
    if not student_name or not password:
        return "waiting", "يرجى إدخال الاسم والرقم السري."
    s_name = "".join(student_name.split()).lower()
    s_pass = str(password).strip()
    try:
        df = pd.read_csv(WHITELIST_CSV, dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        name_col = next((c for c in df.columns if "name" in c or "اسم" in c), None)
        pass_col = next((c for c in df.columns if "pass" in c or "رقم" in c or "سري" in c), None)
        if not name_col or not pass_col:
            return "error", "⚠️ خطأ في بنية شيت الـ whitelist."
        for _, row in df.iterrows():
            row_name = "".join(force_string(row.get(name_col, '')).split()).lower()
            row_pass = force_string(row.get(pass_col, ''))
            if row_name == s_name and row_pass == s_pass:
                return "granted", "تم تسجيل الدخول بنجاح."
        return "denied", "❌ عذراً، الاسم أو الرقم السري غير صحيح."
    except:
        return "error", "⚠️ تعذر الاتصال بنظام التحقق."

def has_submitted_before(student_name, quiz_title):
    try:
        answers_df = pd.read_csv(ANSWERS_CSV, dtype=str)
        answers_df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in answers_df.columns]
        s_name = "".join(student_name.split()).lower()
        q_title = "".join(quiz_title.split()).lower()
        name_col = next((c for c in answers_df.columns if "student" in c or "اسم" in c), None)
        quiz_col = next((c for c in answers_df.columns if "quiz" in c or "امتحان" in c or "اختبار" in c), None)
        if name_col and quiz_col:
            for _, row in answers_df.iterrows():
                row_student = "".join(force_string(row.get(name_col, '')).split()).lower()
                row_quiz = "".join(force_string(row.get(quiz_col, '')).split()).lower()
                if row_student == s_name and row_quiz == q_title:
                    return True
    except: pass
    return False

def load_data():
    courses = {}
    quizzes = {}
    
    try:
        lessons_df = pd.read_csv(LESSONS_CSV, dtype=str)
        raw_columns = [str(c).strip() for c in lessons_df.columns]
        normalized_columns = [c.lower().replace("_", "").replace(" ", "") for c in raw_columns]
        c_title_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "course" in c or "كورس" in c))]
        l_title_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "lesson" in c or "درس" in c))]
        v_url_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "video" in c or "فيديو" in c))]
        p_url_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "pdf" in c or "ملف" in c))]

        for idx, row in lessons_df.iterrows():
            c_title = force_string(row.get(c_title_col, ''))
            if not c_title: continue
            if c_title not in courses: courses[c_title] = []
            courses[c_title].append({
                "title": force_string(row.get(l_title_col, f"المحاضرة {len(courses[c_title])+1}")),
                "video": force_string(row.get(v_url_col, '')),
                "pdf": force_string(row.get(p_url_col, ''))
            })
    except: pass

    try:
        quizzes_df = pd.read_csv(QUIZZES_CSV, dtype=str)
        raw_q_columns = [str(c).strip() for c in quizzes_df.columns]
        norm_q_columns = [c.lower().replace("_", "").replace(" ", "") for c in raw_q_columns]

        q_title_col = raw_q_columns[norm_q_columns.index(next(c for c in norm_q_columns if "quiz" in c or "امتحان" in c))]
        q_text_col = raw_q_columns[norm_q_columns.index(next(c for c in norm_q_columns if "question" in c or "سؤال" in c))]

        opt_a_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "opta" in c or "opt_b" in c or (c.endswith("a") and len(c)<=5)), None)
        opt_b_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "optb" in c or "opt_b" in c or (c.endswith("b") and len(c)<=5)), None)
        opt_c_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "optc" in c or "opt_c" in c or (c.endswith("c") and len(c)<=5)), None)
        opt_d_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "optd" in c or "opt_d" in c or (c.endswith("d") and len(c)<=5)), None)

        degree_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "degree" in c or "درج" in c or "درجه" in c), None)
        correct_col = next((raw_q_columns[i] for i, c in enumerate(norm_q_columns) if "correct" in c or "إجابة" in c), None)

        for _, row in quizzes_df.iterrows():
            q_title = force_string(row.get(q_title_col, ''))
            if not q_title: continue
            if q_title not in quizzes: quizzes[q_title] = []

            raw_correct = force_string(row.get(correct_col, '')).upper()
            final_correct = raw_correct[-1] if raw_correct.startswith('OPT') else raw_correct

            try:
                val_deg = row.get(degree_col, "1")
                if pd.isna(val_deg) or str(val_deg).strip() == "" or str(val_deg).lower() == 'nan':
                    q_deg = 1.0
                else:
                    q_deg = float(str(val_deg).strip())
                if q_deg <= 0: q_deg = 1.0
            except:
                q_deg = 1.0

            quizzes[q_title].append({
                "question": force_string(row.get(q_text_col, '')),
                "options": [
                    force_string(row.get(opt_a_col, '') if opt_a_col else ''),
                    force_string(row.get(opt_b_col, '') if opt_b_col else ''),
                    force_string(row.get(opt_c_col, '') if opt_c_col else ''),
                    force_string(row.get(opt_d_col, '') if opt_d_col else '')
                ],
                "correct": final_correct,
                "degree": q_deg,
                "start_at": row.get('startat', row.get('start_at', None)),
                "end_at": row.get('endat', row.get('end_at', None))
            })
    except: pass
    return courses, quizzes

# --- 7. واجهة تسجيل دخول الطالب ---
st.header("🎓 بوابة الطالب التعليمية")

if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

if not st.session_state.access_granted:
    st.subheader("🔒 تسجيل الدخول للطلاب")
    with st.form(key="login_form"):
        student_name_input = st.text_input("✍️ اسم الطالب الثلاثي:")
        student_password_input = st.text_input("🔑 الرقم السري:", type="password")
        submit_login = st.form_submit_button("🚪 دخول المنصة", type="primary")
        if submit_login:
            if not student_name_input.strip() or not student_password_input.strip():
                st.warning("⚠️ يرجى كتابة الاسم والرقم السري أولاً.")
            else:
                status, msg = verify_student_credentials(student_name_input.strip(), student_password_input.strip())
                if status == "granted":
                    st.session_state.access_granted = True
                    st.session_state.student_name = student_name_input.strip()
                    st.success(msg)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
    st.stop()

# --- 8. القائمة الجانبية ومحتوى المنصة الرئيسي ---
student_name = st.session_state.student_name
st.sidebar.success(f"👤 مرحبًا بك : {student_name}")
if st.sidebar.button("🔒 تسجيل الخروج"):
    st.session_state.access_granted = False
    st.rerun()

courses_db, quizzes_db = load_data()

if "current_view" not in st.session_state: 
    st.session_state.current_view = "sharh"

# أزرار التنقل العلوية
box_sharh, box_quiz = st.columns(2)
with box_sharh:
    if st.button("📺 الشرح والدروس", key="btn_sharh"): 
        st.session_state.current_view = "sharh"
with box_quiz:
    if st.button("📝 الامتحانات والاختبارات", key="btn_quiz"): 
        st.session_state.current_view = "quiz"
st.markdown("---")

# عرض المحاضرات والدروس
if st.session_state.current_view == "sharh":
    st.subheader("📺 قسم الدروس وفيديوهات الشرح")
    if courses_db:
        chosen_course = st.selectbox("اختر الوحدة:", list(courses_db.keys()))
        lessons_available = courses_db[chosen_course]
        if not lessons_available:
            st.info("👋 قريباً.. سيتم رفع دروس ومحتوى هذه الوحدة.")
        else:
            chosen_lesson = st.selectbox("اختر الدرس المراد مشاهدته:", [l['title'] for l in lessons_available])
            current_lesson = next(l for l in lessons_available if l['title'] == chosen_lesson)
            if current_lesson['video']: 
                st.video(current_lesson['video'])
            if current_lesson['pdf']:
                st.markdown("---")
                st.write("📄 **المرفقات والمذكرات الخاصة بالدرس:**")
                st.link_button("📂 اضغط هنا لفتح وتحميل ملف الـ PDF", current_lesson['pdf'], use_container_width=True)
    else:
        st.info("👋 لا توجد دروس مرفوعة حالياً...")

# عرض نظام الاختبارات الذكي
elif st.session_state.current_view == "quiz":
    st.subheader("📝 قسم الامتحانات والتقييمات الذكية")
    if not quizzes_db:
        st.info("👋 لا توجد امتحانات على المنصة حالياً...")
    else:
        chosen_quiz = st.selectbox("اختر الامتحان المطلوب للدخول:", list(quizzes_db.keys()))
        cairo_tz = pytz.timezone('Africa/Cairo')
        now = datetime.now(cairo_tz).replace(tzinfo=None)

        questions = quizzes_db[chosen_quiz]
        first_q = questions[0]
        quiz_allowed = True
        error_msg = ""

        start_dt = clean_date_string(first_q["start_at"])
        end_dt = clean_date_string(first_q["end_at"])

        if (first_q["start_at"] and str(first_q["start_at"]).lower() != 'nan' and str(first_q["start_at"]).strip() != '') and not start_dt:
            quiz_allowed = False
            error_msg = "⚠️ صيغة التاريخ في الشيت غير صحيحة."
        if quiz_allowed and start_dt and now < start_dt:
            quiz_allowed = False
            error_msg = f"⏳ عذراً، هذا الامتحان لم يبدأ بعد. ميعاد البدء المحدد: {first_q['start_at']}"
        if quiz_allowed and end_dt and now > end_dt:
            quiz_allowed = False
            error_msg = f"🚫 عذراً، انتهى الوقت المحدد لحل هذا الامتحان."

        if not quiz_allowed:
            st.error(error_msg)
        else:
            if has_submitted_before(student_name, chosen_quiz):
                st.error(f"❌ عذراً يا {student_name}، لقد قمت بأداء هذا الاختبار مسبقاً!")
            else:
                session_key = f"start_{chosen_quiz}"
                if session_key not in st.session_state:
                    st.session_state[session_key] = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

                with st.form(key=f"quiz_form_{chosen_quiz}"):
                    st.markdown(f"### 📋 {chosen_quiz}")
                    st.info(f"👤 الطالب: {student_name} | 🕒 وقت الدخول: {st.session_state[session_key]}")

                    student_answers = {}
                    for i, q in enumerate(questions):
                        st.markdown(f"#### **سؤال {i+1}: {q['question']}** *[الدرجة: {int(q['degree']) if q['degree'].is_integer() else q['degree']}]*")

                        letters = ["A", "B", "C", "D"]
                        available_options_for_radio = []
                        for idx, letter in enumerate(letters):
                            opt_text = str(q['options'][idx]).strip()
                            if opt_text != "" and opt_text.lower() != 'nan':
                                st.write(f"🔹 **{letter}:** {opt_text}")
                            available_options_for_radio.append(letter)

                        student_answers[i] = st.radio(f"اختر إجابة السؤال {i+1}:", options=available_options_for_radio, key=f"quiz_radio_q_{i}_{chosen_quiz}", horizontal=True)
                        st.markdown("---")

                    if st.form_submit_button("📥 إرسال الإجابات وإنهاء الامتحان"):
                        submit_time = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")
                        total_earned_degrees = 0.0
                        total_quiz_degrees = 0.0

                        for i, q in enumerate(questions):
                            selected_letter = str(student_answers[i]).strip().upper()
                            q_weight = q['degree']
                            total_quiz_degrees += q_weight

                            if selected_letter == str(q['correct']).strip().upper():
                                total_earned_degrees += q_weight

                        display_earned = int(total_earned_degrees) if total_earned_degrees.is_integer() else total_earned_degrees
                        display_total = int(total_quiz_degrees) if total_quiz_degrees.is_integer() else total_quiz_degrees

                        payload = {
                            "action": "submit_quiz", 
                            "student_name": student_name, 
                            "quiz_title": chosen_quiz,
                            "score": display_earned, 
                            "start_time": st.session_state[session_key], 
                            "submit_time": submit_time
                        }
                        try:
                            current_web_app = WEB_APP_URLS[st.session_state.grade_name]
                            requests.post(current_web_app, json=payload)
                            
                            st.success(f"✅ تم الإرسال بنجاح يا {student_name}!")
                            st.info(f"📊 درجتك: {display_earned} من {display_total}")
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"⚠️ حدث خطأ أثناء الإرسال: {e}")
