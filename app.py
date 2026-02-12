import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. СТИЛЬ
st.set_page_config(page_title="Companion", page_icon="🤍", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #0E1117; }
    .chat-header { text-align: center; padding: 10px; border-bottom: 1px solid #30363D; color: white; }
    div[data-testid="stChatMessageUser"] { background-color: #0088CC !important; border-radius: 15px 15px 2px 15px !important; margin-left: 20% !important; }
    div[data-testid="stChatMessageAssistant"] { background-color: #21262D !important; border-radius: 15px 15px 15px 2px !important; margin-right: 20% !important; }
    div[data-testid="stChatMessageUser"] img, div[data-testid="stChatMessageAssistant"] img { display: none; }
    .stMarkdown p { color: #E6EDF3 !important; }
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
    except Exception as e:
        st.error(f"Ошибка базы: {e}")
        return None, None

sheet, settings_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. НАСТРОЙКИ
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.expander("👤 Настройки", expanded=False):
    u_info = st.text_area("О тебе:", value=st.session_state.get('u_info', 'Подруга'), key="u_info_input")
    st.session_state.u_info = u_info
    
    if settings_sheet:
        data = settings_sheet.get_all_records()
        names = [r['Name'] for r in data]
        if names:
            sel = st.selectbox("Партнер:", names)
            curr = next(i for i in data if i["Name"] == sel)
            st.session_state.persona = f"Ты {curr['Name']}. {curr['Prompt']}. Собеседник: {st.session_state.u_info}. ПРАВИЛА: Используй ЭМОДЗИ, не пиши действия в скобках."
            st.session_state.current_name = curr['Name']

# 4. ЧАТ
name_display = st.session_state.get('current_name', 'Companion')
st.markdown(f"<div class='chat-header'><h3>{name_display}</h3></div>", unsafe_allow_html=True)

for m in st.session_state.messages:
    av = "👤" if m["role"] == "user" else "✨"
    with st.chat_message(m["role"], avatar=av):
        st.markdown(m["content"])

if prompt := st.chat_input("Напиши мне..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        p = st.session_state.get('persona', "Будь собой, используй эмодзи.")
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": p}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        if sheet:
            sheet.append_row([datetime.now().strftime("%d.%m %H:%M"), name_display, prompt, ans[:200]])
    except Exception as e:
        st.error("Минутку, я перезагружаю мысли...")
