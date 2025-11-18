import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import gpxpy
from stravalib.client import Client

# --- AYARLAR ---
st.set_page_config(page_title="RunMaster Auto", page_icon="⚡", layout="centered")

# --- VERİ FONKSİYONLARI ---
def get_data():
    if 'df' not in st.session_state:
        # Veri yoksa boş tablo oluştur
        st.session_state.df = pd.DataFrame(columns=["Tarih", "Mesafe (km)", "Süre (dk)", "Tempo", "Kalori", "Hissiyat", "Kaynak"])
    return st.session_state.df

def save_run(new_row):
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

# --- SOL MENÜ (STRAVA GİRİŞİ BURADA!) ---
with st.sidebar:
    st.header("🔗 Strava Bağlantısı")
    st.info("Strava API bilgilerini buraya gir:")
    
    # İşte aradığın kutucuklar bunlar:
    client_id = st.text_input("Client ID (Sayı olan)")
    client_secret = st.text_input("Client Secret (Uzun şifre)", type="password")
    
    auth_url = ""
    if client_id and client_secret:
        try:
            client = Client()
            auth_url = client.authorization_url(
                client_id=client_id,
                redirect_uri='https://share.streamlit.io',
                scope=['read_all','activity:read_all']
            )
        except:
            st.error("ID hatalı girildi.")

# --- ANA EKRAN ---
st.title("⚡ RunMaster: Strava Modu")

tab1, tab2, tab3 = st.tabs(["📊 Özet", "☁️ Strava'dan Çek", "✍️ Manuel Ekle"])

# SEKME 1: ÖZET
with tab1:
    df = get_data()
    if not df.empty:
        total_km = df["Mesafe (km)"].sum()
        st.metric("Toplam Mesafe", f"{total_km} km")
        st.plotly_chart(px.bar(df, x="Tarih", y="Mesafe (km)", color="Kaynak"))
    else:
        st.info("Henüz koşu yok.")

# SEKME 2: STRAVA İŞLEMLERİ
with tab2:
    st.header("Strava Entegrasyonu")
    
    if auth_url:
        # 1. İzin Verme Butonu
        st.markdown(f'<a href="{auth_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #FC4C02; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">🚀 1. Adım: Strava\'ya İzin Ver</a>', unsafe_allow_html=True)
        st.caption("👆 Butona bas, izin ver, sonra adres çubuğundaki 'code=...' kısmını kopyala.")
        
        st.divider()
        
        # 2. Kod Yapıştırma Alanı
        code = st.text_input("🚀 2. Adım: İzin Kodunu Buraya Yapıştır")
        
        if code:
            if st.button("Verileri İndir 📥"):
                try:
                    token_response = client.exchange_code_for_token(
                        client_id=client_id, client_secret=client_secret, code=code
                    )
                    client.access_token = token_response['access_token']
                    activities = client.get_activities(limit=5)
                    
                    st.success("Bağlandı! Son aktiviteler:")
                    
                    for act in activities:
                        km = round(act.distance.num / 1000, 2)
                        dk = int(act.moving_time.total_seconds() / 60)
                        date = act.start_date_local.date()
                        name = act.name
                        
                        with st.expander(f"🏃 {date} - {name} ({km} km)"):
                            st.write(f"Süre: {dk} dk | Tempo: {act.average_speed}")
                            if st.button("Bu Koşuyu Kaydet", key=act.id):
                                pace = f"{int(dk/km)}:{int(((dk/km)%1)*60):02d}" if km>0 else "0:00"
                                new_row = pd.DataFrame([{"Tarih": date, "Mesafe (km)": km, "Süre (dk)": dk, "Tempo": pace, "Kalori": int(dk*12), "Hissiyat": "İyi", "Kaynak": "Strava"}])
                                save_run(new_row)
                                st.success("Eklendi!")
                                
                except Exception as e:
                    st.error(f"Hata: {e}. Kodu yanlış kopyalamış olabilirsin.")
    else:
        st.warning("⬅️ Önce sol menüden Client ID ve Secret girmen lazım.")

# SEKME 3: MANUEL GİRİŞ
with tab3:
    with st.form("manuel"):
        d = st.date_input("Tarih")
        km = st.number_input("Mesafe", 0.0)
        dk = st.number_input("Süre", 0)
        if st.form_submit_button("Kaydet"):
            new_row = pd.DataFrame([{"Tarih": d, "Mesafe (km)": km, "Süre (dk)": dk, "Tempo": "0:00", "Kalori": 0, "Hissiyat": "Normal", "Kaynak": "Manuel"}])
            save_run(new_row)
            st.success("Kaydedildi!")