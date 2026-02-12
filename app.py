import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Прямая ссылка на фото для хедера
USER_PHOTO = "https://i.yapx.ru/Yif9K.jpg"

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
        background: rgba(36, 47, 61, 0.2);
        backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 30px;
        border: 1px solid rgba(255, 0, 0, 0.3);
        text-align: center;
        margin-top: 50px;
        box-shadow: 0 0 30px rgba(255, 0, 0, 0.1);
    }
    .stButton>button {
        width: 100%;
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 15px;
        padding: 10px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: rgba(255, 75, 75, 0.3) !important;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.4);
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

# 3. ЛОГИКА ЭКРАНОВ
if st.session_state.app_state == "welcome":
    st.markdown("""
        <div class='welcome-card'>
            <h1 style='letter-spacing: 5px; color: #ff4b4b;'>JUAN AI</h1>
            <p style='opacity: 0.6; font-weight: 300;'>Система находится в режиме ожидания...</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("РАЗБУДИТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>КТО В СЕТИ?</h3></div>", unsafe_allow_html=True)
    if users_sheet:
        u_data = users_sheet.get_all_records()
        u_names = [u['Name'] for u in u_data]
        t1, t2 = st.tabs(["ВХОД", "РЕГИСТРАЦИЯ"])
