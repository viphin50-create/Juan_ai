import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ТОТАЛЬНЫЙ ДИЗАЙН: НЕОНОВЫЙ ХУАН
st.set_page_config(page_title="Cipher", page_icon="💡", layout="centered")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
    /* Скрытие мусора */
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}

    /* Глобальные шрифты и фон */
    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif !important;
        color: white !important;
    }

    .stApp {
        background: #0a0a0a;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.12) 0%, transparent 40%),
            radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.03) 0%, transparent 40%);
    }

    /* Анимация неоновых волн */
    .stApp::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            rgba(255, 0, 0, 0.02) 100px,
            rgba(255, 0, 0, 0.02) 200px
        );
        animation: move 20s linear infinite;
        z-index: -1;
    }

    @keyframes move {
        from { transform: translate(0, 0); }
        to { transform: translate(100px, 100px); }
    }

    /* Экраны и карточки */
    .welcome-card {
        background: rgba(36, 47, 61, 0.4);
        backdrop-filter: blur(15px);
        padding: 25px 20px;
        border-radius: 20px;
        border: 1px solid rgba(255, 0, 0, 0.15);
        text-align: center;
        margin-bottom: 20px;
    }

    /* Заголовки и текст */
    h1 { font-size: 32px !important; font-weight: 600 !important; }
    h2 { font-size: 18px !important; font-weight: 300 !important; color: #84919b !important; }
    h3 { font-size: 16px !important; margin-bottom: 10px !important; }

    /* Кнопки */
    .stButton>button {
        width: 100%;
        background: transparent !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 12px;
        padding: 8px 15px;
        font-size: 14px !important;
        font-weight: 400 !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: rgba(255, 75, 75, 0.2) !important;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.3);
    }

    /* Чат и баблы */
    div[data-testid="stChatMessage"] {
        padding: 8px 12px !important;
        background-color: transparent !important;
    }

    div[data-testid="stChatMessageUser"] {
        background: rgba(43, 82, 120, 0.6) !important;
        border-radius: 15px 15px 2px 15px !important;
        border: none !important;
        margin-left: 10% !important;
    }

    div[data-testid="stChatMessageAssistant"] {
        background: rgba(28, 39, 50, 0.7) !important;
        border-radius: 15px 15px 15px 2px !important;
        border: 0.5px solid rgba(255, 0, 0, 0.15) !important;
        margin-right: 10% !important;
    }

    .stMarkdown p {
        font-size: 14px !important;
        font-weight: 300 !important;
        line-height: 1.5 !important;
        color: #f0f0f0 !important;
    }

    /* Поле ввода */
    .stChatInputContainer {
        padding: 15px !important;
        background-color: transparent !important;
    }
    .stChatInput textarea {
        background: rgba(30, 30, 30, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        color: white !important;
        font-size: 14px !important;
    }

    /* Скрытие аватарок */
    div[data-testid="stAvatar"] { display: none !important; }
    
    /* Табы выбора */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #84919b; font-size: 13px; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #ff4b4b; }
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
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except:
        return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЭКРАН 1: ПРИВЕТСТВИЕ
if st.session_state.app_state == "welcome":
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='welcome-card'>
            <h1 style='margin-bottom: 5px;'>👤</h1>
            <h1>ХУАН</h1>
            <h2>Теневой доступ активирован</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("АКТИВИРОВАТЬ СВЯЗЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

# 4. ЭКРАН 2: ВЫБОР ПОЛЬЗОВАТЕЛЯ (КТО ТЫ)
elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>Идентификация</h3></div>", unsafe_allow_html=True)
    
    if users_sheet:
        u_data = users_sheet.get_all_records()
        u_names = [u['Name'] for u in u_data]
        
        t1, t2 = st.tabs(["Вход", "Регистрация"])
        with t1:
            if u_names:
                sel_u = st.selectbox("Выбери свой профиль:", u_names)
                if st.button("Подтвердить"):
                    curr = next(i for i in u_data if i["Name"] == sel_u)
                    st.session_state.u_name = curr['Name']
                    st.session_state.u_bio = curr['Bio']
                    st.session_state.app_state = "hero_select"
                    st.rerun()
            else: st.info("Профилей пока нет")
        with t2:
            new_un = st.text_input("Твой ник")
            new_ub = st.text_area("О тебе (факты, вайб)")
            if st.button("Создать профиль"):
                if new_un:
                    users_sheet.append_row([new_un, new_ub])
                    st.success("Профиль создан! Войди через вкладку 'Вход'")

# 5. ЭКРАН 3: ВЫБОР ГЕРОЯ (ПАРТНЕРА)
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>Привет, {st.session_state.u_name}</h3><p>С кем хочешь поговорить?</p></div>", unsafe_allow_html=True)
    
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in h_data]
        
        ht1, ht2 = st.tabs(["Выбрать", "Создать"])
        with ht1:
            sel_h = st.selectbox("Партнер:", h_names)
            if st.button("Начать диалог"):
                h_curr = next(i for i in h_data if i["Name"] == sel_h)
                st.session_state.persona = (
                    f"Ты {h_curr['Name']}. {h_curr['Prompt']}. "
                    f"Твой собеседник: {st.session_state.u_name} ({st.session_state.u_bio}). "
                    "ПРАВИЛА: Используй эмодзи. Считывай эмодзи собеседника. Не пиши действия в скобках."
                )
                st.session_state.current_name = h_curr['Name']
                st.session_state.app_state = "chat"
                st.rerun()
        with ht2:
            nh = st.text_input("Имя нового героя")
            nb = st.text_area("Его биография и стиль")
            if st.button("Добавить"):
                settings_sheet.append_row([nh, nb, 25])
                st.success("Герой добавлен!")

# 6. ЭКРАН 4: ЧАТ
elif st.session_state.app_state == "chat":
    h_name = st.session_state.get('current_name', 'Партнер')
    st.markdown(f"<div style='text-align: center; color: white; border-bottom: 0.5px solid rgba(255,0,0,0.2); padding-bottom: 10px; font-size: 14px; letter-spacing: 1px;'><b>{h_name.upper()}</b></div>", unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []

    # Рендеринг чата
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Написать Хуану..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        try:
            res = gro_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
            )
            ans = res.choices[0].message.content
            with st.chat_message("assistant"): st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            if sheet: sheet.append_row([datetime.now().strftime("%H:%M"), h_name, prompt, ans[:200]])
        except:
            st.error("Потеря связи с теневым узлом...")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ ВЫЙТИ"):
        st.session_state.app_state = "welcome"
        st.rerun()
