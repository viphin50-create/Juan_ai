import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. КОНФИГУРАЦИЯ
AI_AVATAR = "https://r2.syntx.ai/mj/5069746049/single-7585790-1.png"

st.set_page_config(page_title="Cipher", layout="centered")

# Твой фирменный стиль
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    html, body, [class*="st-"] { font-family: 'Montserrat', sans-serif !important; font-size: 14px !important; }
    .stApp { background-color: #0a0a0a !important; color: #ffffff !important; }
    [data-testid="stAvatar"] { display: none !important; }
    div[data-testid="stChatMessage"] { padding: 8px !important; margin: 5px 0 !important; border-radius: 10px !important; }
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
        # Листы: 1-й для логов, Settings для героев, Users для истории диалогов
        return client.get_worksheet(0), client.worksheet("Settings"), client.worksheet("Users")
    except: return None, None, None

log_sheet, settings_sheet, users_sheet = init_db()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "app_state" not in st.session_state: st.session_state.app_state = "welcome"

st.markdown("<h3 style='text-align:center; color:#ff4b4b; letter-spacing:3px; margin:0;'>JUAN AI</h3>", unsafe_allow_html=True)

# --- ШАГ 1: ВЫБОР ПОЛЬЗОВАТЕЛЯ ---
if st.session_state.app_state == "welcome":
    # Для простоты вводим имя вручную или выбираем из Users (колонка A)
    u_name = st.text_input("Введи свой ник (для сохранения памяти)", placeholder="Например: vanya_dev")
    if st.button("ВОЙТИ") and u_name:
        st.session_state.u_name = u_name
        st.session_state.app_state = "hero_select"
        st.rerun()

# --- ШАГ 2: ВЫБОР ПАРТНЕРА + ЗАГРУЗКА ПАМЯТИ ---
elif st.session_state.app_state == "hero_select":
    try:
        heroes = settings_sheet.get_all_records()
        h_names = [h['partner_id'] for h in heroes] # Используем partner_id как в таблице
        h_choice = st.selectbox("🎯 С кем на связь?", h_names)
        
        if st.button("НАЧАТЬ ЧАТ"):
            h = next(i for i in heroes if i["partner_id"] == h_choice)
            st.session_state.current_name = h['partner_id']
            st.session_state.persona = f"Ты {h['partner_id']}. {h['system_prompt']}. Собеседник: {st.session_state.u_name}. Романтика, LGBT+, эмодзи."
            
            # ЗАГРУЗКА ПАМЯТИ ИЗ ТАБЛИЦЫ USERS
            st.session_state.messages = []
            if users_sheet:
                all_history = users_sheet.get_all_records()
                # Фильтруем историю: только для этого юзера и этого партнера
                personal_history = [
                    {"role": row['role'], "content": row['content']} 
                    for row in all_history 
                    if str(row.get('user_id')) == st.session_state.u_name and str(row.get('partner_id')) == h_choice
                ]
                st.session_state.messages = personal_history[-10:] # Берем последние 10 сообщений
            
            st.session_state.app_state = "chat"
            st.rerun()
    except Exception as e:
        st.error(f"Ошибка при загрузке героев или памяти: {e}")

# --- ШАГ 3: ЧАТ ---
elif st.session_state.app_state == "chat":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="{AI_AVATAR}" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ff4b4b;">
                <div>
                    <div style="color: #ff4b4b; font-size: 14px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                    <div style="font-size: 9px; color: #00ff00;">В СЕТИ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("ВЫЙТИ"):
            st.session_state.app_state = "hero_select"
            st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Напиши сообщение..."):
        # 1. Отображаем и сохраняем локально
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        # 2. Сохраняем в таблицу Users (БД)
        if users_sheet:
            users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "user", p, datetime.now().strftime("%Y-%m-%d %H:%M")])

        # 3. Ответ ИИ
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": st.session_state.persona}] + st.session_state.messages
        )
        ans = response.choices[0].message.content
        
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        # 4. Сохраняем ответ ИИ в таблицу Users (БД)
        if users_sheet:
            users_sheet.append_row([st.session_state.u_name, st.session_state.current_name, "assistant", ans, datetime.now().strftime("%Y-%m-%d %H:%M")])
