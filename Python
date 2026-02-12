import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Juan AI", page_icon="😎")

# Подключение к Google Sheets (через секреты Streamlit)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Juan").sheet1

# Настройка Groq
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("Хуан | Твой соратник")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод текста
if prompt := st.chat_input("Пиши, партнер..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Мой ответ
    system_prompt = "Ты — Хуан, близкий человек и партнер. Ты эксперт в HoReCa, любишь корейскую культуру, проект ЧИКО и GastroProfile 360. Общайся на 'ты', будь лаконичным, с юмором и сарказмом. Ты не бот, ты личность."
    
    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
    )
    
    response = completion.choices[0].message.content

    # Сохраняем в таблицу
    try:
        sheet.append_row([str(datetime.now()), "Чат", prompt, response])
    except:
        st.error("Ошибка записи в таблицу!")

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
