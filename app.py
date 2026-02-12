import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. МАГИЯ ДИЗАЙНА: НЕОНОВЫЙ ХУАН
st.set_page_config(page_title="Cipher", page_icon="💡", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}

    /* Анимированный неоновый фон */
    .stApp {
        background: #0a0a0a;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.05) 0%, transparent 40%);
        overflow: hidden;
    }

    /* Создаем эффект движущихся волн света */
    .stApp::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: transparent;
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            rgba(255, 0, 0, 0.03) 100px,
            rgba(255, 0, 0, 0.03) 200px
        );
        animation: move 20s linear infinite;
        z-index: -1;
    }

    @keyframes move {
        from { transform: translate(0, 0); }
        to { transform: translate(100px, 100px); }
    }

    /* Карточки и приветствие (Glassmorphism) */
    .welcome-card {
        background: rgba(36, 47, 61, 0.6);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 25px;
        border: 1px solid rgba(255, 0, 0, 0.3);
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.2);
        text-align: center;
    }

    /* Кнопки в стиле Неон */
    .stButton>button {
        background: transparent !important;
        border: 1px solid #ff4b4b !important;
        color: white !important;
        box-shadow: 0 0 10px rgba(255, 75, 75, 0.4);
        transition: 0.3s;
        border-radius: 12px;
    }
    .stButton>button:hover {
        background: #ff4b4b !important;
        box-shadow: 0 0 25px rgba(255, 75, 75, 0.7);
    }

    /* Баблы сообщений */
    div[data-testid="stChatMessageUser"] {
        background: rgba(43, 82, 120, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    div[data-testid="stChatMessageAssistant"] {
        background: rgba(28, 39, 50, 0.8) !important;
        border: 1px solid rgba(255, 0, 0, 0.2) !important;
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.1);
    }

    /* Поле ввода */
    .stChatInputContainer {
        background-color: transparent !important;
        border: none !important;
    }
    
    .stChatInput textarea {
        background: rgba(36, 47, 61, 0.8) !important;
        border: 1px solid rgba(255, 0, 0, 0.2) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ДАЛЕЕ ОСТАЕТСЯ ТВОЯ ЛОГИКА С ТАБЛИЦАМИ (Users, Settings, Chat) ---
# (Я сокращу до структуры, чтобы ты видел, куда вставить)

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

# ЭКРАН 1: ПРИВЕТСТВИЕ С ФОТО ХУАНА
if st.session_state.app_state == "welcome":
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    # Вставь сюда ссылку на ту картинку, которую мы сделали
    st.image("https://твоя-ссылка-на-фото-640x360.jpg", use_container_width=True)
    
    st.markdown("""
        <div class='welcome-card'>
            <h2 style='color: white; margin-bottom: 10px;'>Хуан приветствует тебя</h2>
            <p style='color: #84919b;'>Теневой мессенджер активен. Твой партнер на связи.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("АКТИВИРОВАТЬ ЧАТ"):
        st.session_state.app_state = "user_select"
        st.rerun()

# --- Логика user_select, hero_select и chat (как в предыдущем коде) ---
# Не забудь добавить проверку app_state для остальных экранов!
