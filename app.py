import streamlit as st
import requests

# ВСТАВЬ СЮДА СВОЮ НОВУЮ ССЫЛКУ
URL = "https://script.google.com/macros/s/ВАША_ССЫЛКА/exec"

st.set_page_config(page_title="Cipher AI", layout="centered")

# Стили (коротко)
st.markdown("<style>.stApp {background-color: #0a0a0a; color: white;} .stButton>button {width:100%; border-radius:10px; background:#ff4b4b22; border:1px solid #ff4b4b; color:white;}</style>", unsafe_allow_html=True)

if "app_state" not in st.session_state: st.session_state.app_state = "welcome"

st.title("🤖 JUAN AI")

# ШАГ 1: ВХОД
if st.session_state.app_state == "welcome":
    name = st.text_input("Твоё имя")
    if st.button("ВОЙТИ") and name:
        st.session_state.u_name = name
        st.session_state.app_state = "hero_select"
        st.rerun()

# ШАГ 2: ВЫБОР ИЛИ СОЗДАНИЕ
elif st.session_state.app_state == "hero_select":
    mode = st.radio("Действие:", ["Выбрать партнера", "Создать нового"])
    
    if mode == "Выбрать партнера":
        # В идеале тут должен быть запрос списка, но пока впиши имя из таблицы
        h_name = st.text_input("Имя партнера из таблицы (напр. Мигель)")
        if st.button("НАЧАТЬ ЧАТ") and h_name:
            st.session_state.current_name = h_name
            st.session_state.messages = []
            st.session_state.app_state = "chat"
            st.rerun()
            
    else:
        with st.form("new_hero"):
            n = st.text_input("Имя героя")
            b = st.text_area("Характер (System Prompt)")
            l = st.text_area("Внешность (Appearance Prompt)")
            if st.form_submit_button("СОЗДАТЬ"):
                requests.post(URL, json={"action": "create", "partnerId": n, "bio": b, "look": l})
                st.success(f"Герой {n} создан в таблице!")

# ШАГ 3: ЧАТ
elif st.session_state.app_state == "chat":
    col1, col2 = st.columns([3, 1])
    col1.subheader(f"Чат с {st.session_state.current_name}")
    if col2.button("ВЫХОД"):
        st.session_state.app_state = "hero_select"
        st.rerun()

    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Напиши..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        res = requests.post(URL, json={"partnerId": st.session_state.current_name, "message": p}).json()
        
        if "image" in res: st.session_state.current_img = res["image"]
        ans = res.get("text", "Ошибка")
        
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
