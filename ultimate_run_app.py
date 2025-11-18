import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import gpxpy
import time

# --- AYARLAR ---
st.set_page_config(page_title="RunMaster Titan", page_icon="🏃", layout="centered")

# --- FONKSİYONLAR ---
def get_data():
    # Streamlit Cloud'da veriler silinmesin diye hafızada (Cache) tutuyoruz
    # Not: Gerçek kalıcılık için veritabanı gerekir ama bu başlangıç için yeterli.
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns=["Tarih", "Mesafe (km)", "Süre (dk)", "Tempo", "Kalori", "Hissiyat", "Kaynak"])
    return st.session_state.df

def save_run(new_row):
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)

def parse_gpx(file):
    try:
        gpx = gpxpy.parse(file)
        moving_data = gpx.get_moving_data()
        dist = moving_data.moving_distance / 1000
        dur = moving_data.moving_time / 60
        date = gpx.time.date() if gpx.time else datetime.date.today()
        route = [{"lat": p.latitude, "lon": p.longitude} for t in gpx.tracks for s in t.segments for p in s.points]
        return dist, dur, date, route
    except:
        return 0, 0, datetime.date.today(), []

# --- TASARIM ---
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🏃 RunMaster TITAN</h1>", unsafe_allow_html=True)

# --- ANA EKRAN ---
df = get_data()
tab1, tab2, tab3 = st.tabs(["📊 Özet", "➕ Ekle", "🤖 Koç"])

with tab1:
    if not df.empty:
        total_km = df["Mesafe (km)"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Toplam Mesafe", f"{total_km:.1f} km")
        c2.metric("Koşu Sayısı", len(df))
        st.progress(min(total_km/50, 1.0))
        st.caption("Aylık Hedef: 50km")
        st.plotly_chart(px.bar(df, x="Tarih", y="Mesafe (km)", color="Hissiyat"), use_container_width=True)
    else:
        st.info("Henüz koşu kaydı yok. 'Ekle' sekmesine git!")

with tab2:
    mode = st.radio("Giriş Türü", ["Manuel", "GPS Dosyası"], horizontal=True)
    if mode == "Manuel":
        with st.form("entry_form"):
            d = st.date_input("Tarih")
            km = st.number_input("Mesafe (km)", 0.0)
            dk = st.number_input("Süre (dk)", 0)
            feel = st.select_slider("Hissiyat", ["Kötü", "Normal", "İyi", "Süper"])
            if st.form_submit_button("Kaydet"):
                pace = f"{int(dk/km)}:{int(((dk/km)%1)*60):02d}" if km>0 else "0:00"
                new_row = pd.DataFrame([{"Tarih": d, "Mesafe (km)": km, "Süre (dk)": dk, "Tempo": pace, "Kalori": km*60, "Hissiyat": feel, "Kaynak": "Manuel"}])
                save_run(new_row)
                st.success("Kaydedildi!")
                st.experimental_rerun()
    else:
        up_file = st.file_uploader("GPX Yükle", type=['gpx'])
        if up_file:
            dist, dur, date, route = parse_gpx(up_file)
            st.success(f"GPS Okundu: {dist:.2f} km")
            if route: st.map(pd.DataFrame(route))
            if st.button("Kaydet"):
                pace = f"{int(dur/dist)}:{int(((dur/dist)%1)*60):02d}" if dist>0 else "0:00"
                new_row = pd.DataFrame([{"Tarih": date, "Mesafe (km)": round(dist,2), "Süre (dk)": int(dur), "Tempo": pace, "Kalori": int(dur*10), "Hissiyat": "Normal", "Kaynak": "GPS"}])
                save_run(new_row)
                st.success("GPS Kaydedildi!")
                st.experimental_rerun()

with tab3:
    goal = st.selectbox("Hedef Seç", ["5K Başlangıç", "10K Geliştirme", "Kilo Verme"])
    if st.button("Plan Oluştur"):
        st.success(f"Senin için {goal} planı hazırlandı! (Burada yapay zeka planı listelenir)")