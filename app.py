import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq

# 1. Сначала логика, дизайн — вторым шагом
if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 2. ФУНКЦИЯ ДИЗАЙНА (ПИШЕМ АККУРАТНО)
def load_design():
    style = """
    <style>
    /* Прячем лишнее */
    header, footer {visibility: hidden;}
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* Компактный шрифт */
    * { font-size: 14px !important; }
    h1 { font-size: 24px !important; color: #ff4b4b !important; }
    /* Баблы */
    [data-testid="stChatMessageUser"] { background: #2b5278 !important; }
    [data-testid="stChatMessageAssistant"] { background: #1c2732 !important; border: 1px solid #ff4b4b !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

load_design()

# 3. ПОДКЛЮЧЕНИЕ (БАЗА)
def get_db():
    try:
        info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except: return None, None, None

sheet, settings_sheet, users_sheet = get_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. ЭКРАНЫ (УПРОЩЕННО ДЛЯ ПРОВЕРКИ)
if st.session_state.app_state == "welcome":
    st.title("ХУАН")
    st.write("Система готова к работе.")
    if st.button("ВОЙТИ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.subheader("Кто ты?")
    if users_sheet:
        names = [u['Name'] for u in users_sheet.get_all_records()]
        sel = st.selectbox("Профиль:", names if names else ["Пусто"])
        if st.button("Подтвердить") and names:
            st.session_state.u_name = sel
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    st.write(f"Чат с Хуаном (Вы: {st.session_state.u_name})")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    if p := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": p})
        st.rerun()
