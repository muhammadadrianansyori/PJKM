import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
from datetime import datetime
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import requests

# Import custom modules
from modules.street_mapper import StreetMapper
from config.bkd_config import BOUNDARY_GEOJSON_PATH

# Page Config
st.set_page_config(
    layout="wide",
    page_title="Pemetaan Jalan & Gang - Kota Mataram",
    page_icon="🛣️"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #f8fafc;
        border-left: 5px solid #3b82f6;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #1e293b;
    }
    .stMetric {
        background-color: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div class="main-header">
    <h1>🛣️ Sistem Pemetaan Jalan & Gang</h1>
</div>
""", unsafe_allow_html=True)

# Helper function
def normalize_street_name(name):
    """Normalize street name by expanding abbreviations"""
    if pd.isna(name):
        return ""
    name = str(name).strip()
    replacements = [
        (r'\bGg\.?\s+', 'Gang '), (r'\bJl\.?\s+', 'Jalan '),
        (r'\bJln\.?\s+', 'Jalan '), (r'\bJln\b', 'Jalan'),
        (r'\bGg\b', 'Gang'), (r'\bJl\b', 'Jalan'),
    ]
    for pattern, replacement in replacements:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
    return ' '.join(name.split()).lower()

# Initialize street mapper
try:
    street_mapper = StreetMapper(BOUNDARY_GEOJSON_PATH)
    
    # Kecamatan selection
    kec_list = street_mapper.get_kecamatan_list()
    selected_kec = st.selectbox("📍 Pilih Kecamatan untuk Pemetaan", kec_list)
    
    if st.button("🚀 Proses Data Jalan", type="primary", use_container_width=True):
        with st.spinner(f"Mengambil data dari OpenStreetMap & mencocokkan batas untuk {selected_kec}..."):
            data = street_mapper.map_streets_to_admin(selected_kec)
            st.session_state['standalone_data'] = data
            st.session_state['standalone_kec'] = selected_kec

    # Display results
    if 'standalone_data' in st.session_state and st.session_state['standalone_kec'] == selected_kec:
        df = st.session_state['standalone_data']
        
        if df.empty:
            st.warning("⚠️ Data tidak ditemukan.")
        else:
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🛣️ Total Jalan", f"{len(df)} item")
            m2.metric("📍 Kelurahan", f"{df['Kelurahan'].nunique()}")
            m3.metric("🏘️ Lingkungan", f"{df['Lingkungan'].nunique()}")
            m4.metric("📋 RT", f"{df['SLS'].nunique()}")
            
            # Map search & filters
            st.subheader("🗺️ Peta Interaktif")
            s_col, t_col = st.columns([3, 1])
            with s_col:
                names = ["--- Fokus ke Jalan ---"] + sorted(df['Nama Jalan dan Gang'].unique().tolist())
                sel_street = st.selectbox("Cari Jalan:", names)
            with t_col:
                show_rt = st.checkbox("Batas Administrasi", value=True)
            
            # Folium Map
            clat, clon = df['Latitude'].mean(), df['Longitude'].mean()
            m = folium.Map(location=[clat, clon], zoom_start=14, tiles='Cartodb Positron')
            
            if show_rt:
                bounds = street_mapper.sls_gdf[street_mapper.sls_gdf['nmkec'] == selected_kec.upper()]
                for _, b in bounds.iterrows():
                    folium.GeoJson(b['geometry'], style_function=lambda x:{'fillColor':'#3b82f622','color':'#3b82f6','weight':1.5,'dashArray':'5,5'}).add_to(m)
            
            for _, r in df.iterrows():
                folium.CircleMarker([r['Latitude'], r['Longitude']], radius=4, color='#ef4444', fill=True, 
                                    popup=f"<b>{r['Nama Jalan dan Gang']}</b><br>{r['SLS']}").add_to(m)
            
            if sel_street != "--- Fokus ke Jalan ---":
                p = df[df['Nama Jalan dan Gang'] == sel_street].iloc[0]
                m.location, m.zoom_start = [p['Latitude'], p['Longitude']], 17
            
            st_folium(m, width="100%", height=500, returned_objects=[])

            # Data & Export
            st.subheader("📋 Tabel Data Final")
            st.dataframe(df, use_container_width=True)
            
            # Professional Excel Export
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
                # (Simple formatting for standalone version)
            
            st.download_button("📥 Download Laporan (Excel)", output.getvalue(), f"peta_jalan_{selected_kec}.xlsx")

            # Google Sheets Validation
            st.markdown("---")
            st.subheader("✅ Validasi dengan Google Sheets")
            gs_url = st.text_input("Link Google Sheets (Publik):")
            if st.button("Mulai Validasi"):
                try:
                    # GID Extraction
                    gid = "0"
                    if "gid=" in gs_url: gid = gs_url.split("gid=")[1].split("&")[0]
                    csv_url = gs_url.replace("/edit#", "/export?format=csv&") + f"&gid={gid}"
                    df_ref = pd.read_csv(csv_url)
                    
                    # Normalize & Match
                    df_match = df.copy()
                    df_match['norm'] = df_match['Nama Jalan dan Gang'].apply(normalize_street_name)
                    # (Matching logic simplified for standalone)
                    st.success(f"Berhasil memuat {len(df_ref)} data pembanding.")
                    st.dataframe(df_ref.head())
                except:
                    st.error("Gagal memuat data. Periksa apakah link sudah 'Public' (Anyone with the link can view)")

except Exception as e:
    st.error(f"Inisialisasi Gagal: {e}")

