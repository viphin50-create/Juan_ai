import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ И НЕОНОВЫЙ СТИЛЬ
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

st.set_page_config(page_title="JUAN AI", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;900&display=swap');
    
    header, footer, #MainMenu {visibility: hidden !important;}
    
    .stApp {
        background-color: #050505 !important;
        background-image: radial-gradient(circle at 50% 50%, #250505 0%, #050505 100%) !important;
        color: #ffffff !important;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* АНИМАЦИЯ ЛОГОТИПА */
    @keyframes pulse-red {
        0% { text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000; opacity: 0.8; }
        50% { text-shadow: 0 0 20px #ff0000, 0 0 40px #ff0000, 0 0 60px #ff0000; opacity: 1; }
        100% { text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000; opacity: 0.8; }
    }
    .glitch-logo {
        text-align: center;
        font-size: clamp(40px, 8vw, 80px) !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        letter-spacing: 15px !important;
        animation: pulse-red 3s infinite ease-in-out;
        margin: 40px 0;
    }

    /* НЕОНОВЫЕ КНОПКИ */
    .stButton>button {
        width: 100% !important;
        background: transparent !important;
        border: 2px solid #ff0000 !important;
        color: #ff0000 !important;
        box-shadow: 0 0 10px #ff0000, inset 0 0 5px #ff0000 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        font-weight: 700 !important;
        transition: 0.3s !important;
        border-radius: 0px !important;
    }
    .stButton>button:hover {
        background: #ff0000 !important;
        color: white !important;
        box-shadow: 0 0 30px #ff0000 !important;
    }

    /* ЧАТ-СООБЩЕНИЯ */
    div[data-testid="stChatMessage"] {
        background: rgba(30, 0, 0, 0.4) !important;
        border-left: 3px solid #ff0000 !important;
        border-radius: 5px !important;
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.1) !important;
    }

    /* ТАБЫ И ВВОД */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    .stChatInputContainer textarea { border: 1px solid #ff0000 !important; background: #101010 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ К БД
@st.cache_resource
def init_db():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds).open("Juan")
        return client.worksheet("Settings"), client.worksheet("Users"), client.worksheet("Profiles")
    except: return None, None, None

settings_sheet, users_sheet, profiles_sheet = init_db()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state: st.session_state.app_state = "user_select"

# --- ШАГ 1: ВХОД В СИСТЕМУ ---
if st.session_state.app_state == "user_select":
    st.markdown('<div class="glitch-logo">JUAN AI</div>', unsafe_allow_html=True)
    
    profiles = profiles_sheet.get_all_records() if profiles_sheet else []
    u_names = [p['user_id'] for p in profiles]
    
    t1, t2 = st.tabs(["ВХОД", "РЕГИСТРАЦИЯ"])
    
    with t1:
        u_choice = st.selectbox("ПРОФИЛЬ", u_names if u_names else ["НЕТ ДАННЫХ"])
        if st.button("ПОДКЛЮЧИТЬСЯ") and u_choice != "НЕТ ДАННЫХ":
            p_data = next(p for p in profiles if p['user_id'] == u_choice)
            st.session_state.u_name = u_choice
            st.session_state.u_bio = p_data.get('bio', '')
            st.session_state.app_state = "hero_select"
            st.rerun()
            
    with t2:
        new_u = st.text_input("НОВЫЙ ID")
        new_u_bio = st.text_area("О СЕБЕ (БИОГРАФИЯ ДЛЯ ИИ)")
        if st.button("СОЗДАТЬ АККАУНТ") and new_u:
            profiles_sheet.append_row([new_u, new_u_bio, datetime.now().strftime("%Y-%m-%d")])
            st.session_state.u_name = new_u
            st.session_state.u_bio = new_u_bio
            st.session_state.app_state = "hero_select"
            st.rerun()

# --- ШАГ 2: ВЫБОР ПАРТНЕРА ---
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center; color:#ff0000; letter-spacing:2px;'>USER: {st.session_state.u_name.upper()}</p>", unsafe_allow_html=True)
    
    heroes = settings_sheet.get_all_records() if settings_sheet else []
    h_names = [h['partner_id'] for h in heroes]
    
    m1, m2 = st.tabs(["СПИСОК ПАРТНЕРОВ", "СОЗДАТЬ НОВОГО"])
    
    with m1:
        h_choice = st.selectbox("ВЫБЕРИТЕ ЛИЧНОСТЬ", h_names if h_names else ["ПУСТО"])
        if st.button("УСТАНОВИТЬ СВЯЗЬ") and h_names:
            h = next(i for i in heroes if i["partner_id"] == h_choice)
            st.session_state.current_name = h['partner_id']
            st.session_state.persona = f"Ты {h['partner_id']}. {h['system_prompt']}. Собеседник: {st.session_state.u_name}. О нем: {st.session_state.u_bio}. Романтика, LGBT+, эмодзи."
            
            # ЗАГРУЗКА ПАМЯТИ
            all_hist = users_sheet.get_all_records()
            st.session_state.messages = [
                {"role": r['role'], "content": r['content']} 
                for r in all_hist if str(r.get('user_id')) == st.session_state.u_name and str(r.get('partner_id')) == h_choice
            ][-15:]
            st.session_state.app_state = "chat"
            st.rerun()
            
    with m2:
        with st.form("new_h"):
            n_id = st.text_input("ID ГЕРОЯ")
            n_p = st.text_area("SYSTEM PROMPT (ХАРАКТЕР)")
            if st.form_submit_button("ЗАПИСАТЬ В СИСТЕМУ"):
                settings_sheet.append_row([n_id, n_id, n_p, "", "777", ""])
                st.success("ГЕРОЙ ДОБАВЛЕН")

    if st.button("⬅ ВЕРНУТЬСЯ К ВЫБОРУ ЮЗЕРА"):
        st.session_state.app_state = "user_select"
        st.rerun()

# --- ШАГ 3: ЧАТ ---
elif st.session_state.app_state == "chat":
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px;">
                <img src="{AI_AVATAR}" style="width: 50px; border-radius: 50%; border: 2px solid #ff0000; filter: drop-shadow(0 0 5px #ff0000);">
                <div>
                    <div style="color: #ff0000; font-size: 18px; font-weight: 700;">{st.session_state.current_name.upper()}</div>
                    <div style="font-size: 10px; color: #ff0000;">SIGNAL ESTABLISHED</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        if st.button("LOGOUT"):
            st.session_state.app_state = "user_select" # ПОЛНЫЙ СБРОС
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "user", p, datetime.now().strftime("%H:%M")])

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = response.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "assistant", ans, datetime.now().strftime("%Y-%m-%d %H:%M")])
