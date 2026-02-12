import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ И ТГ-СТИЛЬ (УЛУЧШЕННЫЙ КОНТРАСТ)
st.set_page_config(page_title="Messenger", page_icon="💬", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* Основной фон (чуть светлее, чтобы не сливалось) */
    .stApp {
        background-color: #1c2732; 
    }
    
    /* Шапка чата */
    .chat-header {
        text-align: center;
        padding: 15px;
        background-color: #242f3d;
        border-bottom: 1px solid #101921;
        color: #ffffff;
        font-family: -apple-system, system-ui, Roboto;
        position: sticky;
        top: 0;
        z-index: 999;
    }

    /* Пузыри сообщений */
    .stChatMessage { border: none !important; padding: 10px !important; }
    
    /* Свой бабл */
    div[data-testid="stChatMessageUser"] {
        background-color: #2b5278 !important;
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 15% !important;
        border: 1px solid #36608a !important;
    }
    
    /* Бабл бота */
    div[data-testid="stChatMessageAssistant"] {
        background-color: #242f3d !important;
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 15% !important;
        border: 1px solid #2d3947 !important;
    }

    /* Аватарки-заглушки */
    div[data-testid="stChatMessageUser"] [data-testid="stAvatar"],
    div[data-testid="stChatMessageAssistant"] [data-testid="stAvatar"] {
        display: none !important;
    }

    .stMarkdown p { color: #ffffff !important; font-size: 15px !important; }
    
    /* Поле ввода */
    .stChatInputContainer {
        padding: 15px !important;
        background-color: #1c2732 !important;
    }
    
    /* Вкладки настроек */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #242f3d;
        border-radius: 10px;
        padding: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. БАЗА ДАННЫХ
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

# 3. НАСТРОЙКИ (ВЕРХНЯЯ ПАНЕЛЬ)
with st.expander("⚙️ Твой профиль и настройки партнера", expanded=False):
    # ОБРАЗ ПОЛЬЗОВАТЕЛЯ
    st.subheader("Твой образ")
    u_name = st.text_input("Как тебя называть?", value=st.session_state.get('u_name', 'Подруга'))
    u_bio = st.text_area("Твои интересы и факты о тебе:", 
                        value=st.session_state.get('u_bio', 'Люблю кофе и хорошие шутки'),
                        placeholder="Напиши здесь, что партнер должен о тебе помнить...")
    
    st.session_state.u_name = u_name
    st.session_state.u_bio = u_bio
    
    st.divider()

    # УПРАВЛЕНИЕ ГЕРОЯМИ
    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        
        tab1, tab2 = st.tabs(["Выбрать героя", "Создать нового"])
        
        with tab1:
            if names:
                sel = st.selectbox("С кем хочешь пообщаться?", names)
                curr = next(i for i in data if i["Name"] == sel)
                st.session_state.persona = (
                    f"Ты {curr['Name']}, тебе {curr['Age']}. {curr['Prompt']}. "
                    f"Ты общаешься с пользователем по имени {u_name}. Вот что ты знаешь о нем: {u_bio}. "
                    "ПРАВИЛА: Общайся на 'ты', используй эмодзи, не пиши действия текстом в скобках."
                )
                st.session_state.current_name = curr['Name']
                st.success(f"Выбран: {sel}")

        with tab2:
            st.write("Добавь новую личность в базу:")
            new_n = st.text_input("Имя героя")
            new_a = st.number_input("Возраст", 18, 99, 25)
            new_b = st.text_area("Описание (биография, стиль речи)")
            if st.button("✨ Создать и сохранить"):
                if new_n and new_b:
                    settings_sheet.append_row([new_n, new_b, new_age])
                    st.success(f"Герой {new_n} добавлен! Теперь выбери его в первой вкладке.")
                    st.rerun()

# 4. ИНТЕРФЕЙС ЧАТА
curr_hero = st.session_state.get('current_name', 'Companion')
st.markdown(f"<div class='chat-header'><b>{curr_hero}</b></div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Вывод сообщений
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Напиши сообщение..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        current_p = st.session_state.get('persona', "Будь собой и используй эмодзи.")
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": current_p}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        
        with st.chat_message("assistant"):
            st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet:
            sheet.append_row([datetime.now().strftime("%d.%m %H:%M"), curr_hero, prompt, ans[:200]])
    except:
        st.error("Минутку, я перезагружаю мысли...")
