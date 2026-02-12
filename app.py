import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА НА ФОТО ПАРТНЕРА
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

# 1. ДИЗАЙН (Montserrat + Full Clean)
st.set_page_config(page_title="Cipher", layout="centered")

st.markdown('<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.1) 0%, transparent 50%) !important;
        color: white !important;
    }
    
    /* ПОЛНОЕ УДАЛЕНИЕ FACE И ART */
    [data-testid="stAvatar"] { display: none !important; }
    div[data-testid="stChatMessage"] section div { font-size: 0 !important; }
    div[data-testid="stChatMessage"] section div * { font-size: 16px !important; }

    /* Кнопки */
    .stButton>button {
        width: 100% !important;
        background: transparent !important;
        border: 1px solid rgba(255, 75, 75, 0.4) !important;
        color: white !important;
        border-radius: 10px !important;
        height: 42px !important;
    }
    
    /* Мини-кнопка выхода */
    .exit-btn-col button {
        height: 30px !important;
        font-size: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Хедер чата */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        border-bottom: 1px solid rgba(255, 75, 75, 0.2);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. ПОДКЛЮЧЕНИЕ
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

st.markdown("<h2 style='text-align:center; color:#ff4b4b; letter-spacing:5px; margin-bottom:30px;'>JUAN AI</h2>", unsafe_allow_html=True)

# 3. ЛОГИКА ШАГОВ

# ШАГ 1: КТО ТЫ?
if st.session_state.app_state == "welcome":
    st.write("👤 **ШАГ 1: ВЫБЕРИ СЕБЯ**")
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    options = u_names + ["+ Создать новый профиль"]
    choice = st.selectbox("Твой аккаунт:", options)

    if choice == "+ Создать новый профиль":
        new_n = st.text_input("Как тебя называть?")
        new_b = st.text_area("О себе")
        if st.button("ЗАРЕГИСТРИРОВАТЬ"):
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

# ШАГ 2: ВЫБЕРИ ПАРТНЕРА
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center;'>Привет, <b>{st.session_state.u_name}</b>!</p>", unsafe_allow_html=True)
    st.write("🎯 **ШАГ 2: ВЫБЕРИ ПАРТНЕРА**")
    
    h_names = []
    if settings_sheet:
        try:
            heroes = settings_sheet.get_all_records()
            h_names = [h['Name'] for h in heroes]
        except: pass

    h_options = h_names + ["+ Создать нового партнера"]
    h_choice = st.selectbox("С кем на связь?", h_options)

    if h_choice == "+ Создать нового партнера":
        new_h_n = st.text_input("Имя партнера")
        new_h_p = st.text_area("Промпт (характер)")
        if st.button("СОЗДАТЬ И ВОЙТИ"):
            if new_h_n and settings_sheet:
                settings_sheet.append_row([new_h_n, new_h_p])
                st.session_state.persona = f"Ты {new_h_n}. {new_h_p}. Собеседник: {st.session_state.u_name}. Ты романтичный LGBT+ парень. Используй много эмодзи."
                st.session_state.current_name = new_h_n
                st.session_state.app_state = "chat"
                st.rerun()
    else:
        if st.button("ВЫБРАТЬ"):
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
    # КОМПАКТНЫЙ ХЕДЕР С ФОТО И КНОПКОЙ ВЫХОДА
    col_head, col_exit = st.columns([4, 1])
    
    with col_head:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="{AI_AVATAR}" style="width: 45px; height: 45px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
                <div style="text-align: left;">
                    <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                    <div style="color: #00ff00; font-size: 10px;">● В СЕТИ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_exit:
        st.markdown('<div class="exit-btn-col">', unsafe_allow_html=True)
        if st.button("ВЫЙТИ"):
            st.session_state.app_state = "welcome"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        icon = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]): st.markdown(f"**{icon}** {m['content']}")
    
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
