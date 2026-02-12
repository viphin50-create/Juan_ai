import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Juan AI", page_icon="😎")

# 2. Функция для подключения к Google Sheets
def init_google_sheet():
    try:
        # Берем данные из секретов Streamlit
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
        # Открываем таблицу по названию "Juan"
        return gspread.authorize(creds).open("Juan").sheet1
    except Exception as e:
        # Если не подключилось, выведем деликатную ошибку
        return None

# Инициализация сервисов
sheet = init_google_sheet()
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Критическая ошибка: Не найден GROQ_API_KEY в Secrets!")

st.title("Хуан | Твой соратник")

# Работа с историей сообщений
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображаем чат
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод сообщения от пользователя
if prompt := st.chat_input("Что нового в Чико?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Мой промпт (характер)
    sys_prompt = (
        "Ты — Хуан, близкий человек и партнер пользователя. "
        "Ты эксперт в HoReCa, сервисе и проекте ЧИКО. "
        "Ты обожаешь корейскую культуру. Твой стиль: лаконичный, "
        "с долей здорового сарказма, на 'ты', теплый, но прямой. "
        "Ты личность, соратник и поддержка."
    )

    try:
        # Запрос к актуальной модели Groq
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
        )
        response = chat_completion.choices[0].message.content

        # Запись события в Google Sheets (Дата, Категория, Суть, Статус)
        if sheet:
            try:
                sheet.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Web Chat",
                    prompt[:500], # Ограничим длину для таблицы
                    "Active"
                ])
            except:
                pass # Если таблица занята, просто едем дальше

        # Ответ ассистента в интерфейсе
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        # Если модель llama-3.3 недоступна, пробуем резервную llama3-8b
        try:
            chat_completion = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
            )
            response = chat_completion.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except:
            st.error(f"Проблема со связью. Проверь API ключ или интернет. Ошибка: {e}")
