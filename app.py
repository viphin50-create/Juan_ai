import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ДИЗАЙН И ШРИФТЫ
st.set_page_config(page_title="Cipher", page_icon="💡", layout="centered")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}

    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif !important;
        color: white !important;
    }

    .stApp {
        background: #0a0a0a;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.15) 0%, transparent 45%),
            radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.05) 0%, transparent 45%);
    }

    .stApp::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 80px,
            rgba(255, 0, 0, 0.02) 80px,
            rgba(255, 0, 0, 0.02) 160px
        );
        animation: drift 25s linear infinite;
        z-index: -1;
    }

    @keyframes drift {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .welcome-card {
        background: rgba(36, 47, 61, 0.4);
        backdrop-filter: blur(20px);
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(255, 0, 0, 0.2);
        text-align: center;
        margin-bottom: 15px;
    }

    h1 { font-size: 26px !important; font-weight: 600 !important; }
    h2 { font-size: 14px !important; font-weight: 300 !important; color: #84919b !important; }
    
    .stButton>button {
        width: 100%;
        background: transparent !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 12px;
        font-size: 14px !important;
        transition: 0.3s;
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

    .stMarkdown p { font-size: 13px !important; font-weight: 300 !important; }
    div[data-testid="stAvatar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ К БАЗЕ
def init_db():
    try:
        info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, [
            "https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except: return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЛОГИКА ЭКРАНОВ
if st.session_state.app_state == "welcome":
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-card'><h1>ХУАН</h1><h2>Система активна.</h2></div>", unsafe_allow_html=True)
    if st.button("АКТИВИРОВАТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h1>Кто ты?</h1></div>", unsafe_allow_html=True)
    if users_sheet:
        u_data = users_sheet.get_all_records()
        u_names = [u['Name'] for u in u_data]
        sel_u = st.selectbox("Выбери профиль:", u_names if u_names else ["Нет данных"])
        if st.button("Войти") and u_names:
            curr = next(i for i in u_data if i["Name"] == sel_u)
            st.session_state.u_name, st.session_state.u_bio = curr['Name'], curr['Bio']
            st.session_state.app_state = "hero_select"
            st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h1>С кем чат, {st.session_state.u_name}?</h1></div>", unsafe_allow_html=True)
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in h_data]
        sel_h = st.selectbox("Партнер:", h_names)
        if st.button("Начать"):
            h_curr = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h_curr['Name']}. {h_curr['Prompt']}. Собеседник: {st.session_state.u_name}."
            st.session_state.current_name = h_curr['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    st.markdown(f"<div style='text-align: center; color: #ff4b4b; font-size: 12px;'>● {st.session_state.current_name.upper()}</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if prompt := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        res = gro_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages)
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
