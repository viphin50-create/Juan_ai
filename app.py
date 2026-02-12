import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

st.set_page_config(page_title="Cipher", layout="centered")

# Твой дизайн
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; font-size: 14px !important; }
    .stApp { background-color: #0a0a0a !important; color: #ffffff !important; }
    .stButton>button {
        width: 100% !important; background: rgba(255, 75, 75, 0.15) !important;
        border: 1px solid #ff4b4b !important; color: #ffffff !important;
        font-weight: 600 !important; height: 38px !important; font-size: 12px !important; border-radius: 10px !important;
    }
    .status-dot { height: 8px; width: 8px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 5px; box-shadow: 0 0 5px #00ff00; }
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
        # Листы: Settings (герои), Users (история), Profiles (данные юзеров)
        return client.worksheet("Settings"), client.worksheet("Users"), client.worksheet("Profiles")
    except: return None, None, None

settings_sheet, users_sheet, profiles_sheet = init_db()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state: st.session_state.app_state = "user_select"

st.markdown("<h3 style='text-align:center; color:#ff4b4b; letter-spacing:3px; margin:0;'>JUAN AI</h3>", unsafe_allow_html=True)

# --- ШАГ 1: ВЫБОР ИЛИ СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ---
if st.session_state.app_state == "user_select":
    st.markdown("<p style='text-align:center;'>Кто заходит?</p>", unsafe_allow_html=True)
    
    profiles = []
    if profiles_sheet:
        profiles = profiles_sheet.get_all_records()
    
    mode = st.radio("Действие", ["Выбрать профиль", "Создать профиль"], label_visibility="collapsed")
    
    if mode == "Выбрать профиль":
        u_names = [p['user_id'] for p in profiles] if profiles else []
        u_choice = st.selectbox("Твой аккаунт", u_names if u_names else ["Пусто"])
        if st.button("ВОЙТИ") and u_choice != "Пусто":
            p_data = next(p for p in profiles if p['user_id'] == u_choice)
            st.session_state.u_name = u_choice
            st.session_state.u_bio = p_data.get('bio', '')
            st.session_state.app_state = "hero_select"
            st.rerun()
    else:
        new_u = st.text_input("Придумай ник")
        new_u_bio = st.text_area("Расскажи о себе (внешность, характер)", placeholder="Напр: Парень, 20 лет, люблю дерзких...")
        if st.button("СОЗДАТЬ И ВОЙТИ") and new_u:
            if profiles_sheet:
                profiles_sheet.append_row([new_u, new_u_bio, datetime.now().strftime("%Y-%m-%d")])
                st.session_state.u_name = new_u
                st.session_state.u_bio = new_u_bio
                st.session_state.app_state = "hero_select"
                st.rerun()

# --- ШАГ 2: ВЫБОР ИЛИ СОЗДАНИЕ ПАРТНЕРА ---
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center; font-size:12px;'>Юзер: {st.session_state.u_name}</p>", unsafe_allow_html=True)
    
    heroes = settings_sheet.get_all_records() if settings_sheet else []
    h_mode = st.radio("Партнер", ["Выбрать из списка", "Создать нового"], label_visibility="collapsed")
    
    if h_mode == "Выбрать из списка":
        h_names = [h['partner_id'] for h in heroes]
        h_choice = st.selectbox("С кем общаемся?", h_names if h_names else ["Нет героев"])
        
        if st.button("НАЧАТЬ ЧАТ") and h_names:
            h = next(i for i in heroes if i["partner_id"] == h_choice)
            st.session_state.current_name = h['partner_id']
            # ВШИВАЕМ ИНФУ О ЮЗЕРЕ В ПЕРСОНУ
            st.session_state.persona = f"Ты {h['partner_id']}. {h['system_prompt']}. Твой собеседник — {st.session_state.u_name}. О нем известно: {st.session_state.get('u_bio', 'информации нет')}. Веди диалог в стиле романтики и LGBT+, используй эмодзи."
            
            # ЗАГРУЗКА ПАМЯТИ
            st.session_state.messages = []
            if users_sheet:
                all_hist = users_sheet.get_all_records()
                st.session_state.messages = [
                    {"role": r['role'], "content": r['content']} 
                    for r in all_hist if str(r.get('user_id')) == st.session_state.u_name and str(r.get('partner_id')) == h_choice
                ][-15:]
            
            st.session_state.app_state = "chat"
            st.rerun()
    
    else:
        with st.form("new_hero"):
            n_id = st.text_input("ID персонажа (латиница)")
            n_prompt = st.text_area("Характер персонажа")
            if st.form_submit_button("СОЗДАТЬ"):
                settings_sheet.append_row([n_id, n_id, n_prompt, "", "777", ""])
                st.success("Герой создан!")

# --- ШАГ 3: ЧАТ ---
elif st.session_state.app_state == "chat":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"<div style='display:flex;align-items:center;gap:10px;'><img src='{AI_AVATAR}' style='width:40px;border-radius:50%;border:2px solid #ff4b4b;'><div><b style='color:#ff4b4b;'>{st.session_state.current_name.upper()}</b><br><small style='color:#00ff00;'>В СЕТИ</small></div></div>", unsafe_allow_html=True)
    with col2:
        if st.button("ВЫХОД"):
            st.session_state.app_state = "hero_select"
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Напиши..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "user", p, datetime.now().strftime("%H:%M")])

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = response.choices[0].message.content
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "assistant", ans, datetime.now().strftime("%H:%M")])
