import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Прямая ссылка на фото
USER_PHOTO = "https://i.yapx.ru/Yif9K.jpg"

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
        padding: 30px;
        border-radius: 30px;
        border: 1px solid rgba(255, 0, 0, 0.3);
        text-align: center;
        margin-top: 50px;
    }
    .stButton>button {
        width: 100%;
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 15px;
        padding: 10px;
        font-weight: 600;
        margin-top: 10px;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important;
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
    st.markdown("<div class='welcome-card'><h1 style='color: #ff4b4b;'>JUAN AI</h1><p>Система в режиме ожидания...</p></div>", unsafe_allow_html=True)
    if st.button("РАЗБУДИТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>КТО В СЕТИ?</h3></div>", unsafe_allow_html=True)
    
    # Сначала пробуем получить список пользователей
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    # Разделяем логику Входа и Регистрации четко через табы
    tab_login, tab_reg = st.tabs(["ВХОД", "РЕГИСТРАЦИЯ"])

    with tab_login:
        if u_names:
            sel_u = st.selectbox("Твой профиль:", u_names, key="login_select")
            if st.button("ПОДТВЕРДИТЬ ВХОД"):
                st.session_state.u_name = sel_u
                st.session_state.app_state = "hero_select"
                st.rerun()
        else:
            st.write("Список пуст. Создай профиль!")

    with tab_reg:
        new_n = st.text_input("Как тебя называть?", key="reg_name")
        new_b = st.text_area("Пару слов о тебе (для памяти ИИ)", key="reg_bio")
        if st.button("СОЗДАТЬ И ВОЙТИ"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()
            else:
                st.error("Введи хотя бы имя!")

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>ПРИВЕТ, {st.session_state.u_name}</h3><p>Выбери личность:</p></div>", unsafe_allow_html=True)
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in h_data]
        sel_h = st.selectbox("Контакт:", h_names)
        if st.button("УСТАНОВИТЬ СОЕДИНЕНИЕ"):
            h = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}."
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    # Твой стильный хедер с аватаркой
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 25px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 20px;">
            <img src="{USER_PHOTO}" style="width: 55px; height: 55px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 11px;">● В СЕТИ</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("Напиши сообщение..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        if sheet:
            try: sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])
            except: pass

    if st.button("ЗАВЕРШИТЬ СЕАНС"):
        st.session_state.app_state = "welcome"
        st.rerun()
