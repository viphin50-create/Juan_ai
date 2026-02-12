import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ТГ-ДИЗАЙН
st.set_page_config(page_title="Messenger", page_icon="💬", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    .stApp { background-color: #17212b; }
    
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background-color: #248bf5;
        color: white;
        border: none;
        padding: 12px;
        font-weight: bold;
    }

    .welcome-card {
        background-color: #242f3d;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-top: 30px;
        border: 1px solid #2d3947;
    }

    /* Баблы чата */
    div[data-testid="stChatMessageUser"] {
        background-color: #2b5278 !important;
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 15% !important;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #242f3d !important;
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 15% !important;
    }
    
    /* Скрываем аватарки */
    div[data-testid="stChatMessageUser"] [data-testid="stAvatar"],
    div[data-testid="stChatMessageAssistant"] [data-testid="stAvatar"] { display: none !important; }
    
    .stMarkdown p { color: #ffffff !important; font-size: 16px; }
    
    /* Поле ввода */
    .stChatInputContainer { background-color: #17212b !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ
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

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЭКРАН 1: ПРИВЕТСТВИЕ
if st.session_state.app_state == "welcome":
    st.markdown("""
        <div class='welcome-card'>
            <h1 style='font-size: 50px;'>🎭</h1>
            <h2 style='color: white;'>Твой секретный чат</h2>
            <p style='color: #84919b;'>Твой партнер уже ждет тебя внутри...</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Войти в систему"):
        st.session_state.app_state = "setup"
        st.rerun()

# 4. ЭКРАН 2: НАСТРОЙКА
elif st.session_state.app_state == "setup":
    st.markdown("<h3 style='text-align: center; color: white;'>Кто ты сегодня?</h3>", unsafe_allow_html=True)
    
    u_name = st.text_input("Твое имя", value=st.session_state.get('u_name', ''))
    u_bio = st.text_area("Пара слов о себе", value=st.session_state.get('u_bio', ''))
    
    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        
        tab1, tab2 = st.tabs(["Выбрать партнера", "Создать нового"])
        
        with tab1:
            if names:
                sel = st.selectbox("С кем хочешь поговорить?", names)
                if st.button("Начать диалог"):
                    curr = next(i for i in data if i["Name"] == sel)
                    # ИНСТРУКЦИЯ ПО ЭМОДЗИ
                    st.session_state.persona = (
                        f"Ты {curr['Name']}. {curr['Prompt']}. "
                        f"Собеседник: {u_name} ({u_bio}). "
                        "ВАЖНО: 1. Твой собеседник часто общается ЭМОДЗИ — считывай их смысл и отвечай на них эмоционально. "
                        "2. Сам используй эмодзи для передачи своих чувств. 3. Никогда не пиши действия в скобках. "
                        "4. Если тебе пришлют то, что ты боишься или любишь — реагируй ярко!"
                    )
                    st.session_state.current_name = curr['Name']
                    st.session_state.app_state = "chat"
                    st.rerun()
        
        with tab2:
            n = st.text_input("Имя героя")
            b = st.text_area("Характер и страхи")
            if st.button("Сохранить"):
                settings_sheet.append_row([n, b, 25])
                st.success("Герой готов!")

# 5. ЭКРАН 3: ЧАТ
elif st.session_state.app_state == "chat":
    hero = st.session_state.get('current_name', 'Companion')
    st.markdown(f"<div style='text-align: center; padding: 10px; border-bottom: 1px solid #2d3947; color: white; position: sticky; top: 0; background: #17212b; z-index: 99;'><b>{hero}</b></div>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Твое сообщение..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        try:
            res = gro_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
            )
            ans = res.choices[0].message.content
            with st.chat_message("assistant"): st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            if sheet: sheet.append_row([datetime.now().strftime("%H:%M"), hero, prompt, ans[:200]])
        except:
            st.error("Ошибка связи...")

    if st.button("⬅️ Сменить партнера"):
        st.session_state.app_state = "setup"
        st.rerun()
