import streamlit as st
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="MNS Document Tracking", layout="centered")

# --- LINK EXCEL ONLINE ---
# Pastikan link sudah menggunakan format '/x/raw/'
EXCEL_LINK = "https://1drv.ms/x/raw/c/dd9fa8fb69b8d724/IQB6jkXW1LudS7oz316-zqmrAeNhk3ueihmJXOUsTSoo2oo?e=yWQEJq" 

@st.cache_data(ttl=30) # Sinkronisasi otomatis dari Excel setiap 30 detik
def load_data():
    try:
        df_docs = pd.read_excel(EXCEL_LINK, sheet_name="Dokumen")
        df_depts = pd.read_excel(EXCEL_LINK, sheet_name="Users")
        return df_docs, df_depts
    except Exception as e:
        st.error("Gagal memuat database Excel. Periksa kembali format link '/x/raw/' Anda.")
        return pd.DataFrame(), pd.DataFrame()

# Memuat data terbaru
db_tracking_dokumen, db_departments = load_data()

# --- STATE LOGIN ---
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.session_dept = None

st.write("## 📑 Document Tracking System (BUH Sign)")
st.write("Multi Nabati Sulawesi — Independent Portal")
st.markdown("---")

# --- 1. HALAMAN LOGIN PORTAL DEPARTEMEN ---
if not st.session_state.is_logged_in:
    st.subheader("🔑 Login Portal Departemen")
    
    if not db_departments.empty:
        list_dept = db_departments['dept_name'].dropna().tolist()
        dept_input = st.selectbox("Pilih Departemen Anda", ["-- Pilih Departemen --"] + list_dept)
        password_input = st.text_input("Masukkan Password", type="password")
        
        if st.button("Masuk ke Sistem", use_container_width=True):
            if dept_input == "-- Pilih Departemen --":
                st.warning("Silakan pilih departemen terlebih dahulu!")
            elif not password_input:
                st.warning("Password wajib diisi!")
            else:
                # Validasi kecocokan departemen dan password
                match = db_departments[
                    (db_departments['dept_name'] == dept_input) & 
                    (db_departments['password'].astype(str) == password_input.strip())
                ]
                
                if not match.empty:
                    st.session_state.is_logged_in = True
                    st.session_state.session_dept = dept_input
                    st.rerun()
                else:
                    st.error("Password salah. Silakan hubungi Sekretaris (Abygaile).")
    else:
        st.info("Memuat data departemen dari Excel...")

# --- 2. HALAMAN UTAMA PROGRESS DOKUMEN ---
else:
    current_dept = st.session_state.session_dept
    
    # Sidebar Info Akses & Keluar
    st.sidebar.write(f"### 🏢 Departemen:")
    st.sidebar.info(f"**{current_dept}**")
    
    if st.sidebar.button("Keluar (Log Out)", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.session_dept = None
        st.rerun()

    st.subheader(f"📊 Progress Dokumen - {current_dept}")
    st.markdown("Berikut adalah tabel kontrol dokumen internal departemen Anda:")
    
    # FILTER UTAMA: Menyaring dokumen berdasarkan departemen yang login
    if not db_tracking_dokumen.empty:
        # Sinkronisasi format string teks untuk menghindari error spasi/huruf besar-kecil
        db_tracking_dokumen['dept_clean'] = db_tracking_dokumen['department'].astype(str).str.strip().str.upper()
        df_filtered = db_tracking_dokumen[db_tracking_dokumen['dept_clean'] == current_dept.strip().upper()]
        
        if df_filtered.empty:
            st.info(f"Saat ini tidak ada dokumen aktif dari departemen {current_dept} di meja BUH.")
        else:
            # Mengurutkan tampilan kolom secara berurutan sesuai 8 kriteria yang Anda minta
            kolom_tampilan = ['department', 'pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']
            kolom_ada = [col for col in kolom_tampilan if col in df_filtered.columns]
            
            # Tampilkan data secara rapi (Read-Only)
            st.dataframe(
                df_filtered[kolom_ada], 
                use_container_width=True, 
                hide_index=True
            )
            
            # Fitur Highlight Berkas Penting di bawah tabel
            st.markdown("---")
            st.markdown("### 🔔 Ringkasan & Catatan Penting")
            for _, row in df_filtered.iterrows():
                # Tambah penanda khusus jika urgency di Excel diisi "HIGH" atau "URGENT"
                status_urgency = str(row.get('urgency', '')).upper()
                is_urgent = "🚨 [URGENT] " if status_urgency in ["HIGH", "URGENT"] else ""
                
                status_doc = str(row.get('status', '')).upper()
                if status_doc == 'COMPLETED':
                    st.success(f"✅ {is_urgent}**{row['dokumen']}** (PIC: {row['pic']}) — Selesai! Diambil: {row.get('tanggal_ambil', '-')}")
                elif status_doc == 'REVISION REQUIRED':
                    st.error(f"⚠️ {is_urgent}**{row['dokumen']}** (PIC: {row['pic']}) — Perlu Revisi! Catatan: {row.get('remark', '-')}")
                else:
                    st.info(f"⏳ {is_urgent}**{row['dokumen']}** (PIC: {row['pic']}) — Status: *{row.get('status', 'Diproses')}*")
    else:
        st.warning("Data dokumen kosong atau gagal dimuat dari Excel.")