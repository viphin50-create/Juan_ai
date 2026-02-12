import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА (PostImages - обычно работает лучше всех)
USER_PHOTO = "https://cdn.midjourney.com/u/3e5aa158-179e-48aa-88b0-bbef6bb9e7a0/0e909883da6dc88b440ea65fc9c9249352270c36a3b71af9f7744cf2b3d43381.png

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
        background: rgba(36, 47, 61, 0.2);
        backdrop-filter: blur(20px);
        padding: 25px;
        border-radius: 25px;
        border: 1px solid rgba(255, 75, 75, 0.3);
        text-align: center;
        margin-top: 30px;
    }
    .stButton>button {
        width: 100%;
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 12px;
        padding: 8px;
        font-weight: 600;
    }
    /* ЖЕСТКОЕ УДАЛЕНИЕ FACE И ART */
    [data-testid="stChatMessage"] [data-testid="stAvatar"] {
        display: none !important;
    }
    [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 0 !important;
    }
    /* Компактный хедер */
    .chat-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        padding: 12px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        border: 1px solid rgba(255, 75, 75, 0.2);
        margin-bottom: 20px;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
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
    except: return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЛОГИКА
if st.session_state.app_state == "welcome":
    st.markdown("<div class='welcome-card'><h1 style='color: #ff4b4b;'>JUAN AI</h1><p>Система в режиме ожидания...</p></div>", unsafe_allow_html=True)
    if st.button("РАЗБУДИТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>КТО В СЕТИ?</h3></div>", unsafe_allow_html=True)
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    tab_login, tab_reg = st.tabs(["ВХОД", "РЕГИСТРАЦИЯ"])
    with tab_login:
        if u_names:
            sel_u = st.selectbox("Выбери профиль:", u_names, key="login_dropdown")
            if st.button("ВОЙТИ", key="login_btn"):
                st.session_state.u_name = sel_u
                st.session_state.app_state = "hero_select"
                st.rerun()
        else: st.write("Нет активных профилей.")

    with tab_reg:
        new_n = st.text_input("Имя нового парня", key="new_user_name")
        new_b = st.text_area("О нем", key="new_user_bio")
        if st.button("СОЗДАТЬ ПРОФИЛЬ", key="reg_btn"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>ПРИВЕТ, {st.session_state.u_name}</h3></div>", unsafe_allow_html=True)
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in h_data]
        sel_h = st.selectbox("С кем на связи?", h_names, key="hero_dropdown")
        if st.button("УСТАНОВИТЬ СОЕДИНЕНИЕ"):
            h = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. ПИШИ С ЭМОДЗИ! ⚡️✨"
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    st.markdown(f"""
        <div class="chat-header">
            <img src="{USER_PHOTO}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 10px;">● В СЕТИ</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        icon = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]):
            st.markdown(f"{icon} {m['content']}")
    
    if p := st.chat_input("Напиши сообщение... 💭"):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(f"👤 {p}")
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(f"✨ {ans}")
        st.session_state.messages.append({"role": "assistant", "content": ans})
        if sheet: 
            try: sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])
            except: pass

    if st.button("ЗАВЕРШИТЬ СЕАНС"):
        st.session_state.app_state = "welcome"
        st.rerun()
