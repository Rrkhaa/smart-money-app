import streamlit as st
import pandas as pd
import datetime 
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from supabase import create_client, Client

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Smart Money", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# INISIALISASI SESSION STATE (harus paling awal)
# ==========================================
if "language" not in st.session_state:
    st.session_state.language = "ID"
if "currency" not in st.session_state:
    st.session_state.currency = "IDR"
if "user" not in st.session_state:
    st.session_state.user = None
if "session" not in st.session_state:
    st.session_state.session = None

# Inisialisasi Supabase client di session state agar aman dari polusi session
if "supabase" not in st.session_state:
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        st.session_state.supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error("Gagal menginisialisasi Supabase client. Pastikan file `.streamlit/secrets.toml` telah dibuat dengan URL dan API Key yang benar.")
        st.stop()

# Kurs konversi (1 USD = Rp 16.000)
USD_RATE = 16000

def t(id_text, en_text):
    """Fungsi terjemahan: kembalikan teks sesuai bahasa aktif."""
    return en_text if st.session_state.language == "EN" else id_text

def format_currency(angka):
    """Format angka sesuai mata uang aktif."""
    if pd.isna(angka):
        return "Rp 0" if st.session_state.currency == "IDR" else "$ 0.00"
    try:
        val = float(angka)
        if st.session_state.currency == "USD":
            return f"$ {val / USD_RATE:,.2f}"
        else:
            return f"Rp {int(val):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0" if st.session_state.currency == "IDR" else "$ 0.00"

def format_rp(angka):
    return format_currency(angka)


