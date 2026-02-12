import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Настройки аватарок
USER_AVATAR = "https://iimg.su/i/7LggqS"
BOT_AVATAR = "✨"

# 1. ДИЗАЙН (Montserrat + Neon)
st.set_page_config(page_title="Cipher", layout="centered")

st.markdown('<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.1) 0%, transparent 50%) !important;
        color: white !important;
    }
    .welcome-card {
        background: rgba(36, 47, 61, 0.4);
        backdrop-filter: blur(15px);
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(255, 0, 0, 0.2);
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background: transparent !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 12px;
    }
    div[data-testid="stChatMessageUser"] { 
        background: rgba(43, 82, 120, 0.6) !important; 
        border-radius: 15px 15px 2px 15px !important; 
    }
    div[data-testid="stChatMessageAssistant"] { 
        background: rgba(28, 39, 50, 0.7) !important; 
        border-radius: 15px 15px 15px 2px !important; 
        border: 0.5px solid rgba(255, 0, 0, 0.15) !important; 
    }
    [data-testid="stChatMessage"] img {
        border-radius: 50%;
        border: 1px solid rgba(255, 75, 75, 0.5);
    }
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
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except:
        return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ЭКРАНОВ
if st.session_state.app_state == "welcome":
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-card'><h1>ХУАН</h1><p>Система готова ⚡️</p></div>", unsafe_allow_html=True)
    if st.button("АКТИВИРОВАТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>Кто здесь? 👤</h3></div>", unsafe_allow_html=True)
    if users_sheet:
        u_data = users_sheet.get_all_records()
        u_names = [u['Name'] for u in u_data]
        t1, t2 = st.tabs(["Вход", "Создать профиль"])
        with t1:
            if u_names:
                sel_u = st.selectbox("Выбери профиль:", u_names)
                if st.button("Войти"):
                    curr = next(i for i in u_data if i["Name"] == sel_u)
                    st.session_state.u_name, st.session_state.u_bio = curr['Name'], curr['Bio']
                    st.session_state.app_state = "hero_select"
                    st.rerun()
        with t2:
            new_n = st.text_input("Никнейм")
            new_b = st.text_area("О себе")
            if st.button("Зарегистрироваться"):
                if new_n:
                    users_sheet.append_row([new_n, new_b])
                    st.session_state.u_name, st.session_state.u_bio = new_n, new_b
                    st.session_state.app_state = "hero_select"
                    st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>Привет, {st.session_state.u_name} 👋</h3></div>", unsafe_allow_html=True)
    if settings_sheet:
        heroes = settings_sheet.get_all_records()
        sel_h = st.selectbox("С кем общаемся?", [h['Name'] for h in heroes])
        if st.button("Начать"):
            h = next(i for i in heroes if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. ВАЖНО: Используй эмодзи и живой язык."
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    st.markdown(f"<div style='text-align:center; color:#ff4b4b; font-size:12px;'>● {st.session_state.current_name.upper()}</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        av = USER_AVATAR if m["role"] == "user" else BOT_AVATAR
        with st.chat_message(m["role"], avatar=av): st.markdown(m["content"])
    
    if p := st.chat_input("Напиши что-нибудь..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user", avatar=USER_AVATAR): st.markdown(p)
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-
