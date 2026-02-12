import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. Настройка стиля (CSS)
st.set_page_config(page_title="Juan AI", page_icon="🤍", layout="centered")

st.markdown("""
    <style>
    /* Скрываем лишние элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Делаем фон страницы приятнее */
    .stApp {
        background-color: #f5f7f9;
    }
    
    /* Стили для поля ввода */
    .stChatInputContainer {
        padding-bottom: 20px;
    }

    /* Настройка шрифтов */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Инициализация (твой старый код)
def init_google_sheet():
    try:
        info = st.secrets["gcp_service_account"]
        creds_dict = {
            "type": info["type"],
            "project_id": info["project_id"],
            "private_key_id": info["private_key_id"],
            "private_key": info["private_key"].replace("\\n", "\n"),
            "client_email": info["client_email"],
            "client_id": info["client_id"],
            "auth_uri": info["auth_uri"],
            "token_uri": info["token_uri"],
            "auth_provider_x509_cert_url": info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": info["client_x509_cert_url"]
        }
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client
    except:
        return None, None

sheet, full_client = init_google_sheet()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_persona():
    try:
        settings_sheet = full_client.worksheet("Settings")
        return settings_sheet.acell('A1').value
    except:
        return "Ты — Хуан, партнер. Лаконичен, саркастичен, на 'ты'."

current_persona = get_persona()

# Заголовок без лишних рамок
st.markdown(f"<h2 style='text-align: center; color: #333;'>{current_persona.split(',')[0].replace('Ты — ', '')}</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод
if prompt := st.chat_input("Напиши мне..."):
    if prompt.lower().startswith("настройка:"):
        new_persona = prompt[10:].strip()
        try:
            settings_sheet = full_client.worksheet("Settings")
            settings_sheet.update_acell('A1', new_persona)
            st.success("Личность обновлена!")
            st.rerun()
        except:
            st.error("Создай лист Settings в таблице!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            chat_completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": current_persona}] + st.session_state.messages
            )
            response = chat_completion.choices[0].message.content
            
            if sheet:
                sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), "Web", prompt, "OK", response[:200]])

            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Ошибка: {e}")
