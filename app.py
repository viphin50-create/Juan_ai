import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ТГ-ДИЗАЙН (CSS)
st.set_page_config(page_title="Telegram", page_icon="💬", layout="centered")

st.markdown("""
    <style>
    /* Прячем весь мусор Streamlit */
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    
    /* Фон как в ночном Telegram */
    .stApp {
        background-color: #17212b; 
    }
    
    /* Контейнер чата */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        max-width: 100% !important;
    }

    /* Стили сообщений */
    .stChatMessage {
        border: none !important;
        background-color: transparent !important;
        padding: 0.5rem 1rem !important;
    }

    /* Бабл пользователя (справа) */
    div[data-testid="stChatMessageUser"] {
        background-color: #2b5278 !important; /* Цвет ТГ для своих сообщений */
        border-radius: 15px 15px 2px 15px !important;
        margin-left: 15% !important;
        width: fit-content !important;
        float: right !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }

    /* Бабл бота (слева) */
    div[data-testid="stChatMessageAssistant"] {
        background-color: #1c2732 !important; /* Цвет ТГ для входящих */
        border-radius: 15px 15px 15px 2px !important;
        margin-right: 15% !important;
        width: fit-content !important;
        float: left !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }

    /* Текст внутри баблов */
    .stMarkdown p {
        color: #f5f5f5 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 15px !important;
        line-height: 1.4 !important;
        margin-bottom: 0px !important;
    }

    /* Скрываем аватарки */
    div[data-testid="stChatMessageUser"] [data-testid="stAvatar"],
    div[data-testid="stChatMessageAssistant"] [data-testid="stAvatar"] {
        display: none !important;
    }

    /* Поле ввода как в ТГ */
    .stChatInputContainer {
        border-top: 1px solid #101921 !important;
        background-color: #17212b !important;
        padding: 10px !important;
    }
    
    .stChatInput textarea {
        background-color: #17212b !important;
        border: none !important;
        color: white !important;
    }
    
    /* Скрываем индикатор "Running..." для беспалевности */
    #stStatusWidget { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ОСТАЛЬНАЯ ЛОГИКА (БЕЗ ИЗМЕНЕНИЙ)
# [Далее идет твой код init_db, персонажи и чат...]
