import streamlit as st
import pandas as pd
import plotly.express as px
from stravalib.client import Client
import datetime

# --- AYARLAR ---
st.set_page_config(page_title="RunMaster Final", page_icon="⚡", layout="wide")

# --- VERİ VE FONKSİYONLAR ---
# Veri Yapısı
def get_data():
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns=["Tarih", "Mesafe (km)", "Süre (dk)", "Tempo", "Kalori", "Hissiyat", "Kaynak"])
    return st.session_state.df

# Data frame'e satır ekleme fonksiyonu
def add_run(new_row):
    st.session_state.df = pd.concat([st.session_session_state.df, new_row], ignore_index=True)

# --- ANA EKRAN BAŞLANGICI ---
st.title("⚡ RunMaster PRO: Tam Otomatik Strava Veri Analizi")

# --- STRAVA ENTEGRASYONU (Sidebar) ---
with st.sidebar:
    st.header("🔗 Strava Bağlantısı")
    st.info("API Bilgilerinizi Buraya Girin:")
    
    client_id = st.text_input("Client ID", value="186085") # Örnek ID ile başlama
    client_secret = st.text_input("Client Secret", type="password")
    
    auth_url = ""
    if client_id and client_secret:
        try:
            client = Client()
            # Yetki Verme Linki Oluşturma
            auth_url = client.authorization_url(
                client_id=client_id,
                redirect_uri='https://share.streamlit.io', # Streamlit Cloud adresi
                scope=['read_all','activity:read_all']
            )
        except:
            pass 

# --- SEKMELER ---
tab1, tab2, tab3 = st.tabs(["📊 Özet ve Grafikler", "☁️ Strava Veri Çekme", "✍️ Manuel Veri Girişi"])

# SEKME 1: DASHBOARD
with tab1:
    st.header("Genel Performans Özeti")
    df = get_data()
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Koşu (km)", f"{df['Mesafe (km)'].sum():.1f} km")
        col2.metric("Ortalama Tempo", f"{df['Tempo'].mode()[0] if not df['Tempo'].empty else 'N/A'}")
        col3.metric("Kayıt Sayısı", len(df))
        
        st.subheader("Koşu Dağılım Grafiği")
        # Plotly kütüphanesini kullanırız
        try:
            st.plotly_chart(px.bar(df, x="Tarih", y="Mesafe (km)", color="Kaynak", title="Tarihe Göre Mesafe"))
        except Exception as e:
            st.warning("Grafik için yeterli veri yok.")
    else:
        st.info("Lütfen Strava'dan veri çekin veya manuel giriş yapın.")

# SEKME 2: STRAVA İŞLEMLERİ (Hata yakalayan bölüm)
with tab2:
    st.header("Adım Adım Strava Yetkilendirme")
    
    if auth_url:
        # Adım 1: İzin Verme Butonu
        st.markdown(f'<a href="{auth_url}" style="display: inline-block; padding: 12px 20px; background-color: #FC4C02; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">🚀 1. Adım: Strava Hesabına İzin Ver</a>', unsafe_allow_html=True)
        st.caption("👆 Butona tıkla, izin ver ve geri dönen adresteki 'code=...' kısmını kopyala.")
    else:
        st.warning("⬅️ Önce sol menüden Client ID ve Secret gir.")
    
    st.divider()

    # Adım 2: Kodu Yapıştır ve Çek (YAPISAL HATA ÇÖZÜMÜ: st.form_submit_button KULLANILDI)
    with st.form("strava_code_exchange"):
        code_input = st.text_input("🚀 2. Adım: İzin Kodunu Buraya Yapıştır")
        submitted = st.form_submit_button("Verileri Getir 📥") # Hata veren st.button() yerine bu kullanılır.
    
        if submitted and code_input:
            st.info("Veriler alınıyor, lütfen bekleyin...")
            
            # Tüm API Hatalarını Yakalayan Ana Try-Except Bloğu
            try:
                # Token Alışverişi
                client = Client()
                token_response = client.exchange_code_for_token(
                    client_id=client_id, client_secret=client_secret, code=code_input
                )
                client.access_token = token_response['access_token']
                
                activities = client.get_activities(limit=5)
                st.success("Bağlantı Başarılı! İşte son aktivitelerin:")
                
                # --- HATA YAKALAYICI AKTİVİTE DÖNGÜSÜ ---
                for act in activities:
                    
                    # 1. MESAFE HESAPLAMA (km) - Tüm olası attribute hatalarını yakalar
                    try: 
                        km = round(act.distance.meters / 1000, 2)
                    except AttributeError:
                        try:
                            km = round(act.distance.magnitude / 1000, 2)
                        except (AttributeError, TypeError):
                            km = round(act.distance / 1000, 2) # En sade deneme

                    # 2. SÜRE HESAPLAMA (dk) - Tüm olası attribute hatalarını yakalar
                    try:
                        dk = int(act.moving_time.total_seconds() / 60)
                    except AttributeError:
                        try:
                            dk = int(act.moving_time.seconds / 60)
                        except (AttributeError, TypeError):
                            dk = int(act.moving_time / 60) # En sade deneme
                            
                    # Diğer veriler
                    date = act.start_date_local.date()
                    name = act.name
                    
                    # --- ARABİRİM KISMI ---
                    with st.expander(f"🏃 {date} - {name} ({km} km)"):
                        st.write(f"Süre: {dk} dk | Tempo: {act.average_speed}")

                        if st.button(f"Bu Koşuyu Veritabanına Ekle ({name})", key=act.id):
                            pace = f"{int(dk/km)}:{int(((dk/km)%1)*60):02d}" if km>0 else "0:00"
                            new_row = pd.DataFrame([{"Tarih": date, "Mesafe (km)": km, "Süre (dk)": dk, "Tempo": pace, "Kalori": int(dk*12), "Hissiyat": "İyi", "Kaynak": "Strava"}])
                            add_run(new_row)
                            st.success("Veritabanına eklendi!")
                            
            except Exception as e:
                st.error(f"HATA: Bağlantı veya Kod Hatası. Tekrar izin alıp deneyin. Detay: {e}")

# SEKME 3: MANUEL GİRİŞ
with tab3:
    st.write("Elle veri girişi (Eski yöntem).")
    # ... (Manuel giriş formu buraya eklenebilir)