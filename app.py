import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА (надежная из Midjourney)
USER_PHOTO = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

# 1. ДИЗАЙН
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
    /* ЖЕСТКАЯ ЗАЧИСТКА FACE И ART */
    div[data-testid="stChatMessage"] [data-testid="stAvatar"] { display: none !important; }
    div[data-testid="stChatMessage"] { padding-left: 0 !important; margin-left: 0 !important; }
    div[data-testid="stChatMessage"] p { font-size: 16px !important; }
    
    /* Стилизация бабблов, чтобы скрыть текст-заменитель */
    .stChatMessage { background-color: transparent !important; border: none !important; }

    .welcome-card {
        background: rgba(36, 47, 61, 0.2);
        backdrop-filter: blur(20px);
        padding: 25px;
        border-radius: 25px;
        border: 1px solid rgba(255, 75, 75, 0.3);
        text-align: center;
        margin-top: 30px;
    }
    .stButton>button {
        width: 100%;
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 12px;
    }
    
    /* Компактный хедер */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 50px;
        border: 1px solid rgba(255, 75, 75, 0.2);
        margin-bottom: 20px;
        width: fit-content;
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

if "app_state" not in st.session_state:
    st.session_state.app_state = "welcome"

# 3. ЛОГИКА
if st.session_state.app_state == "welcome":
    st.markdown("<div class='welcome-card'><h1 style='color:#ff4b4b;'>JUAN AI</h1><p>Система ждет...</p></div>", unsafe_allow_html=True)
    if st.button("РАЗБУДИТЬ"):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='welcome-card'><h3>КТО ТЫ?</h3></div>", unsafe_allow_html=True)
    
    # Прямая форма регистрации выше табов для надежности
    with st.expander("✨ СОЗДАТЬ НОВОГО ПАРНЯ", expanded=True):
        new_n = st.text_input("Имя", key="reg_n")
        new_b = st.text_area("О нем", key="reg_b")
        if st.button("ЗАРЕГИСТРИРОВАТЬ"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

    st.divider()
    
    u_names = []
    if users_sheet:
        u_data = users_sheet.get_all_records()
        u_names = [u['Name'] for u in u_data]
    
    if u_names:
        sel_u = st.selectbox("Или выбери существующего:", u_names)
        if st.button("ВОЙТИ"):
            st.session_state.u_name = sel_u
            st.session_state.app_state = "hero_select"
            st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"<div class='welcome-card'><h3>ПРИВЕТ, {st.session_state.u_name} 👋</h3><p>С кем хочешь поговорить?</p></div>", unsafe_allow_html=True)
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        sel_h = st.selectbox("Контакт:", [h['Name'] for h in h_data])
        if st.button("УСТАНОВИТЬ СОЕДИНЕНИЕ"):
            h = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. ПИШИ С ЭМОДЗИ! ✨"
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    # КНОПКА ЗАВЕРШЕНИЯ В БОКУ
    with st.sidebar:
        st.title("УПРАВЛЕНИЕ")
        st.write(f"Собеседник: **{st.session_state.u_name}**")
        if st.button("🔚 ЗАВЕРШИТЬ СЕАНС"):
            st.session_state.app_state = "welcome"
            st.rerun()

    # Хедер чата
    st.markdown(f"""
        <center><div class="chat-header">
            <img src="{USER_PHOTO}" style="width: 45px; height: 45px; border-radius: 50%; border: 2px solid #ff4b4b;">
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 9px;">● ONLINE</div>
            </div>
        </div></center>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        ico = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]):
            st.markdown(f"**{ico}** {m['content']}")
    
    if p := st.chat_input("Напиши сообщение... 💭"):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(f"👤 {p}")
        
        res = gro_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(f"✨ {ans}")
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        if sheet: 
            try: sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])
            except: pass
