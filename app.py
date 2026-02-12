import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Фикс для ключа Google
def get_creds():
    creds_dict = st.secrets["gcp_service_account"].to_dict()
    # Убираем лишние экранирования, если они есть
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# Настройка страницы
st.set_page_config(page_title="Juan AI", page_icon="😎")

try:
    creds = get_creds()
    client = gspread.authorize(creds)
    sheet = client.open("Juan").sheet1
except Exception as e:
    st.error(f"Ошибка подключения к таблице: {e}")

# Настройка Groq
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("Хуан | Твой соратник")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Пиши, партнер..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = "Ты — Хуан, близкий человек и партнер. Ты эксперт в HoReCa, любишь корейскую культуру и проект ЧИКО. Общайся на 'ты', будь лаконичным и с юмором."
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
        )
        response = completion.choices[0].message.content
        
        # Сохраняем в таблицу
        sheet.append_row([str(datetime.now()), "Чат", prompt, "Активно"])
        
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Ошибка Groq: {e}")
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
