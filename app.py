import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. СТИЛИ (Вставляем максимально просто, чтобы не путать Streamlit)
st.set_page_config(page_title="Cipher", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* Тот самый темный фон с красным свечением */
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.15) 0%, transparent 50%) !important;
        color: white !important;
    }

    /* Красивый компактный шрифт и карточки */
    .welcome-card {
        background: rgba(36, 47, 61, 0.5);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 0, 0, 0.2);
        text-align: center;
        margin-bottom: 20px;
    }

    .stButton>button {
        width: 100%;
        background: transparent !important;
        border: 1px solid #ff4b4b !important;
        color: white !important;
        border-radius: 10px;
    }

    /* Настройка чата */
    div[data-testid="stChatMessage"] { background: transparent !important; }
    div[data-testid="stChatMessageUser"] { background: rgba(43, 82, 120, 0.6) !important; border-radius: 10px !important; }
    div[data-testid="stChatMessageAssistant"] { background: rgba(28, 39, 50, 0.7) !important; border: 1px solid rgba(255, 0, 0, 0.2) !important; border-radius: 10px !important; }
    div[data-testid="stAvatar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ К БАЗЕ
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

# 3. ЭКРАНЫ
if st.session_state.app_state == "welcome":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-card'><h1>ХУАН</h1><p>Теневой канал связи открыт</p></div>", unsafe_allow_html=True)
    if st.button("АКТИВИРОВАТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>Авторизация</h3></div>", unsafe_allow_html=True)
    if users_sheet:
        users = users_sheet.get_all_records()
        names = [u['Name'] for u in users]
        sel = st.selectbox("Кто ты?", names if names else ["Список пуст"])
        if st.button("Войти") and names:
            curr = next(i for i in users if i["Name"] == sel)
            st.session_state.u_name, st.session_state.u_bio = curr['Name'], curr['Bio']
            st.session_state.app_state = "hero_select"
            st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>Привет, {st.session_state.u_name}</h3></div>", unsafe_allow_html=True)
    if settings_sheet:
        heroes = settings_sheet.get_all_records()
        sel_h = st.selectbox("С кем говорим?", [h['Name'] for h in heroes])
        if st.button("Начать"):
            h = next(i for i in heroes if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}."
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    st.markdown(f"<div style='text-align:center; color:#ff4b4b;'>● {st.session_state.current_name}</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        res = gro_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages)
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
