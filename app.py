import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА НА ФОТО
USER_PHOTO = "https://cdn.midjourney.com/u/3e5aa158-179e-48aa-88b0-bbef6bb9e7a0/0e909883da6dc88b440ea65fc9c9249352270c36a3b71af9f7744cf2b3d43381.png"

# 1. ДИЗАЙН И ЖЕСТКАЯ ЗАЧИСТКА
st.set_page_config(page_title="Cipher", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* УНИЧТОЖАЕМ FACE И ART */
    [data-testid="stChatMessage"] [data-testid="stAvatar"] {
        display: none !important;
    }
    /* Убираем текст-заменитель, если он всё ещё лезет */
    div[data-testid="stChatMessage"] section {
        font-size: 0 !important;
    }
    div[data-testid="stChatMessage"] section * {
        font-size: 16px !important;
    }

    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.1) 0%, transparent 50%) !important;
        color: white !important;
    }
    
    /* Стили боковой панели */
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
        border-right: 1px solid rgba(255, 75, 75, 0.3);
    }

    .chat-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 50px;
        border: 1px solid rgba(255, 75, 75, 0.2);
        margin-bottom: 25px;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }
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

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. БОКОВАЯ ПАНЕЛЬ (Она должна быть видна ВСЕГДА)
with st.sidebar:
    st.markdown("<h1 style='color:#ff4b4b; font-size:24px;'>JUAN CONTROL</h1>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("👤 Твой профиль")
    
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    if u_names:
        sel_u = st.selectbox("Войти как:", u_names, key="side_login")
        if st.button("ПОДТВЕРДИТЬ ВХОД"):
            st.session_state.u_name = sel_u
            st.session_state.app_state = "hero_select"
            st.rerun()
    
    with st.expander("➕ Создать профиль"):
        new_n = st.text_input("Имя", key="new_n")
        new_b = st.text_area("О себе", key="new_b")
        if st.button("ЗАРЕГИСТРИРОВАТЬ"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

    if st.session_state.app_state in ["chat", "hero_select"]:
        st.divider()
        if st.button("🔚 ВЕРНУТЬСЯ В МЕНЮ"):
            st.session_state.app_state = "welcome"
            st.rerun()

# 4. ЦЕНТРАЛЬНАЯ ЧАСТЬ
if st.session_state.app_state == "welcome":
    st.markdown("""
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='color:#ff4b4b; letter-spacing:10px;'>JUAN AI</h1>
            <p style='opacity:0.5;'>Раскрой панель слева, чтобы начать</p>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.app_state == "hero_select":
    st.markdown(f"### Привет, {st.session_state.u_name}!")
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        sel_h = st.selectbox("С кем хочешь пообщаться?", [h['Name'] for h in h_data])
        if st.button("УСТАНОВИТЬ СОЕДИНЕНИЕ"):
            h = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. Обязательно используй эмодзи! ✨"
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    # Компактный заголовок с фото Мигеля
    st.markdown(f"""
        <div class="chat-header">
            <img src="{USER_PHOTO}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 18px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 10px;">● ONLINE</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        icon = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]):
            st.markdown(f"**{icon}** {m['content']}")
    
    if p := st.chat_input("Напиши что-нибудь..."):
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
