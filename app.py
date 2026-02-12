import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="AI Companion", page_icon="🎭", layout="centered")

# 2. ДИЗАЙН (CSS) - Телефонный стиль
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp { background-color: #121212; color: #FFFFFF; }
    
    /* Стили сообщений */
    .stChatMessage {
        border-radius: 20px;
        padding: 10px;
        margin-bottom: 10px;
        max-width: 85%;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #0088cc !important;
        margin-left: auto;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #2b2b2b !important;
        margin-right: auto;
    }
    
    /* Скрытие лишнего белого фона вокруг текста */
    .stMarkdown p { color: white !important; font-size: 16px; }
    
    /* Кастомная кнопка настройки */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background-color: #1f1f1f;
        color: white;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# Функция для озвучки (JavaScript)
def speak_text(text):
    if text:
        js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance();
        msg.text = "{text.replace('"', "'")}";
        msg.lang = 'ru-RU';
        msg.rate = 1.0;
        window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(js_code, height=0)

# 3. ИНИЦИАЛИЗАЦИЯ БАЗЫ
def init_db():
    try:
        info = st.secrets["gcp_service_account"]
        creds_dict = {
            "type": info["type"], "project_id": info["project_id"],
            "private_key_id": info["private_key_id"], "private_key": info["private_key"].replace("\\n", "\n"),
            "client_email": info["client_email"], "client_id": info["client_id"],
            "auth_uri": info["auth_uri"], "token_uri": info["token_uri"],
            "auth_provider_x509_cert_url": info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": info["client_x509_cert_url"]
        }
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client.worksheet("Settings")
    except:
        return None, None

log_sheet, settings_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. МЕНЮ НАСТРОЕК (В САЙДБАРЕ)
with st.sidebar:
    st.title("⚙️ Настройки")
    
    if settings_sheet:
        all_data = settings_sheet.get_all_records()
        names = [row['Name'] for row in all_data] if all_data else []
        
        mode = st.radio("Режим", ["Выбрать партнера", "Создать нового"])
        
        if mode == "Выбрать партнера" and names:
            selected_name = st.selectbox("Твой выбор:", names)
            current_p = next(item for item in all_data if item["Name"] == selected_name)
            st.session_state.persona = f"Ты {current_p['Name']}, возраст {current_p['Age']}. Твоя биография: {current_p['Prompt']}. Общайся в этом стиле."
            st.success(f"Активен: {selected_name}")
            
        elif mode == "Создать нового":
            new_name = st.text_input("Имя")
            new_age = st.number_input("Возраст", 18, 99, 25)
            new_bio = st.text_area("Биография/Характер")
            if st.button("Создать и Обучить"):
                settings_sheet.append_row([new_name, new_bio, new_age])
                st.success("Персонаж создан! Переключись в 'Выбрать партнера'")

# 5. ОСНОВНОЙ ЧАТ
if "persona" not in st.session_state:
    st.session_state.persona = "Ты — Хуан, лаконичный партнер."

if "messages" not in st.session_state:
    st.session_state.messages = []

# Приветствие
if not st.session_state.messages:
    with st.chat_message("assistant"):
        msg = "Привет! Я готов. Настрой меня в меню слева или просто начнем общение."
        st.markdown(msg)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Сообщение..."):
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
            speak_text(ans) # Озвучка
            
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if log_sheet:
            log_sheet.append_row([datetime.now().strftime("%H:%M"), "Chat", prompt, ans[:100]])
    except Exception as e:
        st.error(f"Ошибка: {e}")
