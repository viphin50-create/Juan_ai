import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

st.set_page_config(page_title="Cipher", layout="centered")

# Дизайн
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

# 2. ИНИЦИАЛИЗАЦИЯ БД
@st.cache_resource
def init_db():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds).open("Juan")
        # Листы: Settings (герои), Users (история чата), Profiles (список юзеров)
        return client.worksheet("Settings"), client.worksheet("Users")
    except Exception as e:
        st.error(f"Ошибка подключения к Google Sheets: {e}")
        return None, None

settings_sheet, users_sheet = init_db()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state: st.session_state.app_state = "user_select"

st.markdown("<h3 style='text-align:center; color:#ff4b4b; letter-spacing:3px; margin:0;'>JUAN AI</h3>", unsafe_allow_html=True)

# --- ШАГ 1: ВЫБОР ИЛИ СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ---
if st.session_state.app_state == "user_select":
    st.markdown("<p style='text-align:center;'>Кто заходит?</p>", unsafe_allow_html=True)
    
    # Получаем список уникальных юзеров из истории, если нет отдельного листа
    existing_users = []
    if users_sheet:
        try:
            data = users_sheet.get_all_records()
            existing_users = list(set([str(row['user_id']) for row in data if row.get('user_id')]))
        except: pass
    
    mode = st.radio("Действие", ["Выбрать профиль", "Создать профиль"], label_visibility="collapsed")
    
    if mode == "Выбрать профиль":
        u_choice = st.selectbox("Твой аккаунт", existing_users if existing_users else ["Пока пусто"])
        if st.button("ВОЙТИ") and u_choice != "Пока пусто":
            st.session_state.u_name = u_choice
            st.session_state.app_state = "hero_select"
            st.rerun()
    else:
        new_u = st.text_input("Придумай ник")
        if st.button("СОЗДАТЬ И ВОЙТИ") and new_u:
            st.session_state.u_name = new_u
            st.session_state.app_state = "hero_select"
            st.rerun()

# --- ШАГ 2: ВЫБОР ИЛИ СОЗДАНИЕ ПАРТНЕРА ---
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center; font-size:12px;'>Юзер: {st.session_state.u_name}</p>", unsafe_allow_html=True)
    
    heroes = []
    if settings_sheet:
        heroes = settings_sheet.get_all_records()
    
    h_mode = st.radio("Партнер", ["Выбрать из списка", "Создать нового"], label_visibility="collapsed")
    
    if h_mode == "Выбрать из списка":
        h_names = [h['partner_id'] for h in heroes] if heroes else []
        h_choice = st.selectbox("С кем общаемся?", h_names if h_names else ["Нет героев"])
        
        if st.button("НАЧАТЬ ЧАТ") and h_choice != "Нет героев":
            h = next(i for i in heroes if i["partner_id"] == h_choice)
            st.session_state.current_name = h['partner_id']
            st.session_state.persona = f"Ты {h['partner_id']}. {h['system_prompt']}. Собеседник: {st.session_state.u_name}. Романтика, LGBT+, эмодзи."
            
            # ЗАГРУЗКА ПАМЯТИ
            st.session_state.messages = []
            if users_sheet:
                try:
                    all_hist = users_sheet.get_all_records()
                    personal = [
                        {"role": r['role'], "content": r['content']} 
                        for r in all_hist if str(r.get('user_id')) == st.session_state.u_name and str(r.get('partner_id')) == h_choice
                    ]
                    st.session_state.messages = personal[-15:] # Берем последние 15 фраз
                except: pass
            
            st.session_state.app_state = "chat"
            st.rerun()
    
    else:
        with st.form("new_hero_form"):
            new_h_id = st.text_input("ID персонажа (латиницей, например: miguel)")
            new_h_prompt = st.text_area("Характер и поведение")
            if st.form_submit_button("СОЗДАТЬ ПАРТНЕРА"):
                if settings_sheet and new_h_id:
                    settings_sheet.append_row([new_h_id, new_h_id, new_h_prompt, "", "777", ""])
                    st.success("Готово! Теперь выбери его в списке.")
    
    if st.button("⬅ Назад"):
        st.session_state.app_state = "user_select"
        st.rerun()

# --- ШАГ 3: ЧАТ ---
elif st.session_state.app_state == "chat":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="{AI_AVATAR}" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ff4b4b;">
                <div>
                    <div style="color: #ff4b4b; font-size: 14px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                    <div style="font-size: 9px; color: #00ff00;"><span class="status-dot"></span>В СЕТИ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("ВЫХОД"):
            st.session_state.app_state = "hero_select"
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Твое сообщение..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        # Запись в БД (User)
        if users_sheet:
            users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "user", p, datetime.now().strftime("%Y-%m-%d %H:%M")])

        # Ответ ИИ
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = response.choices[0].message.content
        
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        # Запись в БД (AI)
        if users_sheet:
            users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "assistant", ans, datetime.now().strftime("%Y-%m-%d %H:%M")])
