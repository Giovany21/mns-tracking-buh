import streamlit as st
import pandas as pd

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(page_title="MNS Document Tracking", layout="centered", page_icon="📑")

# --- 2. DATABASE UTAMA (LINK DIRECT DOWNLOAD ONEDRIVE) ---
EXCEL_LINK = "https://onedrive.live.com/download?cid=DD9FA8FB69B8D724&resid=DD9FA8FB69B8D724%21142234&authkey=AHqOZdbUt51LujM"

@st.cache_data(ttl=5) # Percepat refresh menjadi 5 detik untuk pengetesan
def load_data_from_excel():
    try:
        # Buka file excel untuk membaca seluruh nama sheet yang ada secara dinamis
        excel_file = pd.ExcelFile(EXCEL_LINK)
        sheet_names = excel_file.sheet_names
        
        # Cari sheet dokumen (bisa Dokumen atau dokumen)
        sheet_doc = [s for s in sheet_names if 'dokumen' in s.lower()][0]
        # Cari sheet users (bisa Users atau users)
        sheet_user = [s for s in sheet_names if 'user' in s.lower()][0]
        
        df_docs = excel_file.parse(sheet_doc)
        df_depts = excel_file.parse(sheet_user)
        
        # Bersihkan spasi kosong di nama kolom
        df_docs.columns = df_docs.columns.str.strip().str.lower()
        df_depts.columns = df_depts.columns.str.strip().str.lower()
        
        return df_docs, df_depts
    except Exception as e:
        st.error("Gagal membaca struktur Excel. Silakan pastikan file Excel di OneDrive Anda tidak sedang ditutup paksa atau rusak.")
        return pd.DataFrame(), pd.DataFrame()

# Memuat data ke memori aplikasi
db_tracking_dokumen, db_departments = load_data_from_excel()

# --- 3. MANAJEMEN STATE LOGIN ---
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.session_dept = None

st.write("## 📑 Document Tracking System (BUH Sign)")
st.write("Multi Nabati Sulawesi — Independent Portal")
st.markdown("---")

# --- 4. HALAMAN INPUT LOGIN DEPARTEMEN ---
if not st.session_state.is_logged_in:
    st.subheader("🔑 Login Portal Departemen")
    
    if not db_departments.empty:
        # Deteksi nama kolom secara fleksibel
        col_dept = 'dept_name' if 'dept_name' in db_departments.columns else db_departments.columns[0]
        col_pass = 'password' if 'password' in db_departments.columns else db_departments.columns[1]
        
        list_dept = db_departments[col_dept].dropna().unique().tolist()
        dept_input = st.selectbox("Pilih Departemen Anda", ["-- Pilih Departemen --"] + list_dept)
        password_input = st.text_input("Masukkan Password Akses", type="password")
        
        if st.button("Masuk ke Sistem", use_container_width=True):
            if dept_input == "-- Pilih Departemen --":
                st.warning("Silakan pilih salah satu departemen terlebih dahulu!")
            elif not password_input:
                st.warning("Kolom password tidak boleh kosong!")
            else:
                # Validasi login kustom
                match = db_departments[
                    (db_departments[col_dept].astype(str).str.strip().str.upper() == dept_input.strip().upper()) & 
                    (db_departments[col_pass].astype(str).str.strip() == password_input.strip())
                ]
                
                if not match.empty:
                    st.session_state.is_logged_in = True
                    st.session_state.session_dept = dept_input
                    st.rerun()
                else:
                    st.error("Password salah! Silakan periksa kembali atau hubungi Sekretaris (Abygaile).")
    else:
        st.info("Sedang menyinkronkan data akses dari OneDrive...")

# --- 5. HALAMAN UTAMA MONITORING (SETELAH LOG IN BERHASIL) ---
else:
    current_dept = st.session_state.session_dept
    
    st.sidebar.write(f"### 🏢 Departemen:")
    st.sidebar.info(f"**{current_dept}**")
    
    if st.sidebar.button("Keluar (Log Out)", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.session_dept = None
        st.rerun()

    st.subheader(f"📊 Progress Kontrol Dokumen - {current_dept}")
    st.markdown("Berikut adalah tabel kontrol dokumen internal departemen Anda:")
    
    if not db_tracking_dokumen.empty:
        col_doc_dept = 'department' if 'department' in db_tracking_dokumen.columns else 'departemen'
        
        if col_doc_dept in db_tracking_dokumen.columns:
            db_tracking_dokumen['dept_clean'] = db_tracking_dokumen[col_doc_dept].astype(str).str.strip().str.upper()
            df_filtered = db_tracking_dokumen[db_tracking_dokumen['dept_clean'] == current_dept.strip().upper()]
            
            if df_filtered.empty:
                st.info(f"Saat ini tidak ada dokumen dari departemen {current_dept} yang sedang diproses di meja BUH.")
            else:
                # Mengikuti susunan 8 kolom yang Anda berikan
                kolom_tampilan = ['department', 'pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']
                kolom_tersedia = [col for col in kolom_tampilan if col in df_filtered.columns]
                
                st.dataframe(
                    df_filtered[kolom_tersedia], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                st.markdown("---")
                st.markdown("### 🔔 Ringkasan & Catatan Penting")
                for _, row in df_filtered.iterrows():
                    urg_val = str(row.get('urgency', '')).upper().strip()
                    is_urgent = "🚨 [URGENT] " if urg_val in ["HIGH", "URGENT"] else ""
                    
                    status_val = str(row.get('status', '')).upper().strip()
                    doc_name = row.get('dokumen', 'Dokumen Tanpa Nama')
                    pic_name = row.get('pic', '-')
                    
                    if status_val == 'COMPLETED' or status_val == 'SELESAI':
                        st.success(f"✅ {is_urgent}**{doc_name}** (PIC: {pic_name}) — Selesai! Pengambilan berkas: {row.get('tanggal_ambil', '-')}")
                    elif status_val == 'REVISION REQUIRED' or status_val == 'PERLU REVISI':
                        st.error(f"⚠️ {is_urgent}**{doc_name}** (PIC: {pic_name}) — Perlu Revisi! Catatan Abygaile: {row.get('remark', '-')}")
                    else:
                        st.info(f"⏳ {is_urgent}**{doc_name}** (PIC: {pic_name}) — Status: *{row.get('status', 'Diproses')}*")
        else:
            st.error("Kolom 'department' tidak ditemukan di Sheet Dokumen Excel Anda.")
    else:
        st.warning("Data dokumen kosong atau gagal dimuat.")
