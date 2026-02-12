import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Настройки аватарок
USER_AVATAR = "https://i.yapx.ru/Yif9K.jpg"
BOT_AVATAR = "✨"

# 1. ДИЗАЙН
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

# 2. ПОДКЛЮЧЕНИЕ
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

# 3. ЛОГИКА
if st.session_state.app_state == "welcome":
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-card'><h1>ХУАН</h1><p>Система готова ⚡️</p></div>", unsafe_allow_html=True)
    if st.button("АКТИВИРОВАТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "chat":
    # --- НОВЫЙ СТИЛЬНЫЙ ХЕДЕР С АВАТАРКОЙ ---
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 20px;">
            <img src="https://i.yapx.ru/Yif9K.jpg" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 14px; font-weight: 600; letter-spacing: 1px;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 10px; opacity: 0.8;">● ONLINE</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Отображение сообщений (без аватарок внутри, чтобы не перегружать)
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): 
            st.markdown(m["content"])
    
    if p := st.chat_input("Напиши что-нибудь..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): 
            st.markdown(p)
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): 
            st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet: 
            sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])

    if st.button("Выйти"):
        st.session_state.app_state = "welcome"
        st.rerun()
