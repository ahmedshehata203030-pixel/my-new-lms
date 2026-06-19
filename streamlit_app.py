import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import re
import time

# 🔗 [1] رابط الجوجل شيت الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/11sa1GDAYCez4b17aI1hDPKJDtfj953ySj8OMYOxbzTI/edit?usp=sharing"

# كسر كاش السيرفر لضمان قراءة البيانات اللحظية من الشيت
LESSONS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=lessons&v={int(time.time())}")
QUIZZES_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=quizzes&v={int(time.time())}")

# 🔒 الربط الحرفي والمباشر بتبويب الرصد الصحيح لقفل التكرار تماماً
ANSWERS_CSV = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet=student_results&v={int(time.time())}")

def clean_date_string(date_str):
    if not date_str or pd.isna(date_str) or str(date_str).lower() == 'nan' or str(date_str).strip() == '':
        return None
    s = str(date_str).strip()
    s = s.replace('/', '-')
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
    except:
        pass
    return False

def load_data():
    try:
        lessons_df = pd.read_csv(LESSONS_CSV, dtype=str)
        raw_columns = [str(c).strip() for c in lessons_df.columns]
        normalized_columns = [c.lower().replace("_", "").replace(" ", "") for c in raw_columns]
        
        # كاشف ذكي وصارم للوصول للأعمدة الحقيقية بالترتيب
        c_title_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "course" in c or "كورس" in c or "دبلوم" in c or "وحدة" in c))]
        l_title_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "lesson" in c or "درس" in c or "محاضر" in c or "عنوان" in c))]
        v_url_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "video" in c or "فيديو" in c or "رابط" in c))]
        p_url_col = raw_columns[normalized_columns.index(next(c for c in normalized_columns if "pdf" in c or "ملف" in c or "مذكر" in c))]
        
        courses = {}
        for idx, row in lessons_df.iterrows():
            c_title = force_string(row.get(c_title_col, ''))
            if not c_title: continue
            
            if c_title not in courses: courses[c_title] = []
            
            lesson_actual_title = force_string(row.get(l_title_col, ''))
            v_url = force_string(row.get(v_url_col, ''))
            p_url = force_string(row.get(p_url_col, ''))
            
            # فلترة حاسمة: لو مفيش عنوان مكتوب للدرس، ابحث عن الـ ID أو اكتب ترتيبه بدلاً من تركه فارغاً
            if not lesson_actual_title:
                lesson_id_col = next((c for c in raw_columns if "id" in c.lower()), None)
                if lesson_id_col:
                    lesson_actual_title = force_string(row.get(lesson_id_col, ''))
            
            # إذا استمر فارغاً تماماً والسطر كله ليس به روابط، تخطى هذا السطر
            if not lesson_actual_title and not v_url and not p_url:
                continue
                
            if not lesson_actual_title:
                lesson_actual_title = f"المحاضرة رقم {len(courses[c_title])+1}"
                
            courses[c_title].append({
                "title": lesson_actual_title, 
                "video": v_url, 
                "pdf": p_url
            })
    except: courses = {}

    try:
        quizzes_df = pd.read_csv(QUIZZES_CSV, dtype=str)
        raw_q_columns = [str(c).strip() for c in quizzes_df.columns]
        norm_q_columns = [c.lower().replace("_", "").replace(" ", "") for c in raw_q_columns]
        
        q_title_col = raw_q_columns[norm_q_columns.index(next(c for c in norm_q_columns if "quiz" in c or "امتحان" in c or "اختبار" in c))]
        q_text_col = raw_q_columns[norm_q_columns.index(next(c for c in norm_q_columns if "question" in c or "سؤال" in c or "السين" in c))]
        
        quizzes = {}
        for _, row in quizzes_df.iterrows():
            q_title = force_string(row.get(q_title_col, ''))
            if not q_title: continue
            
            if q_title not in quizzes: quizzes[q_title] = []
            
            quizzes[q_title].append({
                "question": force_string(row.get(q_text_col, '')),
                "options": [
                    force_string(row.get('opta', '') if 'opta' in norm_q_columns else row.get('opt_a', '')),
                    force_string(row.get('optb', '') if 'optb' in norm_q_columns else row.get('opt_b', '')),
                    force_string(row.get('optc', '') if 'optc' in norm_q_columns else row.get('opt_c', '')),
                    force_string(row.get('optd', '') if 'optd' in norm_q_columns else row.get('opt_d', ''))
                ],
                "correct": force_string(row.get('correctopt', '')).upper()[-1] if force_string(row.get('correctopt', '')).upper().startswith('OPT') else force_string(row.get('correctopt', '')).upper(),
                "start_at": row.get('startat', None),
                "end_at": row.get('endat', None)
            })
    except: 
        quizzes = {}
    return courses, quizzes

st.set_page_config(page_title="منصتي التعليمية", layout="wide")
st.cache_data.clear()
courses_db, quizzes_db = load_data()

st.header("🎓 بوابة الطالب التعليمية")
if "current_view" not in st.session_state: st.session_state.current_view = "sharh"

# 🛠️ الـ CSS المخصص للمنصة لإخفاء أزرار جيت هاب والـ Deploy
st.markdown("""
    <style>
    a[href*="github.com"], 
    button[title="View source"], 
    .stAppDeployButton,
    [class*="viewerBadge"],
    .viewerBadge_link__1S137,
    [data-testid="stActionButton"] {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stHeader"] button[aria-label="Manage app"],
    [data-testid="stHeader"] button[aria-label="Share this app"],
    [data-testid="stHeader"] button:not(#MainMenu) {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu, [data-testid="stHeader"] button#MainMenu {
        display: inline-flex !important;
        visibility: visible !important;
    }
    div[data-testid="stHorizontalBlock"] { 
        display: flex !important; 
        justify-content: center !important; 
        gap: 25px !important; 
    }
    div.stButton > button { 
        width: 100% !important; 
        height: 110px !important; 
        font-size: 26px !important; 
        font-weight: bold !important; 
        color: white !important; 
        border-radius: 15px !important; 
    }
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) div.stButton > button { 
        background-color: #1A365D !important; 
    }
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) div.stButton > button { 
        background-color: #064E3B !important; 
    }
    </style>
""", unsafe_allow_html=True)

