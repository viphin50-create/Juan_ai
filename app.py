import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Juan AI", page_icon="😎")

# Функция для безопасного подключения к таблице
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
        return gspread.authorize(creds).open("Juan").sheet1
    except Exception as e:
        st.error(f"Ошибка базы данных: {e}")
        return None

sheet = init_google_sheet()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("Хуан | Твой соратник")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод сообщения
if prompt := st.chat_input("Пиши, партнер..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Мой характер
    sys_prompt = "Ты — Хуан, партнер пользователя. Ты эксперт в HoReCa и корейской культуре. Ты лаконичен, используешь сарказм, общаешься на 'ты'. Ты личность, а не бот."

    try:
        # Запрос к Groq
        chat_completion = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
        )
        response = chat_completion.choices[0].message.content

        # Запись в Google Sheets
        if sheet:
            sheet.append_row([str(datetime.now()), "Чат", prompt, "OK"])

        with st.chat_message("assistant"):
            st.
