import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. СТИЛЬ (Чистый мобильный интерфейс)
st.set_page_config(page_title="Companion", page_icon="🧸", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #111111; }
    
    /* Красивый заголовок */
    .main-title {
        text-align: center;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        padding: 10px;
    }

    /* Пузыри сообщений */
    .stChatMessage { border: none !important; padding: 10px !important; }
    div[data-testid="stChatMessageUser"] {
        background-color: #248bf5 !important;
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 15% !important;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #262626 !important;
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 15% !important;
    }
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

# 3. ЛОГИКА ПЕРСОНАЖЕЙ
if "persona" not in st.session_state:
    st.session_state.persona = "Ты — заботливый партнер. Общайся нежно и используй эмодзи."

with st.expander("⚙️ Выбор персонажа"):
    if settings_sheet:
        data = settings_sheet.get_all_records()
        if data:
            names = [r['Name'] for r in data]
            sel = st.selectbox("Кто сегодня с тобой?", names)
            curr = next(i for i in data if i["Name"] == sel)
            st.session_state.persona = f"Ты {curr['Name']}, возраст {curr['Age']}. {curr['Prompt']}. Общайся на 'ты', используй эмодзи."
            st.session_state.current_name = curr['Name']

# 4. ЗАГРУЗКА ИСТОРИИ ИЗ ТАБЛИЦЫ (Память)
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Если хочешь, чтобы он вспоминал старое, можно достать последние 5 строк из sheet здесь.

# Заголовок с именем персонажа
name_display = st.session_state.get('current_name', 'Companion')
st.markdown(f"<h3 class='main-title'>{name_display}</h3>", unsafe_allow_html=True)

# 5. ЧАТ
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Напиши мне что-нибудь..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        
        with st.chat_message("assistant"):
            st.markdown(ans)
            
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet:
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M"), 
                name_display, 
                prompt, 
                ans[:500]
            ])
    except Exception as e:
        st.error("Упс, я на секунду задумался. Попробуй еще раз!")