box_sharh, box_quiz = st.columns(2)
with box_sharh:
    if st.button("📺 الشرح والدروس", key="btn_sharh"): st.session_state.current_view = "sharh"
with box_quiz:
    if st.button("📝 الامتحانات والاختبارات", key="btn_quiz"): st.session_state.current_view = "quiz"
st.markdown("---")

if st.session_state.current_view == "sharh":
    st.subheader("📺 قسم الدروس وفيديوهات الشرح")
    if courses_db:
        chosen_course = st.selectbox("اختر الوحدة:", list(courses_db.keys()))
        lessons_available = courses_db[chosen_course]
        
        if not lessons_available:
            st.info("👋 قريباً.. سيتم رفع دروس ومحاضرات هذا الكورس.")
        else:
            chosen_lesson = st.selectbox("اختر الدرس المراد مشاهدته:", [l['title'] for l in lessons_available])
            current_lesson = next(l for l in lessons_available if l['title'] == chosen_lesson)
            
            if current_lesson['video']:
                st.video(current_lesson['video'])
                
            if current_lesson['pdf']:
                st.markdown("---")
                st.write("📄 **المرفقات والمذكرات الخاصة بالدرس:**")
                st.link_button("📂 اضغط هنا لفتح وتحميل ملف الـ PDF", current_lesson['pdf'], use_container_width=True)

elif st.session_state.current_view == "quiz":
    st.subheader("📝 قسم الامتحانات والتقييمات الذكية")
    if not quizzes_db:
        st.info("👋 لا توجد امتحانات مرفوعة في الشيت حالياً...")
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
            error_msg = "⚠️ صيغة التاريخ في الشيت غير صحيحة، يرجى كتابته بصيغة: YYYY-MM-DD HH:MM:SS"
        
        if quiz_allowed and start_dt and now < start_dt:
            quiz_allowed = False
            error_msg = f"⏳ عذراً، هذا الامتحان لم يبدأ بعد. ميعاد البدء المحدد: {first_q['start_at']}"
            
        if quiz_allowed and end_dt and now > end_dt:
            quiz_allowed = False
            error_msg = f"🚫 عذراً، انتهى الوقت المحدد لحل هذا الامتحان. كان آخر ميعاد: {first_q['end_at']}"

        if not quiz_allowed:
            st.error(error_msg)
        else:
            student_name = st.text_input("✍️ من فضلك أدخل اسمك الثلاثي لبدء الاختبار:")
            if not student_name:
                st.warning("⚠️ يجب كتابة اسمك أولاً لتتمكن من حل الامتحان ورصد النتيجة.")
            else:
                if has_submitted_before(student_name, chosen_quiz):
                    st.error(f"❌ عذراً يا {student_name}، لقد قمت بأداء هذا الاختبار مسبقاً! غير مسموح بالدخول مرة أخرى.")
                else:
                    session_key = f"start_{chosen_quiz}"
                    if session_key not in st.session_state:
                        st.session_state[session_key] = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")
                        
                    with st.form(key=f"quiz_form_{chosen_quiz}"):
                        st.markdown(f"### 📋 {chosen_quiz}")
                        st.info(f"👤 الطالب: {student_name} | 🕒 وقت الدخول: {st.session_state[session_key]}")
                        
                        student_answers = {}
                        for i, q in enumerate(questions):
                            st.write(f"**سؤال {i+1}: {q['question']}**")
                            
                            display_options = []
                            letters = ["A", "B", "C", "D"]
                            for idx, letter in enumerate(letters):
                                opt_text = str(q['options'][idx]).strip()
                                if opt_text != "" and opt_text.lower() != 'nan':
                                    display_options.append(f"{letter} - {opt_text}")
                                else:
                                    display_options.append(letter)
                            
                            student_answers[i] = st.radio(
                                "اختر الإجابة:", 
                                options=display_options,
                                key=f"quiz_radio_q_{i}_{chosen_quiz}"
                            )
                        
                        if st.form_submit_button("📥 إرسال الإجابات وإنهاء الامتحان"):
                            submit_time = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")
                            
                            correct_count = 0
                            for i, q in enumerate(questions):
                                selected_letter = str(student_answers[i]).split(" - ")[0].strip().upper()
                                if selected_letter == str(q['correct']).strip().upper():
                                    correct_count += 1
                                    
                            score = int((correct_count / len(questions)) * 100)
                            
                            WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxB72pq4-UUV_N9NOUdZgaCqBYj6x3p2RcPXoY1CDPmCgvo_4yFMEdirZ_nK_c_S8fcPw/exec"
                            
                            payload = {
                                "student_name": student_name, "quiz_title": chosen_quiz, "score": score,
                                "start_time": st.session_state[session_key], "submit_time": submit_time
                            }
                            try: requests.post(WEB_APP_URL, json=payload)
                            except: pass
                            
                            st.markdown("---")
                            if score >= 50: st.success(f"🎉 ممتاز يا {student_name}! درجتك: {score}%")
                            else: st.error(f"😞 للأسف يا {student_name} درجتك: {score}%.")
                            st.balloons()
