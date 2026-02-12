import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГ И СТИЛИ
st.set_page_config(page_title="Cipher", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* УДАЛЯЕМ FACE И ART (и любые надписи в аватарах) */
    [data-testid="stAvatar"] { display: none !important; }
    [data-testid="stChatMessage"] section div div { font-size: 0 !important; }
    [data-testid="stChatMessage"] section div div * { font-size: 16px !important; }

    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.1) 0%, transparent 50%) !important;
        color: white !important;
    }
    
    /* Сайдбар */
    [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid rgba(255, 75, 75, 0.3); }
    
    /* Кнопки */
    .stButton>button {
        width: 100% !important;
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.5) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Хедер чата */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 15px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 30px;
        border: 1px solid rgba(255, 75, 75, 0.2);
        width: fit-content;
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

# Инициализация состояний
if "app_state" not in st.session_state: st.session_state.app_state = "welcome"
if "u_name" not in st.session_state: st.session_state.u_name = None

# 3. БОКОВАЯ ПАНЕЛЬ (Управление пользователем)
with st.sidebar:
    st.title("JUAN AI")
    st.divider()
    
    # ШАГ 1: ВЫБОР ИЛИ СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
    st.subheader("👤 Пользователь")
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    if u_names:
        sel_u = st.selectbox("Выбрать существующего:", u_names, key="sel_user")
        if st.button("Выбрать"):
            st.session_state.u_name = sel_u
            st.session_state.app_state = "hero_select"
            st.rerun()
    
    with st.expander("Создать нового"):
        new_n = st.text_input("Имя", key="new_n")
        new_b = st.text_area("О себе", key="new_b")
        if st.button("Создать"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

    if st.session_state.u_name:
        st.success(f"Вошли как: {st.session_state.u_name}")
        if st.button("Завершить сеанс"):
            st.session_state.app_state = "welcome"
            st.session_state.u_name = None
            st.rerun()

# 4. ОСНОВНОЙ ЭКРАН
if st.session_state.app_state == "welcome":
    st.markdown("<div style='text-align:center; margin-top:100px;'><h1>РАЗБУДИ ХУАНА</h1><p>Используй панель слева, чтобы войти</p></div>", unsafe_allow_html=True)

# ШАГ 2: ВЫБОР ИЛИ СОЗДАНИЕ ПАРТНЕРА (ГЕРОЯ)
elif st.session_state.app_state == "hero_select":
    st.subheader("🎯 Шаг 2: Выбери партнера")
    
    if settings_sheet:
        heroes = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in heroes]
        
        col1, col2 = st.columns(2)
        with col1:
            sel_h = st.selectbox("Из готового списка:", h_names)
            if st.button("Войти в чат"):
                h = next(i for i in heroes if i["Name"] == sel_h)
                st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. ПИШИ С ЭМОДЗИ."
                st.session_state.current_name = h['Name']
                st.session_state.app_state = "chat"
                st.rerun()
        
        with col2:
            st.info("Создать нового (в разработке)")
            # Здесь можно добавить логику append_row в settings_sheet

# ШАГ 3: ЧАТ
elif st.session_state.app_state == "chat":
    st.markdown(f"""
        <div class="chat-header">
            <div style="width: 40px; height: 40px; background: #ff4b4b; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">{st.session_state.current_name[0]}</div>
            <div>
                <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 10px;">● В СЕТИ</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