# ==========================================
# HALAMAN LOGIN / REGISTER (GATING ACCESS)
# ==========================================
if st.session_state.user is None:
    # Selector bahasa di pojok kanan atas
    col_sp, col_lang = st.columns([5, 1.2])
    with col_lang:
        lang_opts = ["🇮🇩 Bahasa Indonesia", "🇺🇸 English"]
        lang_default = 0 if st.session_state.language == "ID" else 1
        sel_lang = st.selectbox("Language / Bahasa", lang_opts, index=lang_default, label_visibility="collapsed")
        new_lang = "ID" if "Bahasa Indonesia" in sel_lang else "EN"
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()

    # Menggunakan container untuk mengatur jarak
    with st.container():
        # Kolom luar untuk menengahkan seluruh konten login
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            # Memaksa konten agak naik agar tidak perlu scroll
            st.markdown("<style>div.block-container{padding-top: 2rem;}</style>", unsafe_allow_html=True)
            
            # Kolom dalam untuk mengecilkan logo
            col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
            with col_img2:
                # Menentukan lebar logo secara spesifik
                st.image("logo.png", width=120)

            # Judul diperkecil ukurannya dan jarak atas-bawah dirapatkan
            st.markdown(f"""
                <div style="text-align: center; margin-top: -15px; margin-bottom: 10px;">
                    <h2 style="background: linear-gradient(45deg, #10B981, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; margin-bottom: 0px;">Smart Money</h2>
                    <p style="opacity: 0.8; font-size: 14px;">{t("Kelola keuangan Anda secara cerdas, otomatis, dan aman", "Manage your finances smartly, automatically, and securely")}</p>
                </div>
            """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs([t("Masuk", "Login"), t("Daftar Akun Baru", "Register")])
        
        with tab_login:
            with st.form("form_login_app"):
                email = st.text_input("Email", placeholder="email@example.com")
                password = st.text_input(t("Kata Sandi", "Password"), type="password", placeholder="••••••••")
                submit_login = st.form_submit_button(t("Masuk", "Sign In"), use_container_width=True, type="primary")
                
                if submit_login:
                    if not email or not password:
                        st.error(t("Email dan kata sandi wajib diisi!", "Email and password are required!"))
                    else:
                        try:
                            supabase = st.session_state.supabase
                            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = res.user
                            st.session_state.session = res.session
                            st.success(t("Berhasil masuk!", "Successfully signed in!"))
                            st.rerun()
                        except Exception as e:
                            err_str = str(e)
                            if "Invalid login credentials" in err_str:
                                st.error(t("Email atau kata sandi salah!", "Invalid email or password!"))
                            else:
                                st.error(f"{t('Gagal masuk', 'Failed to sign in')}: {err_str}")
                                
        with tab_register:
            with st.form("form_register_app"):
                reg_email = st.text_input("Email", placeholder="email@example.com")
                reg_password = st.text_input(t("Kata Sandi (Min 6 Karakter)", "Password (Min 6 Characters)"), type="password", placeholder="••••••••")
                reg_password_confirm = st.text_input(t("Konfirmasi Kata Sandi", "Confirm Password"), type="password", placeholder="••••••••")
                submit_register = st.form_submit_button(t("Daftar", "Sign Up"), use_container_width=True, type="primary")
                
                if submit_register:
                    if not reg_email or not reg_password:
                        st.error(t("Email dan kata sandi wajib diisi!", "Email and password are required!"))
                    elif len(reg_password) < 6:
                        st.error(t("Kata sandi minimal harus 6 karakter!", "Password must be at least 6 characters!"))
                    elif reg_password != reg_password_confirm:
                        st.error(t("Konfirmasi kata sandi tidak cocok!", "Password confirmation does not match!"))
                    else:
                        try:
                            supabase = st.session_state.supabase
                            res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                            st.success(t(
                                "Registrasi sukses! Silakan periksa email Anda untuk memverifikasi akun Anda, kemudian silakan masuk di tab Masuk.",
                                "Registration successful! Please check your email to verify your account, then sign in via the Login tab."
                            ))
                        except Exception as e:
                            st.error(f"{t('Gagal mendaftar', 'Failed to register')}: {e}")
    st.stop()

# ==========================================
# 2. SEEDING & FUNGSI PENGAMBILAN DATA SUPABASE
# ==========================================
def seed_user_data_from_csv(user_id):
    """Fungsi men-seed data default bulanan dari CSV ke Supabase untuk user baru"""
    try:
        df_csv = pd.read_csv('Data_Monthly_Spending.csv', sep=';')
        df_csv.columns = df_csv.columns.str.strip()
        # Bersihkan spasi dan pastikan format Bulan bertipe YYYY-MM-DD
        df_csv['Bulan'] = pd.to_datetime(df_csv['Bulan']).dt.strftime('%Y-%m-%d')
        df_csv['user_id'] = user_id
        
        data_to_insert = df_csv.to_dict(orient='records')
        st.session_state.supabase.table("bulanan").insert(data_to_insert).execute()
    except Exception as e:
        st.error(f"Gagal memuat data default awal: {e}")

def get_data_bulanan():
    try:
        supabase = st.session_state.supabase
        user = st.session_state.user
        if not user:
            return pd.DataFrame()
            
        # Ambil data dari table bulanan filter by user_id
        response = supabase.table("bulanan").select("*").eq("user_id", user.id).execute()
        df = pd.DataFrame(response.data)
        
        # Jika data bulanan masih kosong dan emailnya adalah rakhagg12344@gmail.com, seed dari CSV
        if df.empty and user.email == "rakhagg12344@gmail.com":
            seed_user_data_from_csv(user.id)
            response = supabase.table("bulanan").select("*").eq("user_id", user.id).execute()
            df = pd.DataFrame(response.data)
            
        kolom_lengkap = [
            'Bulan', 'Kebutuhan Pokok', 'Sewa', 'Transportasi', 'Olahraga', 
            'Tagihan', 'Kesehatan', 'Cicilan', 'Makan', 'Hiburan', 
            'Investasi', 'Tabungan', 'Total Pengeluaran', 'Pemasukan'
        ]
        
        if df.empty:
            return pd.DataFrame(columns=kolom_lengkap)
            
        df['Bulan'] = pd.to_datetime(df['Bulan'], errors='coerce')
        df = df.drop(columns=['user_id'], errors='ignore')
        # Urutkan berdasarkan kolom Bulan
        df = df.sort_values('Bulan').reset_index(drop=True)
        # Pastikan seluruh kolom lengkap ada
        for col in kolom_lengkap:
            if col not in df.columns:
                df[col] = 0
        df = df[kolom_lengkap]
        return df.fillna(0)
    except Exception as e:
        st.error(f"Error pembacaan database Supabase (bulanan): {e}")
        kolom_lengkap = [
            'Bulan', 'Kebutuhan Pokok', 'Sewa', 'Transportasi', 'Olahraga', 
            'Tagihan', 'Kesehatan', 'Cicilan', 'Makan', 'Hiburan', 
            'Investasi', 'Tabungan', 'Total Pengeluaran', 'Pemasukan'
        ]
        return pd.DataFrame(columns=kolom_lengkap)

# Eksekusi pengambilan data
df = get_data_bulanan()

# ==========================================
# PENGECEKAN AMAN UNTUK LATEST DATA
# ==========================================
if not df.empty:
    df_sorted = df.sort_values('Bulan')
    latest_data = df_sorted.iloc[-1]
    prev_data = df_sorted.iloc[-2] if len(df_sorted) > 1 else latest_data
else:
    latest_data = pd.Series(dtype='float64')
    prev_data = pd.Series(dtype='float64')

def calc_delta(curr, prev):
    if prev == 0: return 0
    return ((curr - prev) / prev) * 100

# ==========================================
# KONFIGURASI HALAMAN & CSS
# ==========================================
 
st.markdown("""
    <style>
    /* Mengikuti tema Streamlit secara dinamis */
    .stApp { background-color: var(--background-color); }
    
    /* Konfigurasi Kartu (Cards) Dinamis */
    .light-card, .ai-widget, .budget-card { 
        background-color: var(--secondary-background-color); 
        border: 1px solid rgba(128, 128, 128, 0.2); 
        padding: 20px; 
        border-radius: 12px; 
        color: var(--text-color); 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
    }
    
    /* Konfigurasi Teks Dinamis */
    .light-card h4, .budget-subtitle { color: var(--text-color); opacity: 0.7; font-size: 13px; margin-bottom: 8px; font-weight: 500; margin-top: 15px;}
    .light-card h2, .budget-title { color: var(--text-color); margin-top: 0; margin-bottom: 10px; font-size: 24px; font-weight: bold;}
    .light-card p { font-size: 12px; margin: 0; font-weight: 600;}
    
    /* Modifikasi Widget AI */
    .ai-widget-title { color: var(--text-color); font-weight: 600; font-size: 15px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
    
    /* Menggunakan RGBA agar Box Icon tetap cantik di Light maupun Dark Mode */
    .icon-box { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; font-size: 16px; }
    .bg-green { background-color: rgba(22, 163, 74, 0.15); color: #10B981; }
    .bg-red { background-color: rgba(220, 38, 38, 0.15); color: #EF4444; }
    .bg-blue { background-color: rgba(37, 99, 235, 0.15); color: #3B82F6; }
    .bg-teal { background-color: rgba(13, 148, 136, 0.15); color: #14B8A6; }
    
    /* Modifikasi Alert AI dengan transparansi */
    .ai-alert { padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 12px; line-height: 1.5; color: var(--text-color); }
    .ai-alert-red { background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); }
    .ai-alert-green { background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); }
    .ai-alert-blue { background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: var(--secondary-background-color); border-right: 1px solid rgba(128, 128, 128, 0.2); }
    
    /* Progress Bar */
    .prog-bg, .prog-bg-small { width: 100%; background-color: rgba(128, 128, 128, 0.2); border-radius: 10px; overflow: hidden; }
    .prog-bg { height: 6px; margin-bottom: 25px; }
    .prog-bg-small { height: 4px; margin-bottom: 6px; }
    </style>
""", unsafe_allow_html=True)
 
# ==========================================
# SIDEBAR NAVIGATION & THEME SYSTEM
# ==========================================
if st.session_state.language == "ID":
    menu_labels = ["Dasbor", "Transaksi", "Anggaran & Tabungan", "Analisis & Laporan", "Chatbot AI", "Pengaturan"]
else:
    menu_labels = ["Dashboard", "Transaction", "Budget & Saving", "Analysis & Reports", "AI Chatbot", "Settings"]

menu_keys = ["dashboard", "transaction", "budget", "analysis", "chatbot", "settings"]

if "menu_index" not in st.session_state:
    st.session_state.menu_index = 0

if st.session_state.get("go_to_chatbot", False):
    st.session_state.menu_index = menu_keys.index("chatbot") 
    st.session_state.go_to_chatbot = False

with st.sidebar:
    # Menambahkan logo di atas tulisan Sidebar
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.image("logo.png", use_container_width=True)
        
    st.markdown("<h2 style='text-align: center; margin-top: -15px;'>Smart Money</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # --- TOGGLE TEMA ---
    if "dark_theme" not in st.session_state:
        st.session_state.dark_theme = False
        
    # Menghapus simbol emoji bulan
    lbl_tema = t("Mode Gelap", "Dark Mode")
    
    # Membungkus dengan kolom agar posisinya di tengah
    col_t1, col_t2, col_t3 = st.columns([0.2, 2.5, 0.1])
    with col_t2:
        dark_mode_aktif = st.toggle(lbl_tema, value=st.session_state.dark_theme)
    
    if dark_mode_aktif != st.session_state.dark_theme:
        st.session_state.dark_theme = dark_mode_aktif
        st.rerun()

    # ==========================================
    # PALET WARNA (TEMA HIJAU LOGO)
    # ==========================================
    DARK = dict(
        bg="#022C22",             
        surface="#064E3B",        
        text_primary="#F8F9FA",   
        sidebar_border="rgba(167, 243, 208, 0.16)",
        accent="#10B981"
    )
    LIGHT = dict(
        bg="#ECFCCB",             # DIUBAH: Sekarang disamakan dengan warna surface (sidebar)
        surface="#ECFCCB",        # Kartu & Sidebar: Hijau kekuningan
        text_primary="#1E293B",   # Teks: Abu-abu kebiruan gelap agar mudah dibaca
        sidebar_border="rgba(6, 78, 59, 0.12)",
        accent="#10B981"          # Aksen tombol tetap hijau terang
    )
    T = DARK if st.session_state.dark_theme else LIGHT

    # --- PERBAIKAN WARNA SIDEBAR MENU ---
    menu_bg_active = "#065F46" if st.session_state.dark_theme else "#10B981" 
    menu_hover = "rgba(167, 243, 208, 0.16)" if st.session_state.dark_theme else "rgba(16, 185, 129, 0.15)"

    selected_label = option_menu(
        menu_title=None,
        options=menu_labels, 
        icons=["house", "receipt", "wallet2", "bar-chart-line", "robot", "gear"],
        menu_icon="cast",
        default_index=st.session_state.menu_index,
        key=f"sidebar_menu_{st.session_state.menu_index}_{st.session_state.dark_theme}", 
        styles={
            # PERUBAHAN UTAMA: Jangan pakai "transparent", paksa warnanya sesuai palet T['surface']
            "container": {"padding": "10px", "background-color": T['surface']},
            "icon": {"color": T['text_primary'], "opacity": "0.8", "font-size": "16px"}, 
            "nav-link": {
                "font-size": "14px", "text-align": "left", "margin":"5px 0", 
                "border-radius": "8px", "color": T['text_primary'], 
                "opacity": "0.8", "--hover-color": menu_hover, "white-space": "nowrap" 
            },
            "nav-link-selected": { "background-color": menu_bg_active, "color": "#FFFFFF", "font-weight": "600", "opacity": "1" },
        }
    )
    
    # Dapatkan 'key' statis berdasarkan label yang dipilih
    selected_idx = menu_labels.index(selected_label)
    selected = menu_keys[selected_idx]
    
    if selected_idx != st.session_state.menu_index:
        st.session_state.menu_index = selected_idx
        st.rerun()

    st.markdown("---")
    
    # --- CSS INJECTION (MEMPERBAIKI TOMBOL, INPUT & SIDEBAR) ---
    st.markdown(f"""
        <style>
        /* Memaksa background app dan header */
        .stApp, .stApp > header {{
            background-color: {T['bg']} !important;
        }}
        
        /* Memaksa background sidebar menembus layer terdalam */
        section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {{
            background-color: {T['surface']} !important; 
            border-right: 1px solid {T['sidebar_border']} !important; 
        }}
        
        /* Memaksa SEMUA jenis teks berubah warna */
        html, body, p, h1, h2, h3, h4, h5, h6, span, label, li, .stMarkdown, .stText, .b-table th, .b-table td {{
            color: {T['text_primary']} !important;
        }}

        /* Perbaikan Tombol agar background tidak putih */
        .stButton > button {{
            background-color: {T['bg']} !important;
            color: {T['text_primary']} !important;
            border: 1px solid {T['sidebar_border']} !important;
        }}
        .stButton > button:hover {{
            border-color: {T['accent']} !important;
            color: {T['accent']} !important;
        }}
        
        /* Tombol Utama (Masuk, Daftar, Simpan) */
        .stButton > button[kind="primary"] {{
            background-color: {T['accent']} !important;
            color: #ffffff !important;
            border: none !important;
        }}

        /* Perbaikan Kotak Input & Selectbox */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stPasswordInput input {{
            background-color: {T['bg']} !important;
            color: {T['text_primary']} !important;
            border: 1px solid {T['sidebar_border']} !important;
        }}
        div[data-baseweb="select"] > div {{
            background-color: {T['bg']} !important;
            color: {T['text_primary']} !important;
            border: 1px solid {T['sidebar_border']} !important;
        }}

        /* Perbaikan Kotak Chat Chatbot AI */
        .stChatInputContainer {{
            background-color: {T['surface']} !important;
            border: 1px solid {T['sidebar_border']} !important;
        }}
        .stChatInputContainer textarea {{
            color: {T['text_primary']} !important;
        }}
        ::placeholder {{ color: {T['text_primary']} !important; opacity: 0.5 !important; }}
        </style>
    """, unsafe_allow_html=True)
    # --------------------------------------------
    
    # 1. Ambil email user
    user_email = st.session_state.user.email if st.session_state.user else "user@example.com"
        
    # 2. Ambil nama user dari metadata Supabase atau session state
    if "full_name" in st.session_state:
        display_name = st.session_state.full_name
    else:
        user_metadata = st.session_state.user.user_metadata if hasattr(st.session_state.user, 'user_metadata') and st.session_state.user.user_metadata else {}
        display_name = user_metadata.get("full_name", "User")
        # Simpan ke session state agar tidak perlu ngecek berulang-ulang
        st.session_state.full_name = display_name
    
    # 3. Tampilkan nama dan email secara dinamis
    st.markdown(f"🧑‍💼 **{display_name}**\n\n{user_email}")
    
    st.write("")
    if st.button(t("🚪 Keluar", "🚪 Logout"), use_container_width=True):
        st.session_state.user = None
        st.session_state.session = None
        st.rerun()
 
 
# ==========================================
# 1. MENU: HOME
# ==========================================
if selected == "dashboard":
    df['Tahun'] = df['Bulan'].dt.year if not df.empty else []
    lbl_semua_tahun = t("Semua Tahun", "All Years")
    daftar_tahun = [lbl_semua_tahun] + sorted(df['Tahun'].unique().tolist(), reverse=True) if not df.empty else [lbl_semua_tahun]
    
    col_title, col_filter = st.columns([3, 1])
    with col_title:
        judul_dash = t("Dasbor Keuangan", "Financial Dashboard")
        st.title(judul_dash)
        sub_dash = t("Ringkasan kondisi kesehatan finansial Anda", "Summary of your financial health condition")
        st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; margin-top:-15px;'>{sub_dash}</p>", unsafe_allow_html=True)
    with col_filter:
        st.write("") 
        lbl_pilih_tahun = t("Pilih Tahun", "Select Year")
        tahun_pilihan = st.selectbox(lbl_pilih_tahun, daftar_tahun, label_visibility="collapsed")
        
    st.write("")
    
    if tahun_pilihan == lbl_semua_tahun:
        df_filtered = df
        teks_bawah = t("+ Keseluruhan Waktu", "+ All Time")
    else:
        df_filtered = df[df['Tahun'] == tahun_pilihan]
        teks_bawah = t(f"+ Data Tahun {tahun_pilihan}", f"+ Data for Year {tahun_pilihan}")
        
    # 1. Ambil seluruh data anggaran dari database untuk menghitung limit bulanan
    try:
        supabase = st.session_state.supabase
        user_id = st.session_state.user.id
        res_budget_dash = supabase.table("budget").select("nominal").eq("user_id", user_id).execute()
        budget_per_bulan = sum([row['nominal'] for row in res_budget_dash.data]) if res_budget_dash.data else 0
    except:
        budget_per_bulan = 0

    # 2. Hitung jumlah bulan yang sedang aktif/terfilter di layar dasbor
    jumlah_bulan_terfilter = len(df_filtered) if not df_filtered.empty else 0
    total_alokasi_budget_period = budget_per_bulan * jumlah_bulan_terfilter

    # 3. Hitung metrik dasar
    total_pemasukan = df_filtered['Pemasukan'].sum() if not df_filtered.empty else 0
    total_pengeluaran = df_filtered['Total Pengeluaran'].sum() if not df_filtered.empty else 0
    total_saldo = total_pemasukan - total_pengeluaran
    
    # 4. RUMUS BARU DASBOR: Total Tabungan = Total Pemasukan - Total Alokasi Anggaran (sesuai periode filter)
    total_tabungan = total_pemasukan - total_alokasi_budget_period
    
    lbl_tot_pemasukan = t("Total Pemasukan", "Total Income")
    lbl_tot_pengeluaran = t("Total Pengeluaran", "Total Expenses")
    lbl_tot_saldo = t("Total Saldo", "Total Balance")
    lbl_tot_tabungan = t("Total Tabungan", "Total Savings")

    card_style = "background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); padding: 20px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);"
    h4_style = "color: var(--text-color); opacity: 0.7; font-size: 13px; margin-bottom: 8px; font-weight: 500; margin-top: 15px;"
    h2_style = "color: var(--text-color); margin-top: 0; margin-bottom: 10px; font-size: 24px; font-weight: bold;"
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div style="{card_style}"><div class="icon-box bg-teal">💵</div><h4 style="{h4_style}">{lbl_tot_pemasukan}</h4><h2 style="{h2_style}">{format_rp(total_pemasukan)}</h2><p class="text-green" style="margin:0; font-size:12px; font-weight:600;">{teks_bawah}</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div style="{card_style}"><div class="icon-box bg-red">📉</div><h4 style="{h4_style}">{lbl_tot_pengeluaran}</h4><h2 style="{h2_style}">{format_rp(total_pengeluaran)}</h2><p class="text-red" style="margin:0; font-size:12px; font-weight:600;">{teks_bawah}</p></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div style="{card_style}"><div class="icon-box bg-blue">💼</div><h4 style="{h4_style}">{lbl_tot_saldo}</h4><h2 style="{h2_style}">{format_rp(total_saldo)}</h2><p class="text-blue" style="margin:0; font-size:12px; font-weight:600;">{teks_bawah}</p></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div style="{card_style}"><div class="icon-box bg-green">🎯</div><h4 style="{h4_style}">{lbl_tot_tabungan}</h4><h2 style="{h2_style}">{format_rp(total_tabungan)}</h2><p class="text-green" style="margin:0; font-size:12px; font-weight:600;">{teks_bawah}</p></div>""", unsafe_allow_html=True)
        
    st.write("---") 
    
    col_chart, col_ai = st.columns([2.2, 1])
    
    with col_chart:
        judul_pola = t("Pola Pengeluaran", "Spending Patterns")
        sub_pola = t("Tren Pemasukan vs Pengeluaran dari waktu ke waktu", "Income vs Expense trends over time")
        st.markdown(f"<h4 style='color: var(--text-color); margin-bottom: 0px;'>{judul_pola}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; font-size: 13px;'>{sub_pola}</p>", unsafe_allow_html=True)
        
        fig = go.Figure()
        if not df_filtered.empty:
            nama_pemasukan = t("Pemasukan", "Income")
            nama_pengeluaran = t("Pengeluaran", "Expenses")
            fig.add_trace(go.Scatter(x=df_filtered['Bulan'], y=df_filtered['Pemasukan'], fill='tozeroy', name=nama_pemasukan, line=dict(color='#10B981')))
            fig.add_trace(go.Scatter(x=df_filtered['Bulan'], y=df_filtered['Total Pengeluaran'], fill='tozeroy', name=nama_pengeluaran, line=dict(color='#EF4444')))
        
        fig.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0), 
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#64748B"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', zeroline=False), yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', zeroline=False)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_ai:
        kategori = ['Sewa', 'Kebutuhan Pokok', 'Transportasi', 'Hiburan', 'Tagihan', 'Makan']
        max_kenaikan = 0
        kategori_alert = ""
        for cat in kategori:
            kenaikan = latest_data.get(cat, 0) - prev_data.get(cat, 0)
            if kenaikan > max_kenaikan:
                max_kenaikan = kenaikan
                kategori_alert = cat
                
        if max_kenaikan > 0:
            alert_title = t("📉 Peringatan Boros", "📉 Overspending Alert")
            alert_msg = t(f"Biaya <b>{kategori_alert.lower()}</b> Anda naik {format_rp(max_kenaikan)} dari bulan lalu.", f"Your <b>{kategori_alert.lower()}</b> expenses rose by {format_rp(max_kenaikan)} from last month.")
            alert_style = "background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: var(--text-color);"
        else:
            alert_title = t("🌟 Kerja Bagus!", "🌟 Great Job!")
            alert_msg = t("Pengeluaran Anda stabil dan terjaga di semua kategori dibanding bulan lalu!", "Your expenses are stable across all categories compared to last month!")
            alert_style = "background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: var(--text-color);"
            
        surplus = latest_data.get('Pemasukan', 0) - latest_data.get('Total Pengeluaran', 0)
        if surplus > 0:
            potensi_tabung = surplus * 0.5
            savings_title = t("💡 Peluang Menabung", "💡 Savings Opportunity")
            savings_msg = t(f"Ada sisa dana bulan ini! Alokasikan sekitar <b>{format_rp(potensi_tabung)}</b> ke dana darurat.", f"You have extra funds! Consider allocating <b>{format_rp(potensi_tabung)}</b> to emergency savings.")
            savings_style = "background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: var(--text-color);"
        else:
            savings_title = t("⚠️ Peringatan Anggaran", "⚠️ Budget Warning")
            savings_msg = t("Pengeluaran Anda boncos melebihi pemasukan bulan ini.", "Your expenses exceeded your income this month.")
            savings_style = "background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: var(--text-color);"
            
        rasio_investasi = (latest_data.get('Investasi', 0) / latest_data.get('Pemasukan', 1)) * 100 if latest_data.get('Pemasukan', 0) > 0 else 0
        if rasio_investasi >= 10:
            inv_msg = t(f"Mantap! Anda mengalokasikan <b>{rasio_investasi:.1f}%</b> pendapatan untuk investasi.", f"Awesome! You allocated <b>{rasio_investasi:.1f}%</b> of your income to investments.")
        elif rasio_investasi > 0:
            inv_msg = t(f"Anda baru berinvestasi {format_rp(latest_data.get('Investasi',0))}. Coba naikkan perlahan.", f"You invested {format_rp(latest_data.get('Investasi',0))}. Try to increase it slowly.")
        else:
            inv_msg = t("Belum ada investasi bulan ini. Sisihkan sebagian kecil dana sejak awal gajian.", "No investments this month. Set aside a small amount from your payday.")
        inv_style = "background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: var(--text-color);"

        judul_ai = t("🤖 Asisten Keuangan AI", "🤖 AI Financial Assistant")
        lbl_tips_inv = t("📈 Tips Investasi", "📈 Investment Tips")
        
        st.markdown(f"""<div style="{card_style}">
        <div style="color: var(--text-color); font-weight: 600; font-size: 15px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span style="background-color: rgba(128,128,128,0.1); padding: 4px 6px; border-radius: 6px;">🤖</span> {judul_ai.replace("🤖 ", "")}</div>
        <div style="padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 12px; line-height: 1.5; {alert_style}"><div style="font-weight: 600; margin-bottom: 4px;">{alert_title}</div><div style="font-size: 13px;">{alert_msg}</div></div>
        <div style="padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 12px; line-height: 1.5; {savings_style}"><div style="font-weight: 600; margin-bottom: 4px;">{savings_title}</div><div style="font-size: 13px;">{savings_msg}</div></div>
        <div style="padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 12px; line-height: 1.5; {inv_style}"><div style="font-weight: 600; margin-bottom: 4px;">{lbl_tips_inv}</div><div style="font-size: 13px;">{inv_msg}</div></div>
        </div>""", unsafe_allow_html=True)
        
        btn_tanya_ai = t("Tanya Asisten AI", "Ask AI Assistant")
        if st.button(btn_tanya_ai, use_container_width=True, type="primary"):
            st.session_state.go_to_chatbot = True
            st.rerun()

    st.write("---")

    col_health, col_rule = st.columns([1, 1.2])
    
    with col_health:
        judul_skor = t("Skor Kesehatan Keuangan", "Financial Health Score")
        st.markdown(f"<h4 style='color: var(--text-color); margin-bottom: 0px;'>{judul_skor}</h4>", unsafe_allow_html=True)
        sub_skor = t(f"Berdasarkan rasio tabungan {teks_bawah.replace('+ ', '').lower()}", f"Based on savings ratio {teks_bawah.replace('+ ', '').lower()}")
        st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; font-size: 13px;'>{sub_skor}</p>", unsafe_allow_html=True)
        
        total_investasi = df_filtered['Investasi'].sum() if not df_filtered.empty else 0
        total_aset_disimpan = total_tabungan + total_investasi
        rasio_tabungan = (total_aset_disimpan / total_pemasukan) * 100 if total_pemasukan > 0 else 0
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = rasio_tabungan, number = {'suffix': "%", 'font': {'size': 36, 'color': '#10B981'}},
            gauge = {
                'axis': {'range': [0, 50], 'tickwidth': 1, 'tickcolor': "rgba(128,128,128,0.2)"}, 'bar': {'color': "#10B981", 'thickness': 0.3},
                'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                'steps': [
                    {'range': [0, 10], 'color': 'rgba(239, 68, 68, 0.2)'}, 
                    {'range': [10, 20], 'color': 'rgba(245, 158, 11, 0.2)'},
                    {'range': [20, 50], 'color': 'rgba(16, 185, 129, 0.2)'} 
                ],
                'threshold': {'line': {'color': "var(--text-color)", 'width': 4}, 'thickness': 0.75, 'value': rasio_tabungan }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="gray"))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_rule:
        judul_proporsi = t("Cek Proporsi 50/30/20", "Check 50/30/20 Rule")
        sub_proporsi = t("Berdasarkan aturan finansial ideal", "Based on ideal financial proportions")
        st.markdown(f"<h4 style='color: var(--text-color); margin-bottom: 0px;'>{judul_proporsi}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; font-size: 13px;'>{sub_proporsi}</p>", unsafe_allow_html=True)
        
        needs = df_filtered['Kebutuhan Pokok'].sum() + df_filtered['Sewa'].sum() + df_filtered['Tagihan'].sum() + df_filtered['Transportasi'].sum() if not df_filtered.empty else 0
        wants = df_filtered['Hiburan'].sum() + df_filtered['Makan'].sum() if not df_filtered.empty else 0
        savings = total_aset_disimpan 
        total_alokasi = needs + wants + savings
        
        pct_needs = (needs / total_alokasi) * 100 if total_alokasi > 0 else 0
        pct_wants = (wants / total_alokasi) * 100 if total_alokasi > 0 else 0
        pct_savings = (savings / total_alokasi) * 100 if total_alokasi > 0 else 0
        
        lbl_needs = t("Kebutuhan Pokok (Idealnya 50%)", "Basic Needs (Ideally 50%)")
        lbl_wants = t("Keinginan / Hiburan (Idealnya 30%)", "Wants / Entertainment (Ideally 30%)")
        lbl_savings = t("Tabungan & Investasi (Idealnya 20%)", "Savings & Investments (Ideally 20%)")

        st.markdown(f"""<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; margin-top: 10px; height: 260px; display: flex; flex-direction: column; justify-content: center;">
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-color); margin-bottom: 4px;"><span>{lbl_needs}</span><span>{pct_needs:.1f}%</span></div>
            <div style="background-color: rgba(128, 128, 128, 0.2); border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {'#10B981' if pct_needs <= 50 else '#EF4444'}; height: 100%; border-radius: 4px; width: {min(pct_needs, 100)}%;"></div>
            </div>
        </div>
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-color); margin-bottom: 4px;"><span>{lbl_wants}</span><span>{pct_wants:.1f}%</span></div>
            <div style="background-color: rgba(128, 128, 128, 0.2); border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {'#10B981' if pct_wants <= 30 else '#EF4444'}; height: 100%; border-radius: 4px; width: {min(pct_wants, 100)}%;"></div>
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-color); margin-bottom: 4px;"><span>{lbl_savings}</span><span>{pct_savings:.1f}%</span></div>
            <div style="background-color: rgba(128, 128, 128, 0.2); border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {'#10B981' if pct_savings >= 20 else '#F59E0B'}; height: 100%; border-radius: 4px; width: {min(pct_savings, 100)}%;"></div>
            </div>
        </div>
        </div>""", unsafe_allow_html=True)
 
# ==========================================
# 2. MENU: TRANSAKSI 
# ==========================================
elif selected == "transaction": 
    
    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            judul_transaksi = t("Transaksi", "Transactions")
            st.markdown(f"<h3 style='margin-bottom: 0px; margin-top: 0px; color: var(--text-color);'>{judul_transaksi}</h3>", unsafe_allow_html=True)
            sub_transaksi = t("Lihat dan catat transaksi harian Anda", "View and record your daily transactions")
            st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; font-size: 14px; margin-top: 5px;'>{sub_transaksi}</p>", unsafe_allow_html=True)
        with col_t2:
            btn_tambah = t("➕ Tambah Transaksi", "➕ Add Transaction")
            if st.button(btn_tambah, use_container_width=True):
                st.session_state.show_transaction_form = not st.session_state.get('show_transaction_form', False)
 
        if st.session_state.get('show_transaction_form', False):
            st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
            
            lbl_jenis = t("Jenis Transaksi", "Transaction Type")
            opsi_jenis = ["Pengeluaran", "Pemasukan"] if st.session_state.language == "ID" else ["Expense", "Income"]
            pilihan_jenis = st.radio(lbl_jenis, opsi_jenis, horizontal=True)
            
            # Kita kembalikan ke format baku agar aman masuk Database
            jenis_transaksi = "Pengeluaran" if pilihan_jenis in ["Pengeluaran", "Expense"] else "Pemasukan"
            
            with st.form("form_tambah_transaksi", clear_on_submit=True, border=False):
                col_in1, col_in2 = st.columns(2)
                with col_in1:
                    lbl_tanggal = t("Tanggal", "Date")
                    input_tanggal = st.date_input(lbl_tanggal, datetime.date.today())
                    if jenis_transaksi == "Pengeluaran":
                        lbl_kat = t("Kategori", "Category")
                        input_kategori = st.selectbox(lbl_kat, [
                            "Kebutuhan Pokok", "Sewa", "Transportasi", "Olahraga", 
                            "Tagihan", "Kesehatan", "Investasi", "Cicilan", "Makan", "Hiburan"
                        ])
                    else:
                        input_kategori = "Pemasukan"
                        
                with col_in2:
                    lbl_nominal = t("Nominal (Rp)", "Amount (Rp)")
                    input_nominal = st.number_input(lbl_nominal, min_value=0, step=100000)
                    if jenis_transaksi == "Pengeluaran":
                        lbl_desk = t("Deskripsi (Opsional)", "Description (Optional)")
                        input_deskripsi = st.text_input(lbl_desk)
                    else:
                        input_deskripsi = "-"
                        
                btn_simpan = t("Simpan ke Database", "Save to Database")
                submit_btn = st.form_submit_button(btn_simpan, type="primary", use_container_width=True)
                
                if submit_btn:
                    if input_nominal <= 0:
                        msg_err_nom = t("Nominal harus lebih dari Rp 0!", "Amount must be greater than Rp 0!")
                        st.error(msg_err_nom)
                    else:
                        try:
                            supabase = st.session_state.supabase
                            user_id = st.session_state.user.id
                            tanggal_str = input_tanggal.strftime("%Y-%m-%d")
                            deskripsi_final = input_deskripsi if input_deskripsi.strip() != "" else "-"
                            
                            # Simpan transaksi harian ke Supabase
                            supabase.table("harian").insert({
                                "user_id": user_id,
                                "tanggal": tanggal_str,
                                "kategori": input_kategori,
                                "nominal": int(input_nominal),
                                "deskripsi": deskripsi_final
                            }).execute()
                            
                            # Ambil tanggal awal bulan YYYY-MM-01
                            bulan_awal = input_tanggal.replace(day=1).strftime("%Y-%m-%d")
                            
                            # Cek apakah data bulan ini sudah ada di table bulanan
                            res_bulanan = supabase.table("bulanan").select("*").eq("user_id", user_id).eq("Bulan", bulan_awal).execute()
                            
                            if not res_bulanan.data:
                                # Jika belum ada, buat baris bulanan baru
                                new_row = {
                                    "user_id": user_id,
                                    "Bulan": bulan_awal,
                                    "Pemasukan": 0,
                                    "Total Pengeluaran": 0,
                                    "Tabungan": 0,
                                    "Kebutuhan Pokok": 0,
                                    "Sewa": 0,
                                    "Transportasi": 0,
                                    "Olahraga": 0,
                                    "Tagihan": 0,
                                    "Kesehatan": 0,
                                    "Investasi": 0,
                                    "Cicilan": 0,
                                    "Makan": 0,
                                    "Hiburan": 0
                                }
                                supabase.table("bulanan").insert(new_row).execute()
                                current_row = new_row
                            else:
                                current_row = res_bulanan.data[0]
                                
                            # Siapkan update
                            update_vals = {}
                            if jenis_transaksi == "Pengeluaran":
                                cat_val = current_row.get(input_kategori, 0) or 0
                                tot_exp = current_row.get("Total Pengeluaran", 0) or 0
                                saving = current_row.get("Tabungan", 0) or 0
                                
                                update_vals[input_kategori] = int(cat_val + input_nominal)
                                update_vals["Total Pengeluaran"] = int(tot_exp + input_nominal)
                                update_vals["Tabungan"] = int(saving - input_nominal)
                            else:
                                pemasukan_val = current_row.get("Pemasukan", 0) or 0
                                saving = current_row.get("Tabungan", 0) or 0
                                
                                update_vals["Pemasukan"] = int(pemasukan_val + input_nominal)
                                update_vals["Tabungan"] = int(saving + input_nominal)
                                
                            supabase.table("bulanan").update(update_vals).eq("user_id", user_id).eq("Bulan", bulan_awal).execute()
                            
                            nama_jenis = t("pengeluaran", "expense") if jenis_transaksi == "Pengeluaran" else t("pemasukan", "income")
                            msg_sukses = t(f"Berhasil menyimpan {nama_jenis} sebesar {format_rp(input_nominal)}!", f"Successfully saved {nama_jenis} of {format_rp(input_nominal)}!")
                            st.success(msg_sukses)
                            
                            st.session_state.show_transaction_form = False 
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan transaksi ke Supabase: {e}")
 
    st.write("")
    judul_riwayat = t("### Riwayat Transaksi Harian", "### Daily Transaction History")
    st.markdown(judul_riwayat)
    
    try:
        supabase = st.session_state.supabase
        user_id = st.session_state.user.id
        
        # Ambil data raw
        res_harian = supabase.table("harian").select("*").eq("user_id", user_id).execute()
        df_harian_raw = pd.DataFrame(res_harian.data)
        
        if df_harian_raw.empty:
            msg_kosong = t("Belum ada data transaksi harian. Silakan input di atas.", "No daily transaction data yet. Please input above.")
            st.info(msg_kosong)
        else:
            # Urutkan dari yang terbaru
            df_harian_raw = df_harian_raw.sort_values('id', ascending=False).reset_index(drop=True)
            
            # Buat copy untuk ditampilkan di tabel agar formatnya rapi
            df_harian_display = df_harian_raw.copy()
            df_harian_display = df_harian_display.rename(columns={
                "tanggal": "Tanggal", "kategori": "Kategori", 
                "nominal": "Nominal", "deskripsi": "Deskripsi"
            })
            df_harian_display['Deskripsi'] = df_harian_display['Deskripsi'].replace('', '-').fillna('-')
            
            # --- MODIFIKASI: Menambahkan Simbol Panah ---
            def format_nom_with_arrow(row):
                nom_str = format_rp(row['Nominal'])
                if row['Kategori'] == "Pemasukan" or row['Kategori'] == "Income":
                    return f"▲ {nom_str}"
                else:
                    return f"▼ {nom_str}"
                    
            df_harian_display['Nominal'] = df_harian_display.apply(format_nom_with_arrow, axis=1)
            # --------------------------------------------
            
            df_harian_final = df_harian_display[['Tanggal', 'Kategori', 'Nominal', 'Deskripsi']]
            
            col_tgl = t("Tanggal", "Date")
            col_kat = t("Kategori", "Category")
            col_nom = t("Nominal", "Amount")
            col_desk = t("Deskripsi", "Description")
            df_harian_final.columns = [col_tgl, col_kat, col_nom, col_desk]
            
            # --- MODIFIKASI: Memberikan Warna Hijau/Merah pada Kolom Nominal ---
            def color_nominal(val):
                if isinstance(val, str):
                    if '▲' in val:
                        return 'color: #10B981; font-weight: 600;' # Hijau Emerald
                    elif '▼' in val:
                        return 'color: #EF4444; font-weight: 600;' # Merah
                return ''
            
            # Gunakan Pandas Styler untuk mewarnai teks secara dinamis
            try:
                # Untuk Pandas versi terbaru
                styled_df = df_harian_final.style.map(color_nominal, subset=[col_nom])
            except AttributeError:
                # Fallback jika menggunakan Pandas versi lama
                styled_df = df_harian_final.style.applymap(color_nominal, subset=[col_nom])
                
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            # -------------------------------------------------------------------------
            
            # --- FITUR HAPUS TRANSAKSI ---
            st.write("---")
            lbl_expander_del = t(" Hapus Transaksi (Revisi/Batal)", " Delete Transaction (Undo/Revise)")
            with st.expander(lbl_expander_del):
                # Buat dictionary untuk opsi dropdown
                opsi_hapus = {}
                for _, row in df_harian_raw.iterrows():
                    label = f"{row['tanggal']} | {row['kategori']} | {format_rp(row['nominal'])} | {row['deskripsi']}"
                    opsi_hapus[label] = row
                    
                lbl_pilih_hapus = t("Pilih transaksi yang salah / ingin dihapus:", "Select transaction to delete:")
                pilihan_hapus = st.selectbox(lbl_pilih_hapus, list(opsi_hapus.keys()))
                
                if st.button(t("Hapus Transaksi", "Delete Transaction"), type="primary", key="btn_del_tx"):
                    try:
                        row_del = opsi_hapus[pilihan_hapus]
                        
                        # 1. Hapus dari tabel harian
                        supabase.table("harian").delete().eq("id", row_del['id']).execute()
                        
                        # 2. Reverse (kembalikan) perhitungan di tabel bulanan
                        tgl_tx = datetime.datetime.strptime(row_del['tanggal'], "%Y-%m-%d")
                        bulan_awal = tgl_tx.replace(day=1).strftime("%Y-%m-%d")
                        kat_tx = row_del['kategori']
                        nom_tx = int(row_del['nominal'])
                        
                        res_bulanan = supabase.table("bulanan").select("*").eq("user_id", user_id).eq("Bulan", bulan_awal).execute()
                        if res_bulanan.data:
                            current_row = res_bulanan.data[0]
                            update_vals = {}
                            if kat_tx != "Pemasukan": # Jika yang dihapus adalah Pengeluaran
                                update_vals[kat_tx] = max(0, int(current_row.get(kat_tx, 0) - nom_tx))
                                update_vals["Total Pengeluaran"] = max(0, int(current_row.get("Total Pengeluaran", 0) - nom_tx))
                                update_vals["Tabungan"] = int(current_row.get("Tabungan", 0) + nom_tx)
                            else: # Jika yang dihapus adalah Pemasukan
                                update_vals["Pemasukan"] = max(0, int(current_row.get("Pemasukan", 0) - nom_tx))
                                update_vals["Tabungan"] = int(current_row.get("Tabungan", 0) - nom_tx)
                                
                            supabase.table("bulanan").update(update_vals).eq("user_id", user_id).eq("Bulan", bulan_awal).execute()
                        
                        st.success(t("Transaksi berhasil dihapus dan saldo bulanan telah dikembalikan!", "Transaction successfully deleted and monthly balance restored!"))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus transaksi: {e}")

    except Exception as e:
        msg_db_kosong = t(f"Gagal mengambil data transaksi harian dari Supabase: {e}", f"Failed to retrieve daily transactions from Supabase: {e}")
        st.info(msg_db_kosong)
 
# ==========================================
# 3. MENU: BUDGET & SAVING
elif selected == "budget":
    judul_menu_budget = t("Anggaran & Tabungan", "Budget & Savings")
    st.title(judul_menu_budget)
    
    st.markdown("""
    <style>
    .b-summary-card { background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); padding: 20px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.03); margin-bottom: 20px; }
    .b-summary-title { color: var(--text-color); opacity: 0.7; font-size: 13px; font-weight: 500; margin-bottom: 5px; }
    .b-summary-val { color: var(--text-color); font-size: 24px; font-weight: bold; }
    .b-table { width: 100%; border-collapse: collapse; background: var(--secondary-background-color); border-radius: 12px; overflow: hidden; border: 1px solid rgba(128, 128, 128, 0.2); margin-top: 10px; font-family: 'Segoe UI', sans-serif; }
    .b-table th { background-color: rgba(128, 128, 128, 0.05); color: var(--text-color); opacity: 0.7; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 16px; text-align: left; border-bottom: 1px solid rgba(128, 128, 128, 0.2); }
    .b-table td { padding: 16px; border-bottom: 1px solid rgba(128, 128, 128, 0.1); font-size: 13px; color: var(--text-color); vertical-align: middle; }
    .prog-bg-small { width: 100%; height: 6px; background-color: rgba(128, 128, 128, 0.2); border-radius: 10px; overflow: hidden; margin-bottom: 4px; }
    .prog-fill-green { height: 100%; background-color: #10B981; }
    .prog-fill-orange { height: 100%; background-color: #F59E0B; }
    .prog-fill-red { height: 100%; background-color: #EF4444; }
    div[data-testid="stButton"] > button { border: 1px solid rgba(128, 128, 128, 0.2); color: var(--text-color); font-weight: 500; border-radius: 8px; background-color: transparent; }
    div[data-testid="stButton"] > button:hover { border-color: var(--text-color); background-color: rgba(128, 128, 128, 0.05);}
    </style>
    """, unsafe_allow_html=True)
    
    try:
        supabase = st.session_state.supabase
        user_id = st.session_state.user.id
        
        res_budget = supabase.table("budget").select("*").eq("user_id", user_id).execute()
        df_budget = pd.DataFrame(res_budget.data)
        if not df_budget.empty:
            df_budget = df_budget.drop(columns=["user_id"], errors="ignore")
        else:
            df_budget = pd.DataFrame(columns=["kategori", "nominal"])
            
        res_goals = supabase.table("target").select("*").eq("user_id", user_id).execute()
        df_goals = pd.DataFrame(res_goals.data)
        if not df_goals.empty:
            df_goals = df_goals.drop(columns=["user_id"], errors="ignore")
        else:
            df_goals = pd.DataFrame(columns=["tujuan", "target", "terkumpul"])
    except Exception as e:
        df_budget = pd.DataFrame(columns=["kategori", "nominal"])
        df_goals = pd.DataFrame(columns=["tujuan", "target", "terkumpul"])

    tab1, tab2 = st.tabs([" Budgets", " Savings Goals"])
    
    with tab1:
        budget_dict = dict(zip(df_budget['kategori'], df_budget['nominal'])) if not df_budget.empty else {}
 
        if not df.empty:
            df_sorted = df.sort_values('Bulan')
            latest_data_budget = df_sorted.iloc[-1]
            nama_bulan = latest_data_budget['Bulan'].strftime("%B %Y")
        else:
            latest_data_budget = pd.Series(dtype='float64')
            nama_bulan = t("Belum Ada Data", "No Data")
 
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            judul_analisis = t("Anggaran & Tabungan", "Budget & Savings")
            st.markdown(f"<h2 style='margin-bottom: 0px; color: var(--text-color);'>{judul_analisis}</h2>", unsafe_allow_html=True)  
            sub_analisis = t("Wawasan mendalam berdasarkan aktivitas riil di Database Anda", "Deep insights based on real activities in your Database")
            st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; margin-top:0px;'>{sub_analisis}</p>", unsafe_allow_html=True)
        with col_h2:
            st.write("") 
            btn_buat_anggaran = t("➕ Buat Anggaran Baru", "➕ Create New Budget")
            if st.button(btn_buat_anggaran, use_container_width=True):
                st.session_state.show_budget_form = not st.session_state.get('show_budget_form', False)
 
        if st.session_state.get('show_budget_form', False):
            with st.container(border=True):
                # Menyesuaikan judul dengan bulan dari data terakhir
                st.markdown(f"#### Anggaran untuk {nama_bulan}")
                
                with st.form("form_set_budget_massal"):
                    # Membagi menjadi 2 kolom sesuai gambar
                    col_kiri, col_kanan = st.columns(2)
                    
                    with col_kiri:
                        b_pokok = st.number_input("🛒 Kebutuhan Pokok", min_value=0, step=50000, value=int(budget_dict.get("Kebutuhan Pokok", 0)))
                        b_trans = st.number_input("🚗 Transportasi", min_value=0, step=50000, value=int(budget_dict.get("Transportasi", 0)))
                        b_tagihan = st.number_input("📱 Tagihan", min_value=0, step=50000, value=int(budget_dict.get("Tagihan", 0)))
                        b_cicilan = st.number_input("💳 Cicilan", min_value=0, step=50000, value=int(budget_dict.get("Cicilan", 0)))
                        b_hiburan = st.number_input("🎮 Hiburan", min_value=0, step=50000, value=int(budget_dict.get("Hiburan", 0)))
                    with col_kanan:
                        b_sewa = st.number_input("🏠 Sewa", min_value=0, step=50000, value=int(budget_dict.get("Sewa", 0)))
                        b_olahraga = st.number_input("🏃 Olahraga", min_value=0, step=50000, value=int(budget_dict.get("Olahraga", 0)))
                        b_kesehatan = st.number_input("🏥 Kesehatan", min_value=0, step=50000, value=int(budget_dict.get("Kesehatan", 0)))
                        b_makan = st.number_input("🍽️ Makan", min_value=0, step=50000, value=int(budget_dict.get("Makan", 0)))
                        b_investasi = st.number_input("📈 Investasi", min_value=0, step=50000, value=int(budget_dict.get("Investasi", 0)))
                        
                    # Tombol submit yang mengambil lebar penuh wadah (use_container_width=True)
                    btn_simpan_teks = t(" Simpan Anggaran", " Save Budget")
                    submit_budget = st.form_submit_button(btn_simpan_teks, type="primary", use_container_width=True)
                    
                    if submit_budget:
                        try:
                            supabase = st.session_state.supabase
                            user_id = st.session_state.user.id
                            
                            # Menggabungkan data menjadi satu list untuk proses upsert massal (batch)
                            data_upsert = [
                                {"user_id": user_id, "kategori": "Kebutuhan Pokok", "nominal": b_pokok},
                                {"user_id": user_id, "kategori": "Transportasi", "nominal": b_trans},
                                {"user_id": user_id, "kategori": "Tagihan", "nominal": b_tagihan},
                                {"user_id": user_id, "kategori": "Cicilan", "nominal": b_cicilan},
                                {"user_id": user_id, "kategori": "Hiburan", "nominal": b_hiburan},
                                {"user_id": user_id, "kategori": "Sewa", "nominal": b_sewa},
                                {"user_id": user_id, "kategori": "Olahraga", "nominal": b_olahraga},
                                {"user_id": user_id, "kategori": "Kesehatan", "nominal": b_kesehatan},
                                {"user_id": user_id, "kategori": "Makan", "nominal": b_makan},
                                {"user_id": user_id, "kategori": "Investasi", "nominal": b_investasi}
                            ]
                            
                            # Melakukan upsert data sekaligus ke tabel budget
                            supabase.table("budget").upsert(data_upsert).execute()
                            
                            st.success(t("Semua anggaran berhasil diperbarui!", "All budgets successfully updated!"))
                            st.session_state.show_budget_form = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan anggaran ke Supabase: {e}")
     
        total_pemasukan_bulan_ini = latest_data_budget.get('Pemasukan', 0) 
        total_allocated = sum(budget_dict.values())
        total_spent = sum([latest_data_budget.get(kat, 0) for kat in budget_dict.keys()])
        total_remaining = total_allocated - total_spent
        
        rem_color = "#10B981" if total_remaining >= 0 else "#EF4444"
        
        st.write("")
        lbl_tot_pemasukan = t("Total Pemasukan", "Total Income")
        lbl_tot_alokasi = t("Total Alokasi", "Total Allocated")
        lbl_tot_terpakai = t("Total Terpakai", "Total Spent")
        lbl_sisa_anggaran = t("Sisa Anggaran", "Remaining Budget")

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_tot_pemasukan}</div><div class="b-summary-val" style="color: #10B981;">{format_rp(total_pemasukan_bulan_ini)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_tot_alokasi}</div><div class="b-summary-val" style="color: var(--text-color);">{format_rp(total_allocated)}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_tot_terpakai}</div><div class="b-summary-val" style="color: #EA580C;">{format_rp(total_spent)}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_sisa_anggaran}</div><div class="b-summary-val" style="color: {rem_color};">{format_rp(total_remaining)}</div></div>', unsafe_allow_html=True)
 
        th_kat = t("KATEGORI", "CATEGORY")
        th_alokasi = t("ALOKASI", "ALLOCATED")
        th_terpakai = t("TERPAKAI", "SPENT")
        th_sisa = t("SISA", "REMAINING")
        th_progres = t("PROGRES", "PROGRESS")
        th_periode = t("PERIODE", "PERIOD")

        tabel_html = f"""
        <table class="b-table" style="box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: none;">
            <thead>
                <tr style="background-color: rgba(128, 128, 128, 0.05);">
                    <th style="border-top-left-radius: 8px;">{th_kat}</th>
                    <th>{th_alokasi}</th><th>{th_terpakai}</th><th>{th_sisa}</th><th style="width: 18%;">{th_progres}</th><th>{th_periode}</th>
                </tr>
            </thead><tbody>
        """
        
        if not budget_dict:
            msg_no_budget = t("Belum ada anggaran yang diatur. Klik 'Buat Anggaran Baru' di atas.", "No budgets set. Click 'Create New Budget' above.")
            tabel_html += f"<tr><td colspan='6' style='text-align: center; padding: 30px; color: var(--text-color); opacity: 0.7;'>{msg_no_budget}</td></tr>"
        else:
            lbl_bulanan = t("Bulanan", "Monthly")
            for kat, allocated in budget_dict.items():
                spent = latest_data_budget.get(kat, 0)
                rem = allocated - spent
                pct = (spent / allocated) * 100 if allocated > 0 else 0
                
                if pct <= 80: prog_color, spent_color = "prog-fill-green", "#10B981"
                elif pct <= 100: prog_color, spent_color = "prog-fill-orange", "#F59E0B"
                else: prog_color, spent_color = "prog-fill-red", "#EF4444"
                
                rem_color_row = "#10B981" if rem >= 0 else "#EF4444"
                
                tabel_html += f"""<tr>
                    <td style="font-weight: 500; color: var(--text-color);">{kat}</td>
                    <td style="font-weight: 600; color: var(--text-color);">{format_rp(allocated)}</td>
                    <td style="color: {spent_color}; font-weight: 600;">{format_rp(spent)}</td>
                    <td style="color: {rem_color_row}; font-weight: 600;">{format_rp(rem)}</td>
                    <td><div class="prog-bg-small" style="height: 4px; background-color: rgba(128, 128, 128, 0.2); margin-bottom: 6px;"><div class="{prog_color}" style="width: {min(pct, 100)}%; height: 100%; border-radius: 10px;"></div></div><span style="font-size: 11px; color: var(--text-color); opacity: 0.7; font-weight: 500;">{int(pct)}%</span></td>
                    <td style="color: var(--text-color); opacity: 0.7; font-size: 12px;">{lbl_bulanan}</td>
                </tr>"""
                
        tabel_html += "</tbody></table>"
        st.markdown(tabel_html, unsafe_allow_html=True)
 
    with tab2:
        # 1. Ambil data pemasukan dari bulan terbaru (sama seperti logika di tab1)
        if not df.empty:
            df_sorted = df.sort_values('Bulan')
            latest_data_budget = df_sorted.iloc[-1]
            total_pemasukan_bulan_ini = latest_data_budget.get('Pemasukan', 0)
        else:
            total_pemasukan_bulan_ini = 0
            
        # 2. Hitung total seluruh alokasi limit yang ada di tabel budget
        total_alokasi_budget = df_budget['nominal'].sum() if not df_budget.empty else 0
        
        # 3. RUMUS BARU: Total Tabungan = Total Pemasukan Bulanan - Total Alokasi Budget Kategori
        total_tabungan_all = total_pemasukan_bulan_ini - total_alokasi_budget
        
        # 4. Hitung total dana yang sudah berhasil dikumpulkan untuk target-target tabungan
        total_dialokasikan = df_goals['terkumpul'].sum() if not df_goals.empty else 0
        
        # 5. Sisa dana tabungan yang masih bebas dialokasikan ke target berikutnya
        sisa_tabungan = total_tabungan_all - total_dialokasikan
        
        col_sh1, col_sh2 = st.columns([3, 1])
        with col_sh1:
            judul_target = t("Target Tabungan", "Savings Goals")
            sub_target = t("Kelola tujuan tabungan dan alokasikan sisa dana Anda", "Manage savings goals and allocate your remaining funds")
            st.markdown(f"<h3 style='margin-bottom: 0px; color: var(--text-color);'>{judul_target}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; margin-top:0px; font-size: 14px;'>{sub_target}</p>", unsafe_allow_html=True)
        with col_sh2:
            st.write("")
            btn_buat_target = t("➕ Buat Target Baru", "➕ Create New Goal")
            if st.button(btn_buat_target, use_container_width=True):
                st.session_state.show_saving_form = not st.session_state.get('show_saving_form', False)
 
        if st.session_state.get('show_saving_form', False):
            with st.container(border=True):
                st.markdown(f"#### {btn_buat_target.replace('➕ ', '')}")
                with st.form("form_tambah_goal"):
                    cg1, cg2 = st.columns(2)
                    with cg1:
                        lbl_desk_target = t("Deskripsi (Misal: DP Rumah, Darurat)", "Description (e.g., Down Payment, Emergency)")
                        input_deskripsi = st.text_input(lbl_desk_target)
                    with cg2:
                        lbl_nom_target_tab = t("Nominal Target (Rp)", "Target Amount (Rp)")
                        input_target_goal = st.number_input(lbl_nom_target_tab, min_value=0, step=1000000)
                        
                    btn_simpan_target = t("Simpan Target", "Save Goal")
                    if st.form_submit_button(btn_simpan_target, type="primary"):
                        if input_deskripsi == "":
                            err_desk = t("Deskripsi wajib diisi!", "Description is required!")
                            st.error(err_desk)
                        else:
                            try:
                                supabase = st.session_state.supabase
                                user_id = st.session_state.user.id
                                supabase.table("target").upsert({
                                    "user_id": user_id,
                                    "tujuan": input_deskripsi,
                                    "target": int(input_target_goal),
                                    "terkumpul": 0
                                }).execute()
                                msg_sukses_target = t(f"Target '{input_deskripsi}' berhasil dibuat!", f"Goal '{input_deskripsi}' successfully created!")
                                st.success(msg_sukses_target)
                                st.session_state.show_saving_form = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal menyimpan target tabungan ke Supabase: {e}")
 
        rem_color = "#10B981" if sisa_tabungan >= 0 else "#EF4444"
        st.write("")
        
        lbl_tot_tab = t("Total Tabungan", "Total Savings")
        lbl_tot_alokasi = t("Total Alokasi", "Total Allocated")
        lbl_sisa_tab = t("Sisa Tabungan", "Remaining Savings")
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_tot_tab}</div><div class="b-summary-val" style="color: var(--text-color);">{format_rp(total_tabungan_all)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_tot_alokasi}</div><div class="b-summary-val" style="color: #3B82F6;">{format_rp(total_dialokasikan)}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="b-summary-card"><div class="b-summary-title">{lbl_sisa_tab}</div><div class="b-summary-val" style="color: {rem_color};">{format_rp(sisa_tabungan)}</div></div>', unsafe_allow_html=True)
 
        th_desk = t("DESKRIPSI", "DESCRIPTION")
        th_targ = t("TARGET", "TARGET")
        th_alok = t("ALOKASI DANA", "ALLOCATED FUNDS")
        th_prog = t("PROGRES", "PROGRESS")

        tabel_html = f"""
        <table class="b-table" style="box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: none;">
            <thead><tr style="background-color: rgba(128, 128, 128, 0.05);"><th style="border-top-left-radius: 8px;">{th_desk}</th><th>{th_targ}</th><th>{th_alok}</th><th style="width: 25%; border-top-right-radius: 8px;">{th_prog}</th></tr></thead>
            <tbody>
        """
        if df_goals.empty:
            msg_no_goals = t("Belum ada target yang diatur. Klik 'Buat Target Baru' di atas.", "No goals set. Click 'Create New Goal' above.")
            tabel_html += f"<tr><td colspan='4' style='text-align: center; padding: 30px; color: var(--text-color); opacity: 0.7;'>{msg_no_goals}</td></tr>"
        else:
            for row in df_goals.itertuples():
                pct = (row.terkumpul / row.target) * 100 if row.target > 0 else 0
                prog_color = "#3B82F6" if pct < 100 else "#10B981"
                tabel_html += f"""<tr>
                    <td style="font-weight: 500; color: var(--text-color);">{row.tujuan}</td><td style="font-weight: 600; color: var(--text-color);">{format_rp(row.target)}</td><td style="color: #3B82F6; font-weight: 600;">{format_rp(row.terkumpul)}</td>
                    <td><div class="prog-bg-small" style="height: 6px; background-color: rgba(128, 128, 128, 0.2); margin-bottom: 6px; border-radius: 10px;"><div style="background-color: {prog_color}; width: {min(pct, 100)}%; height: 100%; border-radius: 10px;"></div></div><span style="font-size: 11px; color: var(--text-color); opacity: 0.7; font-weight: 500;">{int(pct)}%</span></td>
                </tr>"""
        tabel_html += "</tbody></table>"
        st.markdown(tabel_html, unsafe_allow_html=True)
        st.write("")
 
        if not df_goals.empty and sisa_tabungan > 0:
            lbl_expander = t("💸 Alokasikan Sisa Tabungan Anda", "💸 Allocate Your Remaining Savings")
            with st.expander(lbl_expander, expanded=False):
                with st.form("form_alokasi_dana"):
                    lbl_sisa_info = t(f"Sisa Tabungan yang tersedia: **{format_rp(sisa_tabungan)}**", f"Available remaining savings: **{format_rp(sisa_tabungan)}**")
                    st.info(lbl_sisa_info)
                    ca1, ca2 = st.columns(2)
                    with ca1: 
                        lbl_pilih_target = t("Pilih Target", "Select Goal")
                        pilihan_goal_alokasi = st.selectbox(lbl_pilih_target, df_goals['tujuan'].tolist())
                    with ca2: 
                        lbl_nom_alokasi = t("Nominal Alokasi (Rp)", "Allocation Amount (Rp)")
                        nominal_alokasi = st.number_input(lbl_nom_alokasi, min_value=0, max_value=int(max(0, sisa_tabungan)), step=50000)
                    
                    btn_tambah_alokasi = t("Tambahkan Alokasi", "Add Allocation")
                    if st.form_submit_button(btn_tambah_alokasi, type="primary", use_container_width=True) and nominal_alokasi > 0:
                        try:
                            supabase = st.session_state.supabase
                            user_id = st.session_state.user.id
                            
                            # Dapatkan data terkumpul saat ini
                            res_goal = supabase.table("target").select("terkumpul").eq("user_id", user_id).eq("tujuan", pilihan_goal_alokasi).execute()
                            current_terkumpul = 0
                            if res_goal.data:
                                current_terkumpul = res_goal.data[0].get("terkumpul", 0) or 0
                                
                            new_terkumpul = current_terkumpul + int(nominal_alokasi)
                            supabase.table("target").update({"terkumpul": new_terkumpul}).eq("user_id", user_id).eq("tujuan", pilihan_goal_alokasi).execute()
                            
                            msg_sukses_alokasi = t(f"Berhasil mengalokasikan {format_rp(nominal_alokasi)} ke {pilihan_goal_alokasi}!", f"Successfully allocated {format_rp(nominal_alokasi)} to {pilihan_goal_alokasi}!")
                            st.success(msg_sukses_alokasi)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal mengalokasikan dana di Supabase: {e}")
        # --- FITUR HAPUS TARGET TABUNGAN ---
        if not df_goals.empty:
            lbl_expander_hapus_goal = t("🗑️ Hapus Target Tabungan", "🗑️ Delete Savings Goal")
            with st.expander(lbl_expander_hapus_goal, expanded=False):
                lbl_pilih_del_goal = t("Pilih target yang ingin dihapus:", "Select goal to delete:")
                goal_to_delete = st.selectbox(lbl_pilih_del_goal, df_goals['tujuan'].tolist(), key="del_goal_select")
                
                if st.button(t("Hapus Target", "Delete Goal"), type="primary", key="btn_del_goal"):
                    try:
                        supabase = st.session_state.supabase
                        user_id = st.session_state.user.id
                        # Menghapus target dari tabel target
                        supabase.table("target").delete().eq("user_id", user_id).eq("tujuan", goal_to_delete).execute()
                        
                        msg_del_goal = t(
                            f"Target '{goal_to_delete}' berhasil dihapus! Saldo yang dialokasikan otomatis dikembalikan.", 
                            f"Goal '{goal_to_delete}' successfully deleted! Allocated balance is automatically restored."
                        )
                        st.success(msg_del_goal)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus target: {e}")
 
# ==========================================
# 4. MENU: ANALISIS & REPORTS
# ==========================================
elif selected == "analysis":
        df_bulanan = df.copy()
        
        try:
            supabase = st.session_state.supabase
            user_id = st.session_state.user.id
            res_budget = supabase.table("budget").select("*").eq("user_id", user_id).execute()
            df_budget = pd.DataFrame(res_budget.data)
            if not df_budget.empty:
                df_budget = df_budget.drop(columns=["user_id"], errors="ignore")
            else:
                df_budget = pd.DataFrame(columns=["kategori", "nominal"])
        except:
            df_budget = pd.DataFrame(columns=["kategori", "nominal"])
 
        try:
            supabase = st.session_state.supabase
            user_id = st.session_state.user.id
            res_target = supabase.table("target").select("*").eq("user_id", user_id).execute()
            df_target = pd.DataFrame(res_target.data)
            if not df_target.empty:
                df_target = df_target.drop(columns=["user_id"], errors="ignore")
            else:
                df_target = pd.DataFrame(columns=["tujuan", "target", "terkumpul"])
        except:
            df_target = pd.DataFrame(columns=["tujuan", "target", "terkumpul"])
 
        kategori_pengeluaran = ['Kebutuhan Pokok', 'Sewa', 'Transportasi', 'Olahraga', 'Tagihan', 'Kesehatan', 'Cicilan', 'Makan', 'Hiburan', 'Investasi']
        kategori_valid = [kat for kat in kategori_pengeluaran if kat in df_bulanan.columns]
 
        if df_bulanan.empty:
            judul_kosong = t("Analisis & Laporan", "Analytics & Reports")
            st.markdown(f"<h2 style='color: var(--text-color);'>{judul_kosong}</h2>", unsafe_allow_html=True)
            msg_kosong = t("Belum ada data bulanan untuk dianalisis. Silakan isi data transaksi terlebih dahulu.", "No monthly data to analyze yet. Please input transaction data first.")
            st.warning(msg_kosong)
        else:
            daftar_tahun = sorted(df_bulanan['Bulan'].dt.year.unique().tolist(), reverse=True)
            pilihan_tahun = [str(thn) for thn in daftar_tahun]
            
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                judul_analisis = t("Analisis & Laporan", "Analytics & Reports")
                st.markdown(f"<h2 style='margin-bottom: 0px; color: var(--text-color);'>{judul_analisis}</h2>", unsafe_allow_html=True)
                
                sub_analisis = t("Wawasan mendalam berdasarkan aktivitas riil di Database Anda", "Deep insights based on real activities in your Database")
                st.markdown(f"<p style='color: var(--text-color); opacity: 0.7; margin-top:0px;'>{sub_analisis}</p>", unsafe_allow_html=True)
                
            with col_h2:
                st.write("") 
                lbl_pilih_thn = t("Pilih Tahun", "Select Year")
                tahun_terpilih = st.selectbox(lbl_pilih_thn, pilihan_tahun, label_visibility="collapsed")
                
                # --- TAMBAHAN TOMBOL DOWNLOAD PDF ---
                btn_pdf_label = t("📥 Unduh PDF", "📥 Download PDF")
                if st.button(btn_pdf_label, use_container_width=True):
                    # Memanggil fitur Print / Save as PDF bawaan browser
                    import streamlit.components.v1 as components
                    components.html(
                        """
                        <script>
                            window.parent.print();
                        </script>
                        """,
                        height=0
                    )
                # ------------------------------------
            
            st.write("---")
 
            df_filtered = df_bulanan[df_bulanan['Bulan'].dt.year == int(tahun_terpilih)].copy()
            teks_periode = f"{t('Tahun', 'Year')} {tahun_terpilih}"
            
            if df_filtered.empty:
                st.warning(f"Tidak ada catatan transaksi pada {teks_periode}.")
            else:
                latest_month_data = df_filtered.sort_values('Bulan').iloc[-1]
                nama_bulan_ini = latest_month_data['Bulan'].strftime("%B %Y")
                
                total_pemasukan_all = df_filtered['Pemasukan'].sum()
                total_pengeluaran_all = df_filtered['Total Pengeluaran'].sum()
                avg_savings_rate = ((total_pemasukan_all - total_pengeluaran_all) / total_pemasukan_all * 100) if total_pemasukan_all > 0 else 0
                
                judul_summary = t("Ringkasan Eksekutif", "Executive Summary")
                lbl_pemasukan = t("Total Pemasukan", "Total Income")
                lbl_pengeluaran = t("Total Pengeluaran", "Total Expenses")
                lbl_tabungan = t("Total Tabungan", "Total Savings")
                lbl_rata_rata = t("Rata-rata Savings Rate", "Average Savings Rate")

                st.markdown(f"#### {judul_summary} ({teks_periode})")
                c1, c2, c3, c4 = st.columns(4)
                style_kartu = "background: var(--secondary-background-color); padding:20px; border-radius:10px; border:1px solid rgba(128, 128, 128, 0.2);"
                style_teks = "color: var(--text-color); font-size:13px; margin:0;"
                
                with c1: st.markdown(f'<div style="{style_kartu}"><p style="{style_teks}">{lbl_pemasukan}</p><h3 style="color:#10B981; margin:5px 0 0 0;">{format_rp(total_pemasukan_all)}</h3></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div style="{style_kartu}"><p style="{style_teks}">{lbl_pengeluaran}</p><h3 style="color:#EF4444; margin:5px 0 0 0;">{format_rp(total_pengeluaran_all)}</h3></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div style="{style_kartu}"><p style="{style_teks}">{lbl_tabungan}</p><h3 style="color:#3B82F6; margin:5px 0 0 0;">{format_rp(total_pemasukan_all - total_pengeluaran_all)}</h3></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div style="{style_kartu}"><p style="{style_teks}">{lbl_rata_rata}</p><h3 style="color:#F59E0B; margin:5px 0 0 0;">{avg_savings_rate:.1f}%</h3></div>', unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
 
                judul_grafik_1 = t("1. Tren Arus Kas Bulanan", "1. Monthly Cash Flow Trend")
                st.markdown(f"#### {judul_grafik_1} ({teks_periode})")

                nama_pemasukan = t("Pemasukan", "Income")
                nama_pengeluaran = t("Pengeluaran", "Expenses")

                fig_trend = go.Figure()
                fig_trend.add_trace(go.Bar(x=df_filtered['Bulan'].dt.strftime('%b %Y'), y=df_filtered['Pemasukan'], name='Pemasukan', marker_color='#10B981'))
                fig_trend.add_trace(go.Bar(x=df_filtered['Bulan'].dt.strftime('%b %Y'), y=df_filtered['Total Pengeluaran'], name='Pengeluaran', marker_color='#EF4444'))
                fig_trend.update_layout(barmode='group', margin=dict(t=20, b=20, l=0, r=0), legend=dict(orientation="h", y=1.1), plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trend, use_container_width=True)
                
                bulan_terboros = df_filtered.loc[df_filtered['Total Pengeluaran'].idxmax()]
                bulan_paling_cuan = df_filtered.loc[df_filtered['Tabungan'].idxmax()]
                msg_tren_ai = t(
                    f"**Interpretasi AI:** Pada periode ini, Anda mencetak rekor tabungan tertinggi pada **{bulan_paling_cuan['Bulan'].strftime('%B %Y')}** dengan sisa uang {format_rp(bulan_paling_cuan['Tabungan'])}. Namun, waspadai pengeluaran Anda karena bulan **{bulan_terboros['Bulan'].strftime('%B %Y')}** tercatat sebagai bulan paling boros.",
                    f"**AI Interpretation:** In this period, you hit your highest savings record in **{bulan_paling_cuan['Bulan'].strftime('%B %Y')}** with {format_rp(bulan_paling_cuan['Tabungan'])} remaining. However, watch your spending because **{bulan_terboros['Bulan'].strftime('%B %Y')}** was your most wasteful month."
                )
                st.info(msg_tren_ai)
                
                st.write("---")
 
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    judul_distribusi = t("2. Distribusi Pengeluaran", "2. Expense Distribution")
                    st.markdown(f"#### {judul_distribusi} ({teks_periode})")
                    nilai_pengeluaran = [df_filtered[kat].sum() for kat in kategori_valid]
                    df_pie = pd.DataFrame({'Kategori': kategori_valid, 'Nominal': nilai_pengeluaran})
                    df_pie = df_pie[df_pie['Nominal'] > 0] 
                    if not df_pie.empty:
                        fig_pie = px.pie(df_pie, values='Nominal', names='Kategori', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(margin=dict(t=10, b=10, l=0, r=0), showlegend=False)
                        st.plotly_chart(fig_pie, use_container_width=True)
                        kategori_bocor = df_pie.loc[df_pie['Nominal'].idxmax()]
                        persentase_bocor = (kategori_bocor['Nominal'] / df_pie['Nominal'].sum()) * 100
                        msg_vampir = t(
                            f"**Interpretasi AI:** Kategori **{kategori_bocor['Kategori']}** adalah 'vampir' pengeluaran Anda pada periode ini, menyedot **{persentase_bocor:.1f}%** ({format_rp(kategori_bocor['Nominal'])}) dari total pengeluaran.",
                            f"**AI Interpretation:** The **{kategori_bocor['Kategori']}** category is your expense 'vampire' this period, sucking up **{persentase_bocor:.1f}%** ({format_rp(kategori_bocor['Nominal'])}) of total expenses."
                        )
                        st.success(msg_vampir)
                    
                    else: st.write("Belum ada pengeluaran pada periode ini.")
 
                with col_g2:
                    judul_budget = t("3. Budget vs Aktual", "3. Budget vs Actual")
                    st.markdown(f"#### {judul_budget} ({teks_periode})")
                    
                    if not df_budget.empty:
                        budget_kategori = df_budget['kategori'].tolist()
                        budget_nominal = df_budget['nominal'].tolist()
                        jumlah_bulan = len(df_filtered)
                        aktual_nominal = [df_filtered[kat].sum() if kat in df_filtered.columns else 0 for kat in budget_kategori]
                        
                        df_budget_chart = pd.DataFrame({'Kategori': budget_kategori, 'Target Budget': [n * jumlah_bulan for n in budget_nominal], 'Aktual Terpakai': aktual_nominal})
                        
                        fig_budget = go.Figure()
                        fig_budget.add_trace(go.Bar(x=df_budget_chart['Kategori'], y=df_budget_chart['Target Budget'], name='Total Limit', marker_color='#E2E8F0'))
                        fig_budget.add_trace(go.Bar(x=df_budget_chart['Kategori'], y=df_budget_chart['Aktual Terpakai'], name='Total Aktual', marker_color='#3B82F6'))
                        fig_budget.update_layout(barmode='overlay', margin=dict(t=10, b=10, l=0, r=0), legend=dict(orientation="h", y=1.1), plot_bgcolor='rgba(0,0,0,0)')
                        fig_budget.update_traces(opacity=0.8)
                        st.plotly_chart(fig_budget, use_container_width=True)
                        
                        df_budget_chart['Sisa'] = df_budget_chart['Target Budget'] - df_budget_chart['Aktual Terpakai']
                        over_budget_cats = df_budget_chart[df_budget_chart['Sisa'] < 0]
                        
                        if not over_budget_cats.empty:
                            kategori_over = ", ".join(over_budget_cats['Kategori'].tolist())
                            msg_over = t(
                                f"**Peringatan AI:** Pada periode **{teks_periode}**, total pengeluaran Anda telah MELEWATI batas budget pada kategori: **{kategori_over}**.",
                                f"**AI Alert:** In **{teks_periode}**, your total expenses EXCEEDED the budget limit in categories: **{kategori_over}**."
                            )
                            st.error(msg_over)
                        else: 
                            msg_aman = t(
                                f"**Interpretasi AI:** Luar biasa! Selama **{teks_periode}**, Anda berhasil menjaga pengeluaran di bawah limit budget.",
                                f"**AI Interpretation:** Excellent! During **{teks_periode}**, you successfully kept your expenses below the budget limit."
                            )
                            st.success(msg_aman)
                            
                    else: 
                        msg_nobudget = t("Belum ada data Budget.", "No Budget data available.")
                        st.write(msg_nobudget)
 
                st.write("---")
 
                judul_target = t("4. Progres Target Tabungan Anda", "4. Your Savings Goal Progress")
                st.markdown(f"#### {judul_target}")

            if not df_target.empty:
                df_target['Progres (%)'] = (df_target['terkumpul'] / df_target['target']) * 100
                df_target['Progres (%)'] = df_target['Progres (%)'].fillna(0).clip(upper=100) 
                df_target_sorted = df_target.sort_values('Progres (%)', ascending=True)
                
                fig_target = px.bar(df_target_sorted, x='Progres (%)', y='tujuan', orientation='h', text=df_target_sorted['Progres (%)'].apply(lambda x: f"{x:.1f}%"), color='Progres (%)', color_continuous_scale='Mint')
                fig_target.update_layout(margin=dict(t=10, b=10, l=0, r=0), xaxis=dict(range=[0, 100]), plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_target, use_container_width=True)
                
                target_terdekat = df_target_sorted.iloc[-1]
                
                if target_terdekat['Progres (%)'] >= 100: 
                    msg_tercapai = t(f"**Selamat!** Anda telah mencapai target **{target_terdekat['tujuan']}**!", f"**Congratulations!** You have reached your **{target_terdekat['tujuan']}** goal!")
                    st.success(msg_tercapai)
                elif target_terdekat['Progres (%)'] > 0: 
                    msg_dekat = t(f"**Interpretasi AI:** Anda paling dekat untuk mencapai target **{target_terdekat['tujuan']}** ({target_terdekat['Progres (%)']:.1f}%).", f"**AI Interpretation:** You are closest to reaching your **{target_terdekat['tujuan']}** goal ({target_terdekat['Progres (%)']:.1f}%).")
                    st.info(msg_dekat)
                else: 
                    msg_mulai = t("**Interpretasi AI:** Mulailah sisihkan uang sedikit demi sedikit.", "**AI Interpretation:** Start setting aside money little by little.")
                    st.info(msg_mulai)
                    
            else: 
                msg_notarget = t("Belum ada target tabungan.", "No savings goals available.")
                st.info(msg_notarget)
                
            st.write("---")
            
            judul_laporan = t("Laporan Rincian Transaksi", "Detailed Transaction Report")
            st.markdown(f"#### {judul_laporan} ({teks_periode})")
            
            tabel_report = df_filtered[kategori_valid].sum().reset_index()
            col_kategori = t("Kategori Pengeluaran", "Expense Category")
            col_total = t("Total Terpakai (Rp)", "Total Spent (Rp)")
            tabel_report.columns = [col_kategori, col_total]
            
            tabel_report = tabel_report[tabel_report[col_total] > 0].sort_values(col_total, ascending=False)
            tabel_report[col_total] = tabel_report[col_total].apply(lambda x: format_rp(x))
            st.dataframe(tabel_report, use_container_width=True, hide_index=True)
 
# ==========================================
# 5. MENU: CHATBOT
# ==========================================
elif selected == "chatbot":
    import anthropic
 
    judul_chatbot = t("🤖 AI Penasihat Keuangan", "🤖 AI Financial Advisor")
    sub_chatbot = t("Tanyakan insight, tips keuangan, atau analisis pengeluaran Anda secara real-time.", "Ask for financial insights, tips, or analyze your expenses in real-time.")
 
    st.markdown(f"## {judul_chatbot}")
    st.markdown(f"<p style='color: var(--text-color); opacity: 0.7;'>{sub_chatbot}</p>", unsafe_allow_html=True)
    # --- Siapkan konteks data keuangan untuk dikirim ke AI ---
    def build_financial_context():
        lines = []
 
        # Ringkasan bulanan
        if not df.empty:
            lines.append("=== DATA KEUANGAN BULANAN ===")
            df_display = df.copy()
            df_display['Bulan'] = df_display['Bulan'].dt.strftime('%B %Y')
            lines.append(df_display.tail(6).to_string(index=False))
 
        # Budget
        try:
            supabase = st.session_state.supabase
            user_id = st.session_state.user.id
            res_budget = supabase.table("budget").select("*").eq("user_id", user_id).execute()
            df_budget_ctx = pd.DataFrame(res_budget.data)
            if not df_budget_ctx.empty:
                df_budget_ctx = df_budget_ctx.drop(columns=["user_id"], errors="ignore")
                lines.append("\n=== SETTING BUDGET PER KATEGORI ===")
                lines.append(df_budget_ctx.to_string(index=False))
        except:
            pass
 
        # Target tabungan
        try:
            supabase = st.session_state.supabase
            user_id = st.session_state.user.id
            res_target = supabase.table("target").select("*").eq("user_id", user_id).execute()
            df_target_ctx = pd.DataFrame(res_target.data)
            if not df_target_ctx.empty:
                df_target_ctx = df_target_ctx.drop(columns=["user_id"], errors="ignore")
                lines.append("\n=== TARGET TABUNGAN ===")
                lines.append(df_target_ctx.to_string(index=False))
        except:
            pass
 
        # Transaksi harian terakhir
        try:
            supabase = st.session_state.supabase
            user_id = st.session_state.user.id
            res_harian = supabase.table("harian").select("*").eq("user_id", user_id).order("id", desc=True).limit(10).execute()
            df_harian_ctx = pd.DataFrame(res_harian.data)
            if not df_harian_ctx.empty:
                df_harian_ctx = df_harian_ctx.drop(columns=["user_id"], errors="ignore")
                lines.append("\n=== 10 TRANSAKSI HARIAN TERAKHIR ===")
                lines.append(df_harian_ctx.to_string(index=False))
        except:
            pass
 
        return "\n".join(lines) if lines else "Belum ada data keuangan tersedia."
 
    SYSTEM_PROMPT = f"""Kamu adalah AI Financial Advisor bernama SmartMoney Assistant untuk pengguna dengan email {st.session_state.user.email}.
Kamu adalah asisten keuangan yang cerdas, ramah, dan berbicara dalam Bahasa Indonesia.
Tugasmu adalah membantu pengguna memahami kondisi keuangan mereka, memberikan saran penghematan, 
tips investasi, dan analisis berdasarkan data nyata pengguna.
 
Berikut adalah data keuangan terkini pengguna:
{build_financial_context()}
 
Panduan menjawab:
- Gunakan data di atas saat menjawab pertanyaan tentang pengeluaran, pemasukan, tabungan, atau budget.
- Berikan jawaban yang konkret, ringkas, dan actionable.
- Gunakan format yang mudah dibaca (boleh gunakan bullet points atau angka).
- Selalu format angka dalam Rupiah (Rp x.xxx.xxx).
- Bersikap suportif dan motivatif, bukan menghakimi.
- Jika ditanya hal di luar keuangan, tetap jawab dengan ramah tapi arahkan kembali ke topik keuangan.
"""
 
    # --- Inisialisasi riwayat chat ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Halo John! 👋 Saya SmartMoney Assistant, AI Advisor keuangan Anda.\n\nSaya sudah membaca data keuangan Anda dan siap membantu menganalisis pengeluaran, memberikan tips menabung, atau menjawab pertanyaan finansial apapun. Apa yang ingin Anda diskusikan hari ini?"
            }
        ]
 
    # --- Tampilkan riwayat chat ---
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
 
    # --- Input & proses pesan baru ---
    if prompt := st.chat_input("Tanya sesuatu, misal: 'Bulan mana pengeluaran saya paling boros?'"):
        # Tampilkan pesan user
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
 
        # Panggil Anthropic API
        with st.chat_message("assistant"):
            with st.spinner("SmartMoney sedang menganalisis..."):
                try:
                    client = anthropic.Anthropic()
 
                    # Bangun messages (hanya role user & assistant, tanpa system)
                    api_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                        if m["role"] in ("user", "assistant")
                    ]
 
                    response_obj = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=api_messages
                    )
 
                    ai_response = response_obj.content[0].text
                    st.markdown(ai_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
 
                except anthropic.AuthenticationError:
                    err_msg = "⚠️ **API Key tidak valid.** Pastikan variabel lingkungan `ANTHROPIC_API_KEY` sudah diset dengan benar."
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
                except anthropic.RateLimitError:
                    err_msg = "⚠️ **Batas penggunaan API tercapai.** Silakan coba beberapa saat lagi."
                    st.warning(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
                except Exception as e:
                    err_msg = f"⚠️ **Terjadi kesalahan:** {str(e)}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
 
    # --- Tombol reset chat ---
    st.write("")
    col_reset, col_spacer = st.columns([1, 4])
    with col_reset:
        if st.button("🗑️ Reset Percakapan", use_container_width=True):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "Halo John! 👋 Percakapan baru dimulai. Ada yang ingin Anda diskusikan tentang keuangan Anda?"
                }
            ]
            st.rerun()
 
# ==========================================
# 6. MENU: SETTINGS
# ==========================================
elif selected == "settings":
    lang = st.session_state.language
    curr = st.session_state.currency
 
    st.title(t("⚙️ Settings Akun", "⚙️ Account Settings"))
    col_kiri, col_kanan = st.columns(2)
 
    with col_kiri:
        # --- Profile ---
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.subheader(t("👤 Profil", "👤 Profile Settings"))
        
        # 1. Ambil nama dari metadata Supabase (jika sudah pernah diset sebelumnya)
        user_metadata = st.session_state.user.user_metadata if hasattr(st.session_state.user, 'user_metadata') and st.session_state.user.user_metadata else {}
        current_name = user_metadata.get("full_name", "User SmartMoney")
        
        # Simpan di session_state agar tampilannya stabil
        if "full_name" not in st.session_state:
            st.session_state.full_name = current_name
            
        # 2. Tangkap inputan nama baru ke dalam variabel 'new_name'
        new_name = st.text_input(t("Nama Lengkap", "Full Name"), value=st.session_state.full_name)
        st.text_input("Email", value=st.session_state.user.email, disabled=True)
        
        # 3. Beri aksi saat tombol diklik
        if st.button(t("Simpan Perubahan", "Save Changes"), type="primary"):
            if new_name.strip() == "":
                st.error(t("Nama tidak boleh kosong!", "Name cannot be empty!"))
            else:
                try:
                    supabase = st.session_state.supabase
                    # Update metadata user di Supabase
                    supabase.auth.update_user({
                        "data": {"full_name": new_name}
                    })
                    
                    # Update data di session aplikasi agar langsung berubah
                    st.session_state.full_name = new_name
                    st.success(t("Profil berhasil diperbarui!", "Profile successfully updated!"))
                except Exception as e:
                    st.error(f"Gagal menyimpan profil: {e}")
                    
        st.markdown('</div>', unsafe_allow_html=True)
 
        # --- Security ---
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.subheader(t("🔒 Keamanan", "🔒 Security"))
        st.button(t("Ganti Password", "Change Password"))
        st.button(t("Aktifkan Autentikasi Dua Faktor", "Enable Two-Factor Authentication"))
        st.markdown('</div>', unsafe_allow_html=True)
 
    with col_kanan:
        # --- Notifications ---
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.subheader(t("🔔 Notifikasi", "🔔 Notifications"))
        st.checkbox(t("Peringatan budget", "Budget alerts"), value=True)
        st.checkbox(t("Notifikasi transaksi", "Transaction notifications"), value=True)
        st.checkbox(t("Laporan mingguan", "Weekly reports"), value=False)
        st.markdown('</div>', unsafe_allow_html=True)
 
        # === LANGUAGE TOGGLE ===
        st.markdown(f"**{'🌐 Bahasa Aplikasi' if lang == 'ID' else '🌐 App Language'}**")
        st.caption(t("Bahasa aktif saat ini:", "Current active language:") + f" **{'🇮🇩 Bahasa Indonesia' if lang == 'ID' else '🇺🇸 English'}**")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            btn_id = st.button(
                "🇮🇩 Bahasa Indonesia",
                use_container_width=True,
                type="primary" if lang == "ID" else "secondary",
                key="btn_lang_id"
            )
        with col_l2:
            btn_en = st.button(
                "🇺🇸 English",
                use_container_width=True,
                type="primary" if lang == "EN" else "secondary",
                key="btn_lang_en"
            )
        if btn_id and lang != "ID":
            st.session_state.language = "ID"
            st.rerun()
        if btn_en and lang != "EN":
            st.session_state.language = "EN"
            st.rerun()
 
        st.write("")
 
        # === CURRENCY TOGGLE ===
        st.markdown(f"**{'💱 Mata Uang' if lang == 'ID' else '💱 Currency'}**")
        st.caption(
            t("Mata uang aktif saat ini:", "Current active currency:") +
            f" **{'🇮🇩 IDR – Rupiah (Rp)' if curr == 'IDR' else '🇺🇸 USD – Dollar ($)'}**"
        )
        st.caption(t(f"Kurs konversi: 1 USD = Rp {USD_RATE:,}".replace(",", "."),
                     f"Exchange rate: 1 USD = Rp {USD_RATE:,}"))
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            btn_idr = st.button(
                "🇮🇩 IDR – Rupiah",
                use_container_width=True,
                type="primary" if curr == "IDR" else "secondary",
                key="btn_curr_idr"
            )
        with col_c2:
            btn_usd = st.button(
                "🇺🇸 USD – Dollar",
                use_container_width=True,
                type="primary" if curr == "USD" else "secondary",
                key="btn_curr_usd"
            )
        if btn_idr and curr != "IDR":
            st.session_state.currency = "IDR"
            st.rerun()
        if btn_usd and curr != "USD":
            st.session_state.currency = "USD"
            st.rerun()
 
        st.markdown('</div>', unsafe_allow_html=True)