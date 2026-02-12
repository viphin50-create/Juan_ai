import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ И СТИЛЬ
st.set_page_config(page_title="Companion", page_icon="🤍", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #0E1117; }
    
    .chat-header {
        text-align: center;
        padding: 10px;
        border-bottom: 1px solid #30363D;
        margin-bottom: 20px;
        color: white;
    }

    /* Пузыри сообщений */
    .stChatMessage { border: none !important; padding: 5px !important; background-color: transparent !important; }
    
    div[data-testid="stChatMessageUser"] {
        background-color: #0088CC !important;
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 20% !important;
        padding: 10px !important;
    }
    
    div[data-testid="stChatMessageAssistant"] {
        background-color: #21262D !important;
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 20% !important;
        padding: 10px !important;
    }

    /* Полное скрытие стандартных аватарок */
    div[data-testid="stChatMessageUser"] img, 
    div[data-testid="stChatMessageAssistant"] img { display: none; }
    
    .stMarkdown p { color: #E6EDF3 !important; font-size: 16px; }
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
        return client.get_worksheet(0), client.worksheet("Settings")
    except: return None, None

sheet, settings_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. НАСТРОЙКИ (В складном блоке)
with st.expander("👤 Настройки профиля и собеседника", expanded=False):
    st.subheader("О пользователе")
    u_info = st.text_area("Данные о тебе (кто ты, что любишь):", 
                         value=st.session_state.get('u_info', 'Твоя подруга, любит внимание и кофе'),
                         key="u_info_input")
    st.session_state.u_info = u_info

    st.divider()

    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        
        tab1, tab2 = st.tabs(["Выбрать партнера", "Создать нового"])
        
        with tab1:
            if names:
                sel = st.selectbox("С кем общаемся?", names)
                curr = next(i for i in data if i["Name"] == sel)
                
                # ЖЕСТКАЯ ПРОШИВКА ЛИЧНОСТИ
                st.session_state.persona = (
                    f"Ты {curr['Name']}, возраст {curr['Age']}. {curr['Prompt']}. "
                    f"Твой собеседник: {st.session_state.u_info}. "
                    "ПРАВИЛА: 1. Общайся на 'ты'. 2. НИКОГДА не пиши действия в скобках вроде (улыбается). "
                    "3. Вместо этого используй подходящие ЭМОДЗИ. 4. Будь живым и эмоциональным."
                )
                st.session_state.current_name = curr['Name']
                st.info(f"Активен: {sel}")

        with tab2:
            n = st.text_input("Имя нового героя")
            a = st.number_input("Возраст", 18, 99, 25)
            b = st.text_area("Биография и стиль (Мигель, поэт, сорванец и т.д.)")
