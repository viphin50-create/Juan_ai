import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# ПРЯМАЯ ССЫЛКА НА ФОТО
USER_PHOTO = "https://cdn.midjourney.com/u/3e5aa158-179e-48aa-88b0-bbef6bb9e7a0/0e909883da6dc88b440ea65fc9c9249352270c36a3b71af9f7744cf2b3d43381.png"

# 1. ДИЗАЙН И ЧИСТКА
st.set_page_config(page_title="Cipher", layout="centered")

st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    
    /* УНИЧТОЖАЕМ FACE И ART ПОЛНОСТЬЮ */
    [data-testid="stAvatar"] { display: none !important; }
    [data-testid="stChatMessage"] { padding: 5px !important; margin-left: 0 !important; }
    [data-testid="stChatMessage"] p { font-size: 16px !important; color: white !important; }
    
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp {
        background-color: #0a0a0a !important;
        background-image: radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.1) 0%, transparent 50%) !important;
    }
    
    .main-card {
        background: rgba(30, 30, 30, 0.4);
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(255, 75, 75, 0.2);
        margin-bottom: 15px;
    }
    
    .chat-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50px;
        border: 1px solid rgba(255, 75, 75, 0.3);
        width: fit-content;
        margin: 0 auto 20px auto;
    }
    </style>
""", unsafe_allow_html=True)

# 2. БД
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

# 3. ЛОГИКА ЭКРАНОВ
if st.session_state.app_state == "welcome":
    st.markdown("<div style='text-align:center; margin-top:50px;'><h1 style='color:#ff4b4b;'>JUAN AI</h1></div>", unsafe_allow_html=True)
    if st.button("РАЗБУДИТЬ", use_container_width=True):
        st.session_state.app_state = "user_select"
        st.rerun()

elif st.session_state.app_state == "user_select":
    st.markdown("<div class='main-card'><h3>👤 ВХОД</h3></div>", unsafe_allow_html=True)
    
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    if u_names:
        sel_u = st.selectbox("Выбери профиль:", u_names)
        if st.button("ВОЙТИ КАК ПАРЕНЬ", use_container_width=True):
            st.session_state.u_name = sel_u
            st.session_state.app_state = "hero_select"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ СОЗДАТЬ НОВЫЙ ПРОФИЛЬ"):
        new_n = st.text_input("Имя")
        new_b = st.text_area("О себе")
        if st.button("СОЗДАТЬ", use_container_width=True):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

elif st.session_state.app_state == "hero_select":
    st.markdown(f"### Привет, {st.session_state.u_name}!")
    if settings_sheet:
        h_data = settings_sheet.get_all_records()
        sel_h = st.selectbox("Выбери, с кем говорить:", [h['Name'] for h in h_data])
        if st.button("НАЧАТЬ ЧАТ", use_container_width=True):
            h = next(i for i in h_data if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. Используй много эмодзи! ✨"
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()

elif st.session_state.app_state == "chat":
    # ХЕДЕР С ФОТО
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

    if st.button("🔚 ВЫЙТИ"):
        st.session_state.app_state = "welcome"
        st.rerun()
