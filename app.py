import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ДИЗАЙН (Montserrat + Жесткая чистка)
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
    
    /* УНИЧТОЖАЕМ FACE И ART НА КОРНЮ */
    [data-testid="stAvatar"] { display: none !important; }
    div[data-testid="stChatMessage"] section div { font-size: 0 !important; }
    div[data-testid="stChatMessage"] section div * { font-size: 16px !important; }

    /* Компактные кнопки */
    .stButton>button {
        width: auto !important;
        min-width: 150px;
        background: transparent !important;
        border: 1px solid rgba(255, 75, 75, 0.6) !important;
        color: white !important;
        border-radius: 8px !important;
        margin: 5px 0;
    }
    
    /* Убираем гигантские фоны */
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 10px !important; }
    
    /* Хедер чата */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 40px;
        border: 1px solid rgba(255, 75, 75, 0.3);
        width: fit-content;
        margin: 0 auto 20px auto;
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

if "app_state" not in st.session_state: st.session_state.app_state = "welcome"
if "u_name" not in st.session_state: st.session_state.u_name = None

# 3. ЦЕНТРАЛЬНАЯ ЛОГИКА
st.markdown("<h2 style='text-align:center; color:#ff4b4b; letter-spacing:5px;'>JUAN AI</h2>", unsafe_allow_html=True)

# ШАГ 1: ВЫБОР ИЛИ СОЗДАНИЕ ТЕБЯ
if st.session_state.app_state == "welcome":
    st.write("👤 **ШАГ 1: КТО ТЫ?**")
    
    u_names = []
    if users_sheet:
        try:
            u_data = users_sheet.get_all_records()
            u_names = [u['Name'] for u in u_data]
        except: pass

    if u_names:
        sel_u = st.selectbox("Выбрать существующий профиль:", u_names)
        if st.button("ВЫБРАТЬ"):
            st.session_state.u_name = sel_u
            st.session_state.app_state = "hero_select"
            st.rerun()
    
    with st.expander("Создать новый профиль"):
        new_n = st.text_input("Имя")
        new_b = st.text_area("О себе")
        if st.button("СОЗДАТЬ"):
            if new_n and users_sheet:
                users_sheet.append_row([new_n, new_b])
                st.session_state.u_name = new_n
                st.session_state.app_state = "hero_select"
                st.rerun()

# ШАГ 2: ВЫБОР ИЛИ СОЗДАНИЕ ПАРТНЕРА
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center;'>Привет, <b>{st.session_state.u_name}</b>!</p>", unsafe_allow_html=True)
    st.write("🎯 **ШАГ 2: ВЫБЕРИ ПАРТНЕРА**")
    
    if settings_sheet:
        heroes = settings_sheet.get_all_records()
        h_names = [h['Name'] for h in heroes]
        
        sel_h = st.selectbox("Из готового списка:", h_names)
        if st.button("ВОЙТИ В ЧАТ"):
            h = next(i for i in heroes if i["Name"] == sel_h)
            st.session_state.persona = f"Ты {h['Name']}. {h['Prompt']}. Собеседник: {st.session_state.u_name}. Романтика, LGBT+, эмодзи."
            st.session_state.current_name = h['Name']
            st.session_state.app_state = "chat"
            st.rerun()
            
    with st.expander("Создать нового партнера"):
        new_h_n = st.text_input("Имя персонажа")
        new_h_p = st.text_area("Промпт/Характер")
        if st.button("СОЗДАТЬ И ВЫБРАТЬ"):
            if new_h_n and settings_sheet:
                settings_sheet.append_row([new_h_n, new_h_p])
                st.success("Готово! Выбери его теперь в списке выше.")
                st.rerun()

# ШАГ 3: ЧАТ
elif st.session_state.app_state == "chat":
    st.markdown(f"""
        <div class="chat-header">
            <div style="width: 40px; height: 40px; background: #ff4b4b; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">{st.session_state.current_name[0]}</div>
            <div style="text-align: left;">
                <div style="color: #ff4b4b; font-size: 16px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                <div style="color: #00ff00; font-size: 10px;">● В СЕТИ</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        icon = "👤" if m["role"] == "user" else "✨"
        with st.chat_message(m["role"]): st.markdown(f"**{icon}** {m['content']}")
    
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
        if sheet: sheet.append_row([datetime.now().strftime("%H:%M"), st.session_state.current_name, p, ans[:200]])

    if st.button("ЗАВЕРШИТЬ СЕАНС"):
        st.session_state.app_state = "welcome"
        st.rerun()
