import streamlit as st
import sqlite3
import hashlib
import datetime
import json
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import time

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="📚 Ders Programı Yöneticisi",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    
    .success-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .task-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #333;
    }
    
    .task-card h4 {
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .task-card p {
        color: #555;
        margin: 0.3rem 0;
    }
    
    .completed-task {
        background: #d4edda;
        border-left-color: #28a745;
        opacity: 0.7;
        color: #333;
    }
    
    .completed-task h4 {
        color: #333;
    }
    
    .completed-task p {
        color: #555;
    }
    
    .motivation-badge {
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 20px;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 1rem 0;
        color: #333;
    }
    
    .stats-card h3 {
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .stats-card h2 {
        color: #333;
        font-size: 2rem;
        margin: 0;
    }
    
    /* Sidebar düzenlemeleri */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .css-1d391kg .css-1v0mbdj {
        color: white !important;
    }
    
    .css-1d391kg .css-1v0mbdj h3 {
        color: white !important;
    }
    
    .css-1d391kg .css-1v0mbdj p {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    .css-1d391kg .css-1v0mbdj button {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .css-1d391kg .css-1v0mbdj button:hover {
        background: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Option menu düzenlemeleri */
    .css-1d391kg .css-1v0mbdj .css-1v0mbdj {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    .css-1d391kg .css-1v0mbdj .css-1v0mbdj .css-1v0mbdj {
        color: white !important;
    }
    
    /* Sidebar içindeki tüm yazıları beyaz yap */
    .css-1d391kg * {
        color: white !important;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3, .css-1d391kg h4, .css-1d391kg h5, .css-1d391kg h6 {
        color: white !important;
    }
    
    .css-1d391kg p, .css-1d391kg span, .css-1d391kg div {
        color: rgba(255, 255, 255, 0.9) !important;
    }
</style>
""", unsafe_allow_html=True)

# Veritabanı bağlantısı
def init_db():
    conn = sqlite3.connect('ders_programi.db')
    cursor = conn.cursor()
    
    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dersler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dersler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ders_adi TEXT NOT NULL,
            gun TEXT NOT NULL,
            baslangic_saati TEXT NOT NULL,
            bitis_saati TEXT NOT NULL,
            ogretmen TEXT,
            sinif TEXT,
            renk TEXT DEFAULT '#667eea',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Görevler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gorevler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            gorev_adi TEXT NOT NULL,
            aciklama TEXT,
            tarih DATE NOT NULL,
            saat TEXT,
            tamamlandi BOOLEAN DEFAULT FALSE,
            oncelik TEXT DEFAULT 'Orta',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Başarılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS basarilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            basari_adi TEXT NOT NULL,
            kazanildi_tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Günlük rutin tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rutin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            baslik TEXT NOT NULL,
            gun TEXT NOT NULL,
            baslangic_saati TEXT NOT NULL,
            bitis_saati TEXT NOT NULL,
            kategori TEXT,
            aciklama TEXT,
            renk TEXT DEFAULT '#22c55e',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    return conn

# Şifre hashleme
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Kullanıcı kimlik doğrulama
def authenticate_user(username, password):
    conn = init_db()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    
    cursor.execute('SELECT id, username FROM users WHERE username = ? AND password_hash = ?', 
                   (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    
    return user

# Kullanıcı kaydı
def register_user(username, password, email):
    conn = init_db()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    
    try:
        cursor.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)', 
                      (username, password_hash, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Ana uygulama
def main():
    # Oturum durumu kontrolü
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.username = None
    
    # Giriş yapmamış kullanıcı için giriş/kayıt sayfası
    if st.session_state.user_id is None:
        show_login_page()
    else:
        # Ana başlık (sadece giriş yapmış kullanıcılar için)
        st.markdown("""
        <div class="main-header">
            <h1>📚 Ders Programı Yöneticisi</h1>
            <p>Hedeflerine ulaşmanın en eğlenceli yolu!</p>
        </div>
        """, unsafe_allow_html=True)
        show_main_app()

def show_login_page():
    # Login sayfası için özel CSS
    st.markdown("""
    <style>
        .main-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            padding: 2rem;
            margin: -1rem;
        }
        
        .login-container {
            max-width: 500px;
            margin: 2rem auto;
            padding: 3rem;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .login-title {
            text-align: center;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .welcome-text {
            text-align: center;
            color: #666;
            font-size: 1.3rem;
            margin-bottom: 2rem;
            font-style: italic;
        }
        
        .feature-highlights {
            display: flex;
            justify-content: space-around;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .feature-item {
            text-align: center;
            margin: 1rem;
            padding: 1rem;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 15px;
            border: 2px solid rgba(102, 126, 234, 0.2);
        }
        
        .feature-item h4 {
            color: #667eea;
            margin: 0.5rem 0;
        }
        
        .feature-item p {
            color: #666;
            font-size: 0.9rem;
            margin: 0;
        }
        
        .tab-container {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #667eea);
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .floating-elements {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        
        .floating-element {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }
        
        .floating-element:nth-child(1) {
            width: 80px;
            height: 80px;
            top: 20%;
            left: 10%;
            animation-delay: 0s;
        }
        
        .floating-element:nth-child(2) {
            width: 60px;
            height: 60px;
            top: 60%;
            right: 15%;
            animation-delay: 2s;
        }
        
        .floating-element:nth-child(3) {
            width: 100px;
            height: 100px;
            bottom: 20%;
            left: 20%;
            animation-delay: 4s;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Basit başlık ve açıklama
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 style="color: #667eea; font-size: 3rem; margin-bottom: 1rem;">📚 Ders Programı Yöneticisi</h1>
        <p style="color: #666; font-size: 1.5rem; font-style: italic;">Hedeflerine ulaşmanın en eğlenceli yolu!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Özellik kartları
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: #f0f8ff; border-radius: 15px; margin: 1rem 0;">
            <h3 style="color: #667eea;">📅 Ders Programı</h3>
            <p style="color: #666;">Haftalık ders planınızı oluşturun</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: #f0f8ff; border-radius: 15px; margin: 1rem 0;">
            <h3 style="color: #667eea;">✅ Görev Takibi</h3>
            <p style="color: #666;">Ödevlerinizi organize edin</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: #f0f8ff; border-radius: 15px; margin: 1rem 0;">
            <h3 style="color: #667eea;">🏆 Başarılar</h3>
            <p style="color: #666;">Motivasyonunuzu artırın</p>
        </div>
        """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        st.markdown("### 🔐 Hesabınıza Giriş Yapın")
        with st.form("login_form"):
            col1, col2 = st.columns([1, 1])
            with col1:
                username = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
            with col2:
                password = st.text_input("🔒 Şifre", type="password", placeholder="Şifrenizi girin")
            
            submit = st.form_submit_button("🚀 Giriş Yap", width='stretch')
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.success("🎉 Başarıyla giriş yaptınız!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı!")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun!")
    
    with tab2:
        st.markdown("### 📝 Yeni Hesap Oluşturun")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("👤 Kullanıcı Adı", placeholder="Yeni kullanıcı adı")
                new_password = st.text_input("🔒 Şifre", type="password", placeholder="En az 6 karakter")
            with col2:
                confirm_password = st.text_input("🔒 Şifre Tekrar", type="password", placeholder="Şifrenizi tekrar girin")
                email = st.text_input("📧 E-posta", placeholder="E-posta adresiniz (opsiyonel)")
            
            submit = st.form_submit_button("✨ Kayıt Ol", width='stretch')
            
            if submit:
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Şifreler eşleşmiyor!")
                    elif len(new_password) < 6:
                        st.error("❌ Şifre en az 6 karakter olmalı!")
                    else:
                        if register_user(new_username, new_password, email):
                            st.success("🎉 Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
                        else:
                            st.error("❌ Bu kullanıcı adı zaten kullanılıyor!")
                else:
                    st.warning("⚠️ Lütfen gerekli alanları doldurun!")

def show_main_app():
    # Yan menü
    with st.sidebar:
        # Kullanıcı bilgileri
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 15px; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">👋 Hoş geldin!</h3>
            <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-weight: bold;">{st.session_state.username}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Çıkış butonu
        if st.button("🚪 Çıkış Yap", width='stretch'):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigasyon menüsü
        selected = option_menu(
            menu_title="📋 Menü",
            options=["🏠 Ana Sayfa", "📅 Ders Programı", "✅ Görevler", "🧭 Günlük Rutin", "⏱️ Pomodoro", "🏆 Başarılar", "📊 İstatistikler"],
            icons=["house", "calendar", "check-square", "compass", "clock", "trophy", "bar-chart"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "rgba(255,255,255,0.1)", "border-radius": "10px"},
                "icon": {"color": "white", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "color": "white"},
                "nav-link-selected": {"background-color": "rgba(255,255,255,0.2)", "color": "white"},
            }
        )
    
    # Sayfa içeriği
    if selected == "🏠 Ana Sayfa":
        show_dashboard()
    elif selected == "📅 Ders Programı":
        show_schedule()
    elif selected == "✅ Görevler":
        show_tasks()
    elif selected == "🧭 Günlük Rutin":
        show_daily_routine()
    elif selected == "⏱️ Pomodoro":
        show_pomodoro()
    elif selected == "🏆 Başarılar":
        show_achievements()
    elif selected == "📊 İstatistikler":
        show_statistics()

def show_dashboard():
    st.markdown("### 🏠 Ana Sayfa")
    
    # Motivasyon mesajı
    current_hour = datetime.datetime.now().hour
    if 6 <= current_hour < 12:
        greeting = "Günaydın! 🌅"
        message = "Yeni bir gün, yeni hedefler!"
    elif 12 <= current_hour < 18:
        greeting = "İyi günler! ☀️"
        message = "Günün ortasında harika gidiyorsun!"
    else:
        greeting = "İyi akşamlar! 🌙"
        message = "Günün sonunda bile hedeflerine odaklan!"
    
    st.markdown(f"""
    <div class="success-card">
        <h3>{greeting}</h3>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Bugünkü görevler
    conn = init_db()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    cursor.execute('''
        SELECT COUNT(*) FROM gorevler 
        WHERE user_id = ? AND tarih = ? AND tamamlandi = FALSE
    ''', (st.session_state.user_id, today))
    today_tasks = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM gorevler 
        WHERE user_id = ? AND tarih = ? AND tamamlandi = TRUE
    ''', (st.session_state.user_id, today))
    completed_tasks = cursor.fetchone()[0]
    
    # İstatistik kartları
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>📝 Bugünkü Görevler</h3>
            <h2>{today_tasks}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>✅ Tamamlanan</h3>
            <h2>{completed_tasks}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cursor.execute('SELECT COUNT(*) FROM dersler WHERE user_id = ?', (st.session_state.user_id,))
        total_classes = cursor.fetchone()[0]
        st.markdown(f"""
        <div class="stats-card">
            <h3>📚 Toplam Ders</h3>
            <h2>{total_classes}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        cursor.execute('SELECT COUNT(*) FROM basarilar WHERE user_id = ?', (st.session_state.user_id,))
        total_achievements = cursor.fetchone()[0]
        st.markdown(f"""
        <div class="stats-card">
            <h3>🏆 Başarılar</h3>
            <h2>{total_achievements}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    conn.close()
    
    # Bugünkü dersler
    st.markdown("### 📅 Bugünkü Dersler")
    show_todays_classes()

def show_todays_classes():
    conn = init_db()
    cursor = conn.cursor()
    
    today = datetime.datetime.now().strftime('%A')
    cursor.execute('''
        SELECT ders_adi, baslangic_saati, bitis_saati, ogretmen, sinif, renk
        FROM dersler 
        WHERE user_id = ? AND gun = ?
        ORDER BY baslangic_saati
    ''', (st.session_state.user_id, today))
    
    classes = cursor.fetchall()
    conn.close()
    
    if classes:
        for ders in classes:
            st.markdown(f"""
            <div class="task-card">
                <h4>📚 {ders[0]}</h4>
                <p><strong>🕐 Saat:</strong> {ders[1]} - {ders[2]}</p>
                <p><strong>👨‍🏫 Öğretmen:</strong> {ders[3] or 'Belirtilmemiş'}</p>
                <p><strong>🏫 Sınıf:</strong> {ders[4] or 'Belirtilmemiş'}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Bugün için ders bulunmuyor. Yeni ders eklemek için Ders Programı sekmesini kullanın!")

def show_schedule():
    st.markdown("### 📅 Ders Programı Yönetimi")
    
    tab1, tab2 = st.tabs(["📋 Dersleri Görüntüle", "➕ Yeni Ders Ekle"])
    
    with tab1:
        show_all_classes()
    
    with tab2:
        add_new_class()

def show_all_classes():
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ders_adi, gun, baslangic_saati, bitis_saati, ogretmen, sinif, renk
        FROM dersler 
        WHERE user_id = ?
        ORDER BY gun, baslangic_saati
    ''', (st.session_state.user_id,))
    
    classes = cursor.fetchall()
    conn.close()
    
    if classes:
        # Notion tarzı kompakt ders programı
        st.markdown("""
        <style>
            .notion-schedule {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .notion-day-group {
                border-bottom: 1px solid #f0f0f0;
            }
            
            .notion-day-header {
                background: #f8f9fa;
                padding: 12px 16px;
                font-weight: 600;
                color: #333;
                border-bottom: 1px solid #e9ecef;
            }
            
            .notion-class-item {
                padding: 12px 16px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
                transition: background-color 0.2s;
            }
            
            .notion-class-item:hover {
                background-color: #f8f9fa;
            }
            
            .notion-class-item:last-child {
                border-bottom: none;
            }
            
            .notion-class-color {
                width: 4px;
                height: 40px;
                border-radius: 2px;
                margin-right: 12px;
            }
            
            .notion-class-content {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .notion-class-title {
                font-weight: 500;
                color: #333;
                margin: 0;
                font-size: 14px;
            }
            
            .notion-class-meta {
                font-size: 12px;
                color: #666;
                margin-top: 2px;
            }
            
            .notion-class-time {
                background: #e3f2fd;
                color: #1976d2;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                margin-left: 8px;
                transition: all 0.2s ease;
            }
            
            .notion-class-time:hover {
                background: #1976d2;
                color: white;
                transform: scale(1.05);
            }
            
            .notion-class-actions {
                display: flex;
                gap: 4px;
            }
            
            .notion-class-btn {
                background: none;
                border: none;
                padding: 4px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .notion-class-btn:hover {
                background: #f0f0f0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Günlere göre grupla
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        
        st.markdown('<div class="notion-schedule">', unsafe_allow_html=True)
        
        for i, day in enumerate(days):
            day_classes = [c for c in classes if c[2] == day]
            if day_classes:
                st.markdown(f'<div class="notion-day-header">📅 {day_names[i]}</div>', unsafe_allow_html=True)
                
                for ders in day_classes:
                    class_id, title, day, start_time, end_time, teacher, classroom, color = ders
                    
                    # Meta bilgiler
                    meta_parts = []
                    if teacher:
                        meta_parts.append(f"👨‍🏫 {teacher}")
                    if classroom:
                        meta_parts.append(f"🏫 {classroom}")
                    
                    meta_text = " • ".join(meta_parts) if meta_parts else "Detay yok"
                    time_text = f"{start_time} - {end_time}"
                    
                    st.markdown(f"""
                    <div class="notion-class-item">
                        <div class="notion-class-color" style="background-color: {color}"></div>
                        <div class="notion-class-content">
                            <div class="notion-class-title">📚 {title}</div>
                            <div class="notion-class-meta">{meta_text}</div>
                        </div>
                        <div class="notion-class-time">{time_text}</div>
                        <div class="notion-class-actions">
                            <button class="notion-class-btn" onclick="deleteClass({class_id})">🗑️</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # JavaScript fonksiyonları
        st.markdown("""
        <script>
        function deleteClass(classId) {
            console.log('Delete class:', classId);
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Streamlit butonları
        st.markdown("---")
        st.markdown("**Ders Yönetimi:**")
        for ders in classes:
            class_id, title, day, start_time, end_time, teacher, classroom, color = ders
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📚 {title} - {start_time}")
            with col2:
                if st.button("🗑️", key=f"delete_class_{class_id}", help="Dersi sil"):
                    delete_class(class_id)
                    st.rerun()
    else:
        st.info("Henüz ders eklenmemiş. Yeni ders eklemek için 'Yeni Ders Ekle' sekmesini kullanın!")

def add_new_class():
    with st.form("add_class_form"):
        st.markdown("### ➕ Yeni Ders Ekle")
        
        # Kompakt form düzeni
        ders_adi = st.text_input("📚 Ders Adı", placeholder="Örn: Matematik")
        
        col1, col2 = st.columns(2)
        with col1:
            gun_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            gun_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            gun_index = st.selectbox("📅 Gün", range(len(gun_names)), format_func=lambda x: gun_names[x])
            gun = gun_options[gun_index]
        with col2:
            renk = st.color_picker("🎨 Ders Rengi", "#667eea")
        
        col3, col4 = st.columns(2)
        with col3:
            baslangic_saati = st.time_input("🕐 Başlangıç Saati")
        with col4:
            bitis_saati = st.time_input("🕐 Bitiş Saati")
        
        col5, col6 = st.columns(2)
        with col5:
            ogretmen = st.text_input("👨‍🏫 Öğretmen", placeholder="Öğretmen adı")
        with col6:
            sinif = st.text_input("🏫 Sınıf", placeholder="Sınıf numarası")
        
        submit = st.form_submit_button("✨ Ders Ekle", width='stretch')
        
        if submit:
            if ders_adi and baslangic_saati and bitis_saati:
                conn = init_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO dersler (user_id, ders_adi, gun, baslangic_saati, bitis_saati, ogretmen, sinif, renk)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state.user_id, ders_adi, gun, str(baslangic_saati), str(bitis_saati), ogretmen, sinif, renk))
                conn.commit()
                conn.close()
                st.success("🎉 Ders başarıyla eklendi!")
                st.rerun()
            else:
                st.error("❌ Lütfen tüm gerekli alanları doldurun!")

def delete_class(class_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM dersler WHERE id = ? AND user_id = ?', (class_id, st.session_state.user_id))
    conn.commit()
    conn.close()

def show_tasks():
    st.markdown("### ✅ Görev Yönetimi")
    
    tab1, tab2 = st.tabs(["📋 Görevleri Görüntüle", "➕ Yeni Görev Ekle"])
    
    with tab1:
        show_all_tasks()
    
    with tab2:
        add_new_task()

def show_all_tasks():
    conn = init_db()
    cursor = conn.cursor()
    
    # Tarih seçimi
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_date = st.date_input("📅 Tarih Seçin", datetime.date.today())
    with col2:
        st.markdown("### 📝 Görevler")
    
    cursor.execute('''
        SELECT id, gorev_adi, aciklama, saat, tamamlandi, oncelik
        FROM gorevler 
        WHERE user_id = ? AND tarih = ?
        ORDER BY saat, oncelik DESC
    ''', (st.session_state.user_id, selected_date))
    
    tasks = cursor.fetchall()
    conn.close()
    
    if tasks:
        # Notion tarzı kompakt liste
        st.markdown("""
        <style>
            .notion-task-list {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .notion-task-item {
                padding: 12px 16px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
                transition: background-color 0.2s;
            }
            
            .notion-task-item:hover {
                background-color: #f8f9fa;
            }
            
            .notion-task-item:last-child {
                border-bottom: none;
            }
            
            .notion-task-checkbox {
                margin-right: 12px;
                cursor: pointer;
            }
            
            .notion-task-content {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .notion-task-title {
                font-weight: 500;
                color: #333;
                margin: 0;
                font-size: 14px;
            }
            
            .notion-task-meta {
                font-size: 12px;
                color: #666;
                margin-top: 2px;
            }
            
            .notion-task-time {
                background: #f0f8ff;
                color: #0066cc;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                display: inline-block;
                margin-right: 6px;
                transition: all 0.2s ease;
            }
            
            .notion-task-time:hover {
                background: #0066cc;
                color: white;
                transform: scale(1.05);
            }
            
            .notion-task-priority {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 500;
                margin-left: 8px;
            }
            
            .priority-high {
                background: #fee;
                color: #d73a49;
            }
            
            .priority-medium {
                background: #fff3cd;
                color: #856404;
            }
            
            .priority-low {
                background: #d4edda;
                color: #155724;
            }
            
            .notion-task-actions {
                display: flex;
                gap: 4px;
            }
            
            .notion-task-btn {
                background: none;
                border: none;
                padding: 4px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .notion-task-btn:hover {
                background: #f0f0f0;
            }
            
            .completed-task-title {
                text-decoration: line-through;
                color: #999 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="notion-task-list">', unsafe_allow_html=True)
        
        for task in tasks:
            task_id, title, description, time_val, completed, priority = task
            
            # Öncelik rengi
            priority_class = {
                "Yüksek": "priority-high",
                "Orta": "priority-medium", 
                "Düşük": "priority-low"
            }.get(priority, "priority-medium")
            
            # Tamamlanma durumu
            title_class = "completed-task-title" if completed else ""
            
            # Meta bilgiler
            meta_parts = []
            if description:
                meta_parts.append(f"📄 {description[:30]}{'...' if len(description) > 30 else ''}")
            
            meta_text = " • ".join(meta_parts) if meta_parts else "Detay yok"
            time_display = f'<span class="notion-task-time">🕐 {time_val}</span>' if time_val else ""
            
            st.markdown(f"""
            <div class="notion-task-item">
                <div class="notion-task-checkbox">
                    {"✅" if completed else "⭕"}
                </div>
                <div class="notion-task-content">
                    <div class="notion-task-title {title_class}">{title}</div>
                    <div class="notion-task-meta">{time_display}{meta_text}</div>
                </div>
                <span class="notion-task-priority {priority_class}">{priority}</span>
                <div class="notion-task-actions">
                    {f'<button class="notion-task-btn" onclick="completeTask({task_id})">✅</button>' if not completed else ''}
                    <button class="notion-task-btn" onclick="deleteTask({task_id})">🗑️</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # JavaScript fonksiyonları
        st.markdown("""
        <script>
        function completeTask(taskId) {
            // Bu fonksiyon Streamlit ile entegre edilecek
            console.log('Complete task:', taskId);
        }
        
        function deleteTask(taskId) {
            // Bu fonksiyon Streamlit ile entegre edilecek
            console.log('Delete task:', taskId);
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Streamlit butonları
        st.markdown("---")
        st.markdown("**Görev Yönetimi:**")
        for task in tasks:
            task_id, title, description, time_val, completed, priority = task
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                status = "✅" if completed else "⭕"
                st.write(f"{status} {title[:30]}")
            with col2:
                if not completed and st.button("✅", key=f"complete_{task_id}", help="Tamamla"):
                    complete_task(task_id)
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{task_id}", help="Sil"):
                    delete_task(task_id)
                    st.rerun()
    else:
        st.info("Bu tarih için görev bulunmuyor. Yeni görev eklemek için 'Yeni Görev Ekle' sekmesini kullanın!")

def add_new_task():
    with st.form("add_task_form"):
        st.markdown("### ➕ Yeni Görev Ekle")
        
        # Kompakt form düzeni
        gorev_adi = st.text_input("📝 Görev Adı", placeholder="Örn: Matematik ödevi")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tarih = st.date_input("📅 Tarih", datetime.date.today())
        with col2:
            saat = st.time_input("🕐 Saat (opsiyonel)")
        with col3:
            oncelik = st.selectbox("⚡ Öncelik", ["Düşük", "Orta", "Yüksek"])
        
        aciklama = st.text_area("📄 Açıklama", placeholder="Görev detayları...", height=80)
        
        submit = st.form_submit_button("✨ Görev Ekle", width='stretch')
        
        if submit:
            if gorev_adi:
                conn = init_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO gorevler (user_id, gorev_adi, aciklama, tarih, saat, oncelik)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (st.session_state.user_id, gorev_adi, aciklama, tarih, str(saat) if saat else None, oncelik))
                conn.commit()
                conn.close()
                st.success("🎉 Görev başarıyla eklendi!")
                st.rerun()
            else:
                st.error("❌ Lütfen görev adını girin!")

def complete_task(task_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE gorevler SET tamamlandi = TRUE WHERE id = ? AND user_id = ?', 
                   (task_id, st.session_state.user_id))
    conn.commit()
    conn.close()
    
    # Başarı kontrolü
    check_achievements()

def delete_task(task_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gorevler WHERE id = ? AND user_id = ?', (task_id, st.session_state.user_id))
    conn.commit()
    conn.close()

def show_daily_routine():
    st.markdown("### 🧭 Günlük Rutin Yönetimi")
    tab1, tab2 = st.tabs(["📋 Rutinleri Görüntüle", "➕ Yeni Rutin Ekle"])
    with tab1:
        show_all_routines()
    with tab2:
        add_new_routine()

def show_all_routines():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, baslik, gun, baslangic_saati, bitis_saati, kategori, aciklama, renk
        FROM rutin
        WHERE user_id = ?
        ORDER BY gun, baslangic_saati
    ''', (st.session_state.user_id,))
    routines = cursor.fetchall()
    conn.close()
    if routines:
        st.markdown("""
        <style>
            .routine-list { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .routine-day-header { background:#f8f9fa; padding:12px 16px; font-weight:600; color:#333; border-bottom:1px solid #e9ecef; }
            .routine-item { padding:12px 16px; border-bottom:1px solid #f0f0f0; display:flex; align-items:center; }
            .routine-item:last-child { border-bottom:none; }
            .routine-color { width:4px; height:40px; border-radius:2px; margin-right:12px; }
            .routine-content { flex:1; display:flex; flex-direction:column; }
            .routine-title { font-weight:500; color:#333; margin:0; font-size:14px; }
            .routine-meta { font-size:12px; color:#666; margin-top:2px; }
            .routine-time { background:#dcfce7; color:#166534; padding:6px 12px; border-radius:6px; font-size:13px; font-weight:600; margin-left:8px; }
        </style>
        """, unsafe_allow_html=True)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        st.markdown('<div class="routine-list">', unsafe_allow_html=True)
        for i, day in enumerate(days):
            day_items = [r for r in routines if r[2] == day]
            if day_items:
                st.markdown(f'<div class="routine-day-header">🗓️ {day_names[i]}</div>', unsafe_allow_html=True)
                for r in day_items:
                    r_id, title, _day, start, end, category, desc, color = r
                    meta_parts = []
                    if category:
                        meta_parts.append(f"🏷️ {category}")
                    if desc:
                        meta_parts.append(f"📄 {desc[:30]}{'...' if len(desc) > 30 else ''}")
                    meta_text = " • ".join(meta_parts) if meta_parts else "Detay yok"
                    time_text = f"{start} - {end}"
                    st.markdown(f"""
                    <div class="routine-item">
                        <div class="routine-color" style="background-color:{color}"></div>
                        <div class="routine-content">
                            <div class="routine-title">🧭 {title}</div>
                            <div class="routine-meta">{meta_text}</div>
                        </div>
                        <div class="routine-time">{time_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**Rutin Yönetimi:**")
        for r in routines:
            r_id, title, _day, start, end, category, desc, color = r
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🧭 {title} - {start}")
            with col2:
                if st.button("🗑️", key=f"delete_routine_{r_id}", help="Rutini sil"):
                    delete_routine(r_id)
                    st.rerun()
    else:
        st.info("Henüz rutin eklenmemiş. 'Yeni Rutin Ekle' sekmesi ile başlayın!")

def add_new_routine():
    with st.form("add_routine_form"):
        st.markdown("### ➕ Yeni Rutin Ekle")
        baslik = st.text_input("🧭 Rutin Başlığı", placeholder="Örn: Sabah Çalışması")
        col1, col2 = st.columns(2)
        with col1:
            gun_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            gun_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            gun_index = st.selectbox("📅 Gün", range(len(gun_names)), format_func=lambda x: gun_names[x])
            gun = gun_options[gun_index]
        with col2:
            renk = st.color_picker("🎨 Renk", "#22c55e")
        col3, col4 = st.columns(2)
        with col3:
            baslangic_saati = st.time_input("🕐 Başlangıç Saati", datetime.time(8, 0))
        with col4:
            bitis_saati = st.time_input("🕐 Bitiş Saati", datetime.time(9, 0))
        col5, col6 = st.columns(2)
        with col5:
            kategori = st.text_input("🏷️ Kategori", placeholder="Örn: Ders Çalışma")
        with col6:
            aciklama = st.text_input("📄 Açıklama", placeholder="Kısa açıklama (opsiyonel)")
        submit = st.form_submit_button("✨ Rutin Ekle", width='stretch')
        if submit:
            if baslik:
                conn = init_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rutin (user_id, baslik, gun, baslangic_saati, bitis_saati, kategori, aciklama, renk)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (st.session_state.user_id, baslik, gun, str(baslangic_saati), str(bitis_saati), kategori, aciklama, renk))
                conn.commit()
                conn.close()
                st.success("🎉 Rutin eklendi!")
                st.rerun()
            else:
                st.error("❌ Lütfen rutin başlığını girin!")

def delete_routine(routine_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rutin WHERE id = ? AND user_id = ?', (routine_id, st.session_state.user_id))
    conn.commit()
    conn.close()

def show_achievements():
    st.markdown("### 🏆 Başarılarım")
    
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT basari_adi, kazanildi_tarih
        FROM basarilar 
        WHERE user_id = ?
        ORDER BY kazanildi_tarih DESC
    ''', (st.session_state.user_id,))
    
    achievements = cursor.fetchall()
    conn.close()
    
    if achievements:
        for achievement in achievements:
            st.markdown(f"""
            <div class="motivation-badge">
                🏆 {achievement[0]} - {achievement[1]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz başarı kazanmadınız. Görevlerinizi tamamlayarak başarılar kazanabilirsiniz!")
    
    # Mevcut başarılar
    st.markdown("### 🎯 Mevcut Başarılar")
    st.markdown("""
    <div class="motivation-badge">🎯 İlk Görev - İlk görevinizi tamamlayın</div>
    <div class="motivation-badge">🔥 5 Görev - 5 görev tamamlayın</div>
    <div class="motivation-badge">💪 10 Görev - 10 görev tamamlayın</div>
    <div class="motivation-badge">🚀 25 Görev - 25 görev tamamlayın</div>
    <div class="motivation-badge">⭐ 50 Görev - 50 görev tamamlayın</div>
    <div class="motivation-badge">👑 100 Görev - 100 görev tamamlayın</div>
    """, unsafe_allow_html=True)

def check_achievements():
    conn = init_db()
    cursor = conn.cursor()
    
    # Tamamlanan görev sayısı
    cursor.execute('SELECT COUNT(*) FROM gorevler WHERE user_id = ? AND tamamlandi = TRUE', 
                   (st.session_state.user_id,))
    completed_tasks = cursor.fetchone()[0]
    
    # Başarı kontrolü
    achievements = [
        (1, "İlk Görev"),
        (5, "5 Görev"),
        (10, "10 Görev"),
        (25, "25 Görev"),
        (50, "50 Görev"),
        (100, "100 Görev")
    ]
    
    for threshold, achievement_name in achievements:
        cursor.execute('SELECT COUNT(*) FROM basarilar WHERE user_id = ? AND basari_adi = ?', 
                       (st.session_state.user_id, achievement_name))
        if cursor.fetchone()[0] == 0 and completed_tasks >= threshold:
            cursor.execute('INSERT INTO basarilar (user_id, basari_adi) VALUES (?, ?)', 
                           (st.session_state.user_id, achievement_name))
            conn.commit()
    
    conn.close()

def show_statistics():
    st.markdown("### 📊 İstatistikler")
    
    conn = init_db()
    cursor = conn.cursor()
    
    # Son 7 günün görevleri
    cursor.execute('''
        SELECT tarih, COUNT(*) as toplam, SUM(CASE WHEN tamamlandi = TRUE THEN 1 ELSE 0 END) as tamamlanan
        FROM gorevler 
        WHERE user_id = ? AND tarih >= date('now', '-7 days')
        GROUP BY tarih
        ORDER BY tarih
    ''', (st.session_state.user_id,))
    
    stats = cursor.fetchall()
    conn.close()
    
    if stats:
        df = pd.DataFrame(stats, columns=['Tarih', 'Toplam Görev', 'Tamamlanan'])
        df['Tamamlanma Oranı'] = (df['Tamamlanan'] / df['Toplam Görev'] * 100).round(1)
        
        # Grafik
        fig = px.bar(df, x='Tarih', y=['Toplam Görev', 'Tamamlanan'], 
                     title='Son 7 Günün Görev İstatistikleri',
                     color_discrete_map={'Toplam Görev': '#667eea', 'Tamamlanan': '#28a745'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Tablo
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz yeterli veri bulunmuyor. Görevler ekleyerek istatistiklerinizi görebilirsiniz!")

def show_pomodoro():
    st.markdown("### ⏱️ Pomodoro Zamanlayıcı")
    if 'pomo_running' not in st.session_state:
        st.session_state.pomo_running = False
    if 'pomo_end' not in st.session_state:
        st.session_state.pomo_end = None
    if 'pomo_mode' not in st.session_state:
        st.session_state.pomo_mode = 'work'  # work | break
    col1, col2, col3 = st.columns(3)
    with col1:
        work_min = st.number_input("Çalışma (dk)", min_value=10, max_value=120, value=25, step=5)
    with col2:
        break_min = st.number_input("Mola (dk)", min_value=3, max_value=30, value=5, step=1)
    with col3:
        cycles = st.number_input("Döngü", min_value=1, max_value=12, value=1, step=1)
    if st.button("Başlat" if not st.session_state.pomo_running else "Durdur", use_container_width=True):
        if not st.session_state.pomo_running:
            duration = work_min if st.session_state.pomo_mode == 'work' else break_min
            st.session_state.pomo_end = time.time() + duration * 60
            st.session_state.pomo_running = True
        else:
            st.session_state.pomo_running = False
    if st.button("Sıfırla", use_container_width=True):
        st.session_state.pomo_running = False
        st.session_state.pomo_end = None
        st.session_state.pomo_mode = 'work'
    remaining_placeholder = st.empty()
    phase_placeholder = st.empty()
    progress_placeholder = st.empty()
    if st.session_state.pomo_running and st.session_state.pomo_end:
        remaining = max(0, int(st.session_state.pomo_end - time.time()))
        mins = remaining // 60
        secs = remaining % 60
        phase_placeholder.markdown(f"**Aşama:** {'Çalışma' if st.session_state.pomo_mode=='work' else 'Mola'}")
        remaining_placeholder.markdown(f"**Kalan Süre:** {mins:02d}:{secs:02d}")
        total = (work_min if st.session_state.pomo_mode=='work' else break_min) * 60
        progress = 1 - (remaining / total if total else 1)
        progress_placeholder.progress(progress)
        if remaining == 0:
            st.session_state.pomo_running = False
            st.session_state.pomo_mode = 'break' if st.session_state.pomo_mode == 'work' else 'work'
            st.success("Aşama tamamlandı! Bir sonraki aşamaya geçmek için Başlat'a basın.")
    else:
        phase_placeholder.markdown(f"**Aşama:** {'Çalışma' if st.session_state.pomo_mode=='work' else 'Mola'}")
        remaining_placeholder.markdown("**Kalan Süre:** Hazır")

if __name__ == "__main__":
    main()
