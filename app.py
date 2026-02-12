import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ И СТИЛЬ
st.set_page_config(page_title="Messenger", page_icon="💬", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #0E1117; }
    
    /* Стилизация заголовка */
    .chat-header {
        text-align: center;
        padding: 10px;
        border-bottom: 1px solid #30363D;
        margin-bottom: 20px;
    }

    /* Пузыри сообщений */
    .stChatMessage { border: none !important; padding: 5px !important; background-color: transparent !important; }
    
    /* Сообщение пользователя */
    div[data-testid="stChatMessageUser"] {
        background-color: #0088CC !important;
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 20% !important;
        padding: 10px !important;
    }
    
    /* Сообщение бота */
    div[data-testid="stChatMessageAssistant"] {
        background-color: #21262D !important;
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 20% !important;
        padding: 10px !important;
    }

    /* Убираем стандартные иконки и ставим свои через CSS (заглушка) */
    div[data-testid="stChatMessageUser"] img { display: none; }
    div[data-testid="stChatMessageAssistant"] img { display: none; }
    
    .stMarkdown p { color: #E6EDF3 !important; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ К ТАБЛИЦЕ
def init_db():
    try:
        info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, [
            "https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client.worksheet("Settings")
    except: return None, None

sheet, settings_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. УПРАВЛЕНИЕ ЛИЧНОСТЯМИ (Всегда доступно)
with st.expander("👤 Настройки профиля и собеседника", expanded=False):
    st.subheader("О тебе (пользователь)")
    user_info = st.text_area("Расскажи о себе (чтобы партнер тебя знал)", 
                             value=st.session_state.get('user_info', 'Подруга, любит уют и интересные истории'),
                             help="Эта информация поможет боту понимать, с кем он общается.")
    st.session_state.user_info = user_info

    st.divider()

    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        
        tab1, tab2 = st.tabs(["Выбрать", "Создать нового"])
        
        with tab1:
            if names:
                sel = st.selectbox("Твой партнер:", names)
                curr = next(i for i in data if i["Name"] == sel)
                # Формируем промпт: Личность бота + Инфо о пользователе
                st.session_state.persona = (
                    f"Ты {curr['Name']}, возраст {curr['Age']}. {curr['Prompt']}. "
                    f"Твой собеседник: {st.session_state.user_info}. "
                    "Общайся на 'ты', используй эмодзи, будь живым."
                )
                st.session_state.current_name = curr['Name']
                st.info(f"Сейчас активен: {sel}")

        with tab2:
            n = st.text_input("Имя нового героя")
            a = st.number_input("Возраст", 18, 99, 25)
            b = st.text_area("Биография и стиль")
            if st.button("✨ Сохранить и Обучить"):
                settings_sheet.append_row([n, b, a])
                st.success("Новый герой в списке! Переключись на 'Выбрать'.")
                st.rerun()

# 4. ИНТЕРФЕЙС ЧАТА
name_display = st.session_state.get('current_name', 'Companion')
st.markdown(f"<div class='chat-header'><h3>{name_display}</h3></div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отрисовка чата с кастомными иконками (через эмодзи вместо фото)
for m in st.session_state.messages:
    icon = "👤" if m["role"] == "user" else "🌟"
    with st.chat_message(m["role"], avatar=icon):
        st.markdown(m["content"])

if prompt := st.chat_input("Напиши мне..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.get('persona', 'Будь собой.')}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        
        with st.chat_message("assistant", avatar="🌟"):
            st.markdown(ans)
            
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), name_display, prompt, ans[:500]])
    except Exception as e:
        st.error("Минутку, я перезагружаю мысли...")
