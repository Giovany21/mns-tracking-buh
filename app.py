import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="MNS Document Tracking", layout="wide", page_icon="📑")

# --- 2. KONEKSI KE SUPABASE (DENGAN PEMBERSIH URL OTOMATIS) ---
@st.cache_resource
def init_connection():
    raw_url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # SISTEM PEMBERSIH OTOMATIS: Mencegah Eror PGRST125
    clean_url = raw_url.split("/rest/v1")[0].strip().rstrip("/")
    
    return create_client(clean_url, key)

supabase: Client = init_connection()

# Fungsi Tarik Data
def get_users():
    response = supabase.table("users").select("*").execute()
    return pd.DataFrame(response.data)

def get_dokumen():
    response = supabase.table("dokumen").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

# --- 3. MANAJEMEN LOGIN ---
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.session_dept = None
    st.session_state.session_role = None

st.title("📑 Document Tracking System (BUH Sign)")
st.write("Multi Nabati Sulawesi — Independent Portal")
st.markdown("---")

# --- 4. HALAMAN LOGIN ---
if not st.session_state.is_logged_in:
    st.subheader("🔑 Login Portal Departemen")
    
    try:
        db_users = get_users()
        
        if not db_users.empty:
            list_dept = db_users['dept_name'].tolist()
            dept_input = st.selectbox("Pilih Departemen Anda", ["-- Pilih Departemen --"] + list_dept)
            password_input = st.text_input("Masukkan Password Akses", type="password")
            
            if st.button("Masuk ke Sistem", use_container_width=True):
                if dept_input == "-- Pilih Departemen --" or not password_input:
                    st.warning("Pastikan departemen dipilih dan password diisi!")
                else:
                    match = db_users[(db_users['dept_name'] == dept_input) & (db_users['password'] == password_input)]
                    if not match.empty:
                        st.session_state.is_logged_in = True
                        st.session_state.session_dept = dept_input
                        st.session_state.session_role = match.iloc[0]['role']
                        st.rerun()
                    else:
                        st.error("Password salah! Silakan hubungi Sekretaris.")
        else:
            st.error("Gagal terhubung: Tabel Pengguna kosong.")
    except Exception as e:
        st.error(f"Sistem gagal menarik data dari Supabase. Eror: {e}")

