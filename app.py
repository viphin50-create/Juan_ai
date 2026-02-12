import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА НА ФОТО (Midjourney)
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

# 1. ДИЗАЙН (Адаптация под Telegram Mini App)
st.set_page_config(page_title="Cipher", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* ШРИФТЫ И ЦВЕТА */
    html, body, [class*="st-"] { 
        font-family: 'Montserrat', sans-serif !important; 
        font-size: 14px !important; 
    }
    .stApp {
        background-color: #0a0a0a !important;
        color: #ffffff !important;
    }

    /* УБИРАЕМ FACE/ART И ЛИШНИЕ ОТСТУПЫ */
    [data-testid="stAvatar"] { display: none !important; }
    div[data-testid="stChatMessage"] { 
        padding: 8px !important; 
        margin: 5px 0 !important;
        border-radius: 10px !important;
    }
    /* Прячем текст-заглушку в аватарах */
    div[data-testid="stChatMessage"] section div { font-size: 0 !important; }
    div[data-testid="stChatMessage"] section div * { font-size: 14px !important; }

    /* КНОПКИ (Компактность) */
    .stButton>button {
        width: 100% !important;
        background: rgba(255, 75, 75, 0.15) !important;
        border: 1px solid #ff4b4b !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        height: 38px !important;
        font-size: 12px !important;
        border-radius: 10px !important;
    }

    /* ХЕДЕР ЧАТА (Компактный) */
    .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 75, 75, 0.3);
    }
    
    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #00ff00;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
        box-shadow: 0 0 5px #00ff00;
    }

    /* ИНПУТ ЧАТА */
    .stChatInputContainer { padding-bottom: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ К БД
@st.cache_resource
def init_db():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds).open("Juan")
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except: return None, None, None

sheet, settings_sheet, users_sheet = init_db()
gro_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state: st.session_state.app_state = "welcome"
if "u_name" not in st.session_state: st.session_state.u_name = None

# 3. ЛОГИКА
st.markdown("<h3 style='text-align:center; color:#ff4b4b; letter-spacing:3px; margin:0;'>JUAN AI</h3>", unsafe_allow_html=True)

# ШАГ 1: ПОЛЬЗОВАТЕЛЬ
if st.session_state.app_state == "welcome":
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    options = u_names + ["+ Новый профиль"]
    choice = st.selectbox("👤 Кто в сети?", options)

    if choice == "+ Новый профиль":
        new_n = st.text_input("Имя")
        new_b = st.text_area("О себе")
        if st.button("СОЗДАТЬ"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()
    else:
        if st.button("ВЫБРАТЬ"):
            st.session_state.u_name = choice
            st.session_state.app_state = "hero_select"
            st.rerun()

# ШАГ 2: ПАРТНЕР
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center; font-size:12px;'>Привет, {st.session_state.u_name}</p>", unsafe_allow_html=True)
    
    h_names = []
    if settings_sheet:
        try:
            heroes = settings_sheet.get_all_records()
            h_names = [h['Name'] for h in heroes]
        except: pass

    h_choice = st.selectbox("🎯 С кем на связь?", h_names + ["+ Новый партнер"])

    if h_choice == "+ Новый партнер":
        new_h_n = st.text_input("Имя партнера")
        new_h_p = st.text_area("Характер")
        if st.button("СОЗДАТЬ И ВОЙТИ"):
            if new_h_n and settings_sheet:
                settings_sheet.append_row([new_h_n, new_h_p])
                st.session_state.persona = f"Ты {new_h_n}. {new_h_p}. Собеседник: {st.session_state.u_name}. Романтика, LGBT+, эмодзи."
                st.session_state.current_name = new_h_n
                st.session_state.app_state = "chat"
                st.rerun()
    else:
        if st.button("НАЧАТЬ ЧАТ"):
            h = next(i for i in heroes if i["Name"] == h_choice)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. Романтика, LGBT+, эмодзи."
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()
    
    if st.button("⬅ Назад"):
        st.session_state.app_state = "welcome"
        st.rerun()

# ШАГ 3: ЧАТ
elif st.session_state.app_state == "chat":
    # КОМПАКТНЫЙ ХЕДЕР
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="{AI_AVATAR}" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
                <div style="line-height: 1;">
                    <div style="color: #ff4b4b; font-size: 14px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                    <div style="font-size: 9px; color: #00ff00;"><span class="status-dot"></span>В СЕТИ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("ВЫЙТИ"):
            st.session_state.app_state = "welcome"
            st.rerun()

    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Чат с иконками
    for m in st.session_state.messages:
        icon = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]):
            st.markdown(f"**{icon}** {m['content']}")
    
    if p := st.chat_input("Напиши сообщение..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(f"**👤** {p}")
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(f"**✨** {ans}")
        st.session_state.messages.append({"role": "assistant", "content": ans})
        if sheet:
            try: sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])
            except: pass
