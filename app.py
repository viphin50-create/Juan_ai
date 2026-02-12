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
        width: 100%; border-radius: 12px; background-color: #248bf5;
        color: white; border: none; padding: 12px; font-weight: bold;
    }

    .welcome-card {
        background-color: #242f3d; padding: 25px; border-radius: 20px;
        text-align: center; margin-top: 30px; border: 1px solid #2d3947;
    }

    div[data-testid="stChatMessageUser"] {
        background-color: #2b5278 !important; border-radius: 15px 15px 2px 15px !important;
        margin-left: 15% !important; border: none !important;
    }
    div[data-testid="stChatMessageAssistant"] {
        background-color: #242f3d !important; border-radius: 15px 15px 15px 2px !important;
        margin-right: 15% !important; border: none !important;
    }
    div[data-testid="stChatMessageUser"] [data-testid="stAvatar"],
    div[data-testid="stChatMessageAssistant"] [data-testid="stAvatar"] { display: none !important; }
    
    .stMarkdown p { color: #ffffff !important; font-size: 16px; }
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
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except: return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЭКРАН 1: ПРИВЕТСТВИЕ
if st.session_state.app_state == "welcome":
    st.markdown("<div class='welcome-card'><h1 style='font-size: 50px;'>🎭</h1><h2 style='color: white;'>Secret Messenger</h2></div>", unsafe_allow_html=True)
    if st.button("Войти"):
        st.session_state.app_state = "user_select"
        st.rerun()

# 4. ЭКРАН 2: КТО ТЫ? (ПОЛЬЗОВАТЕЛЬ)
elif st.session_state.app_state == "user_select":
    st.markdown("<h3 style='text-align: center; color: white;'>Кто заходит в чат?</h3>", unsafe_allow_html=True)
    
    if users_sheet:
        users_data = users_sheet.get_all_records()
        user_names = [u['Name'] for u in users_data]
        
        u_tab1, u_tab2 = st.tabs(["Я уже есть в списке", "Создать новый профиль"])
        
        with u_tab1:
            if user_names:
                selected_user = st.selectbox("Выбери себя:", user_names)
                if st.button("Это я"):
                    u_curr = next(i for i in users_data if i["Name"] == selected_user)
                    st.session_state.u_name = u_curr['Name']
                    st.session_state.u_bio = u_curr['Bio']
                    st.session_state.app_state = "hero_select"
                    st.rerun()
            else: st.info("Пользователей пока нет. Создай профиль!")

        with u_tab2:
            new_u_name = st.text_input("Твое имя (ник)")
            new_u_bio = st.text_area("О тебе (интересы, характер)")
            if st.button("Запомнить меня"):
                users_sheet.append_row([new_u_name, new_u_bio])
                st.success("Профиль создан! Выбери его во вкладке слева.")

# 5. ЭКРАН 3: С КЕМ ГОВОРИМ? (ГЕРОЙ)
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<h4 style='text-align: center; color: #84919b;'>Привет, {st.session_state.u_name}!</h4>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white;'>С кем хочешь пообщаться?</h3>", unsafe_allow_html=True)
    
    if settings_sheet:
        heroes_data = settings_sheet.get_all_records()
        hero_names = [r['Name'] for r in heroes_data]
        
        h_tab1, h_tab2 = st.tabs(["Выбрать героя", "Создать нового"])
        
        with h_tab1:
            if hero_names:
                sel_h = st.selectbox("Партнер:", hero_names)
                if st.button("Начать чат"):
                    h_curr = next(i for i in heroes_data if i["Name"] == sel_h)
                    st.session_state.persona = (
                        f"Ты {h_curr['Name']}. {h_curr['Prompt']}. "
                        f"Собеседник: {st.session_state.u_name} ({st.session_state.u_bio}). "
                        "ПРАВИЛА: Общайся на 'ты', используй эмодзи, считывай вайб эмодзи собеседника."
                    )
                    st.session_state.current_name = h_curr['Name']
                    st.session_state.app_state = "chat"
                    st.rerun()

        with h_tab2:
            new_h_name = st.text_input("Имя героя")
            new_h_bio = st.text_area("Его биография и вайб")
            if st.button("Создать героя"):
                settings_sheet.append_row([new_h_name, new_h_bio, 25])
                st.success("Герой готов!")

# 6. ЭКРАН 4: ЧАТ
elif st.session_state.app_state == "chat":
    hero = st.session_state.get('current_name', 'Companion')
    st.markdown(f"<div style='text-align: center; padding: 10px; border-bottom: 1px solid #2d3947; color: white;'><b>{hero}</b></div>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Напиши мне..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet: sheet.append_row([datetime.now().strftime("%H:%M"), hero, prompt, ans[:200]])

    if st.button("⬅️ Сменить обстановку"):
        st.session_state.app_state = "user_select"
        st.rerun()
