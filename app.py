import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq
from datetime import datetime

# 1. ТОТАЛЬНЫЙ ДИЗАЙН: НЕОНОВЫЙ ХУАН
st.set_page_config(page_title="Cipher", page_icon="💡", layout="centered")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
    /* Скрытие мусора */
    header, footer, #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none !important;}

    /* Глобальные шрифты и фон */
    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif !important;
        color: white !important;
    }

    .stApp {
        background: #0a0a0a;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255, 0, 0, 0.12) 0%, transparent 40%),
            radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.03) 0%, transparent 40%);
    }

    /* Анимация неоновых волн */
    .stApp::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background-image: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            rgba(255, 0, 0, 0.02) 100px,
            rgba(255, 0, 0, 0.02) 200px
        );
        animation: move 20s linear infinite;
        z-index: -1;
    }

    @keyframes move {
        from { transform: translate(0, 0); }
        to { transform: translate(100px, 100px); }
    }

    /* Экраны и карточки */
    .welcome-card {
        background: rgba(36, 47, 61, 0.4);
        backdrop-filter: blur(15px);
        padding: 25px 20px;
        border-radius: 20px;
        border: 1px solid rgba(255, 0, 0, 0.15);
        text-align: center;
