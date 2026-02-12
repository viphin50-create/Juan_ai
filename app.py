import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. СТИЛЬ И МОБИЛЬНАЯ ВЕРСТКА
st.set_page_config(page_title="AI Companion", page_icon="🎭", layout="centered")

st.markdown("""
    <style>
    /* Скрываем всё лишнее */
    header, footer, #MainMenu {visibility: hidden !important;}
    
    .stApp { background-color: #0E1117; }
    
    /* Контейнер настроек сверху */
    .setting-box {
        background-color: #1A1C23;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #30363D;
    }
    
    /* Пузыри чата */
    .stChatMessage { border-radius: 18px !important; margin-bottom: 10px !important; }
    div[data-testid="stChatMessageUser"] {
        background-color: #0088CC !important;
        color: white !important;
        border-bottom-right-radius: 2px !important;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #21262D !important;
        color: white !important;
        border-bottom-left-radius: 2px !important;
    }
    
    /* Исправляем белый текст */
    .stMarkdown p { color: #E6EDF3 !important; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. УЛУЧШЕННЫЙ ЖИВОЙ ГОЛОС (JS)
def speak_text(text):
    if text:
        # Улучшенный скрипт: выбирает премиальный мужской голос, если он есть в системе
        js_code = f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance();
        msg.text = "{text.replace('"', "'")}";
        msg.lang = 'ru-RU';
        msg.rate = 1.0;
        msg.pitch = 0.9; // Чуть ниже тон для мужественности
        
        var voices = window.speechSynthesis.getVoices();
        // Пытаемся найти более живой голос (например, Google Russian или Microsoft Pavel)
        for(var i = 0; i < voices.length; i++) {{
            if(voices[i].name.includes('Google') || voices[i].name.includes('Male')) {{
                msg.voice = voices[i];
                break;
            }}
        }}
        window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(js_code, height=0)

# 3. ПОДКЛЮЧЕНИЕ ТАБЛИЦЫ
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

# 4. ВЕРХНЯЯ ПАНЕЛЬ НАСТРОЕК (Вместо сайдбара)
with st.expander("👤 Настроить партнера", expanded=False):
    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        
        col1, col2 = st.columns(2)
        with col1:
            mode = st.selectbox("Режим", ["Выбор", "Создание"])
        
        if mode == "Выбор" and names:
            sel = st.selectbox("Кто сегодня с тобой?", names)
            curr = next(i for i in data if i["Name"] == sel)
            st.session_state.persona = f"Ты {curr['Name']}, возраст {curr['Age']}. {curr['Prompt']}"
            st.info(f"Активен: {sel}")
        else:
            n = st.text_input("Имя")
            a = st.number_input("Возраст", 18, 99, 25)
            b = st.text_area("Характер (био)")
            if st.button("✅ Сохранить личность"):
                settings_sheet.append_row([n, b, a])
                st.success("Готово! Переключись на 'Выбор'")

# 5. ЧАТ
if "messages" not in st.session_state:
    st.session_state.messages = []
if "persona" not in st.session_state:
    st.session_state.persona = "Ты — Хуан, партнер."

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Напиши мне..."):
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
            speak_text(ans)
            
        st.session_state.messages.append({"role": "assistant", "content": ans})
        if sheet: sheet.append_row([datetime.now().strftime("%H:%M"), "Chat", prompt, ans[:100]])
    except Exception as e:
        st.error(f"Ошибка: {e}")
