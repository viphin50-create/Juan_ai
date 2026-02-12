import streamlit as st
import requests
from datetime import datetime

# 1. КОНФИГУРАЦИЯ
# Твой URL развертывания из Google Apps Script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzaG9-qwgYWVi-NvULnvFdzgkAgkxBk2QZdaQngxJiS8wSsA1glvbbQfu2oJHgwlhDySQ/exec"

st.set_page_config(page_title="Cipher AI", layout="centered")

# Стили (Твой оригинальный дизайн)
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
    .status-dot {
        height: 8px; width: 8px; background-color: #00ff00; border-radius: 50%;
        display: inline-block; margin-right: 5px; box-shadow: 0 0 5px #00ff00;
    }
    </style>
""", unsafe_allow_html=True)

# Инициализация состояний
if "app_state" not in st.session_state: st.session_state.app_state = "welcome"
if "current_img" not in st.session_state: st.session_state.current_img = "https://via.placeholder.com/150"

st.markdown("<h3 style='text-align:center; color:#ff4b4b; letter-spacing:3px; margin:0;'>JUAN AI</h3>", unsafe_allow_html=True)

# --- ШАГ 1: ВХОД (УПРОЩЕННЫЙ) ---
if st.session_state.app_state == "welcome":
    st.markdown("<p style='text-align:center;'>Добро пожаловать в систему</p>", unsafe_allow_html=True)
    u_name = st.text_input("Введи своё имя", placeholder="Например, Валентин")
    
    if st.button("ВОЙТИ"):
        if u_name:
            st.session_state.u_name = u_name
            st.session_state.app_state = "hero_select"
            st.rerun()
        else:
            st.warning("Сначала введи имя!")

# --- ШАГ 2: ВЫБОР ПАРТНЕРА ---
elif st.session_state.app_state == "hero_select":
    st.markdown(f"<p style='text-align:center; font-size:12px;'>Привет, {st.session_state.u_name}</p>", unsafe_allow_html=True)
    
    # Здесь можно добавить список имен, которые есть у тебя в Settings
    h_choice = st.selectbox("🎯 С кем на связь?", ["Мигель", "ЧИКО", "+ Новый"])

    if h_choice == "+ Новый":
        st.info("Чтобы добавить нового, просто впиши его имя в таблицу Settings и перезагрузи страницу.")
    
    if st.button("НАЧАТЬ ЧАТ"):
        st.session_state.current_name = h_choice
        st.session_state.app_state = "chat"
        # Сбрасываем старые сообщения при входе к новому партнеру
        st.session_state.messages = [] 
        st.rerun()
    
    if st.button("⬅ Назад"):
        st.session_state.app_state = "welcome"
        st.rerun()

# --- ШАГ 3: ЧАТ ---
elif st.session_state.app_state == "chat":
    # ХЕДЕР ЧАТА
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="{st.session_state.current_img}" style="width: 45px; height: 45px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover;">
                <div style="line-height: 1.2;">
                    <div style="color: #ff4b4b; font-size: 14px; font-weight: 600;">{st.session_state.current_name.upper()}</div>
                    <div style="font-size: 9px; color: #00ff00;"><span class="status-dot"></span>В СЕТИ</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("ВЫЙТИ"):
            st.session_state.app_state = "welcome"
            st.rerun()

    # Отображение сообщений
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    
    # Ввод сообщения
    if p := st.chat_input("Напиши сообщение..."):
        # Добавляем сообщение пользователя в интерфейс
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"):
            st.markdown(p)
        
        # Запрос к твоему Google бэкенду
        try:
            with st.spinner("Думает..."):
                response = requests.post(SCRIPT_URL, json={
                    "partnerId": st.session_state.current_name,
                    "message": p
                }, timeout=30)
                
                res_data = response.json()
                
                if "error" in res_data:
                    st.error(f"Ошибка бэкенда: {res_data['error']}")
                else:
                    ans = res_data.get("text", "...")
                    img = res_data.get("image", st.session_state.current_img)
                    
                    # Обновляем фото партнера, если оно изменилось
                    st.session_state.current_img = img
                    
                    # Показываем ответ
                    with st.chat_message("assistant"):
                        st.markdown(ans)
                    
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    st.rerun() # Перезапуск для обновления аватара в хедере

        except Exception as e:
            st.error(f"Не удалось связаться со скриптом: {e}")