# --- 5. HALAMAN UTAMA (SETELAH LOGIN) ---
else:
    current_dept = st.session_state.session_dept
    current_role = st.session_state.session_role
    
    st.sidebar.write("### 🏢 Logged in as:")
    st.sidebar.info(f"**{current_dept}**\n\n(Role: {current_role.upper()})")
    
    if st.sidebar.button("Keluar (Log Out)", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.session_dept = None
        st.session_state.session_role = None
        st.rerun()

    df_docs = get_dokumen()

    # ==========================================
    # BAGIAN A: TAMPILAN ADMIN (KHUSUS ABYGAILE)
    # ==========================================
    if current_role == 'admin':
        st.subheader("🛠️ Admin Dashboard - Kontrol Penuh Dokumen")
        
        tab_tambah, tab_update, tab_database = st.tabs(["➕ Tambah Dokumen Baru", "📝 Update Status Berkas", "🗂️ Lihat Semua Database"])
        
        with tab_tambah:
            with st.form("form_tambah"):
                st.write("Masukkan data berkas yang baru diterima:")
                col1, col2 = st.columns(2)
                with col1:
                    i_dept = st.text_input("Departemen Pengusul (cth: COST CONTROL)")
                    i_pic = st.text_input("Nama PIC")
                    i_dokumen = st.text_input("Nama Dokumen")
                with col2:
                    i_tgl_masuk = st.date_input("Tanggal Masuk")
                    i_urgency = st.selectbox("Urgency", ["Normal", "High", "Urgent"])
                
                if st.form_submit_button("Simpan Dokumen ke Database"):
                    if i_dept and i_dokumen:
                        supabase.table("dokumen").insert({
                            "department": i_dept.upper(), "pic": i_pic, "dokumen": i_dokumen,
                            "tanggal_masuk": str(i_tgl_masuk), "urgency": i_urgency, "status": "Received"
                        }).execute()
                        st.success("Dokumen berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("Departemen dan Nama Dokumen wajib diisi!")

        with tab_update:
            if not df_docs.empty:
                df_docs['dropdown_label'] = df_docs['id'].astype(str) + " - " + df_docs['dokumen'] + " (" + df_docs['department'] + ")"
                pilihan_dokumen = st.selectbox("Pilih Dokumen yang ingin di-update:", df_docs['dropdown_label'])
                
                if pilihan_dokumen:
                    doc_id = int(pilihan_dokumen.split(" - ")[0])
                    doc_terpilih = df_docs[df_docs['id'] == doc_id].iloc[0]
                    
                    with st.form("form_update"):
                        st.write(f"Mengubah status untuk: **{doc_terpilih['dokumen']}**")
                        
                        status_tersedia = ["Received", "Pending BUH", "Revision Required", "Completed"]
                        status_awal = doc_terpilih['status'] if doc_terpilih['status'] in status_tersedia else "Received"
                        
                        u_status = st.selectbox("Update Status:", status_tersedia, index=status_tersedia.index(status_awal))
                        u_remark = st.text_input("Catatan Tambahan (Remark):", value=doc_terpilih['remark'] if pd.notna(doc_terpilih['remark']) else "")
                        
                        # MODIFIKASI: Membaca data tanggal dari DB. Jika kosong, set ke None agar kalender kosong.
                        tgl_ambil_db = doc_terpilih.get('tanggal_ambil')
                        tgl_awal = pd.to_datetime(tgl_ambil_db).date() if pd.notna(tgl_ambil_db) and tgl_ambil_db != "" else None
                        
                        # Menggunakan value=tgl_awal (bisa bernilai None sehingga inputan kosong)
                        u_tgl_ambil = st.date_input("Tanggal Ambil (Kosongkan jika belum selesai diambil):", value=tgl_awal)
                        
                        if st.form_submit_button("Update Status Dokumen"):
                            # Konversi tanggal ke teks YYYY-MM-DD jika diisi, jika kosong kirim None (NULL)
                            tgl_simpan = str(u_tgl_ambil) if u_tgl_ambil is not None else None
                            
                            supabase.table("dokumen").update({
                                "status": u_status, 
                                "remark": u_remark, 
                                "tanggal_ambil": tgl_simpan
                            }).eq("id", doc_id).execute()
                            
                            st.success("Status berhasil di-update!")
                            st.rerun()
                            
        with tab_database:
            st.dataframe(df_docs[['id', 'department', 'pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']], use_container_width=True)

    # ==========================================
    # BAGIAN B: TAMPILAN USER BIASA (READ-ONLY)
    # ==========================================
    else:
        st.subheader(f"📊 Pantau Dokumen - {current_dept}")
        
        if not df_docs.empty:
            df_docs['dept_clean'] = df_docs['department'].astype(str).str.strip().str.upper()
            df_filtered = df_docs[df_docs['dept_clean'] == current_dept.strip().upper()]
            
            if df_filtered.empty:
                st.info("Tidak ada dokumen aktif untuk departemen Anda.")
            else:
                kolom_tampilan = ['pic', 'dokumen', 'tanggal_masuk', 'tanggal_ambil', 'urgency', 'status', 'remark']
                df_filtered['status_clean'] = df_filtered['status'].astype(str).str.strip().str.upper()
                df_completed = df_filtered[df_filtered['status_clean'] == 'COMPLETED']
                df_outstanding = df_filtered[df_filtered['status_clean'] != 'COMPLETED']
                
                tab_out, tab_comp = st.tabs(["⏳ Outstanding (Dalam Proses)", "✅ Completed (Selesai)"])
                
                with tab_out:
                    st.dataframe(df_outstanding[kolom_tampilan], use_container_width=True, hide_index=True)
                with tab_comp:
                    st.dataframe(df_completed[kolom_tampilan], use_container_width=True, hide_index=True)
