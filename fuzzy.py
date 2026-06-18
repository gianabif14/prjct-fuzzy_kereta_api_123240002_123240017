import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#  KONFIGURASI 
KAI_LOGO = "https://upload.wikimedia.org/wikipedia/commons/5/56/Logo_PT_Kereta_Api_Indonesia_%28Persero%29_2020.svg"

st.set_page_config(
    page_title="SPK Pemilihan Kereta Api - Metode Fuzzy Tsukamoto",
    page_icon=KAI_LOGO,
    layout="wide",
    initial_sidebar_state="expanded",
)

#  GAYA TAMPILAN (CSS) 
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .kai-header {
        background: linear-gradient(135deg, #0D2E5C 0%, #163B6E 45%, #F26522 100%);
        padding: 28px 32px; border-radius: 12px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .kai-header img {
        height: 58px; background: rgba(255,255,255,0.9);
        padding: 6px 10px; border-radius: 8px;
    }
    .kai-header-text h1 {
        color: #fff; font-size: 26px; font-weight: 700;
        margin: 0; letter-spacing: -0.3px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .kai-header-text p {
        color: rgba(255,255,255,0.9); font-size: 14px; margin: 4px 0 0 0;
    }

    .step-badge {
        display: inline-block; background: #F26522; color: #fff;
        width: 28px; height: 28px; border-radius: 50%;
        text-align: center; line-height: 28px;
        font-weight: 600; font-size: 14px; margin-right: 8px;
    }
    .step-badge.inactive { background: #555; }
    .step-badge.done { background: #2ecc71; }

    .section-title {
        font-size: 20px; font-weight: 600; color: #1a1a2e;
        border-left: 4px solid #F26522; padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    .rank-card {
        border-radius: 10px; padding: 16px 20px;
        margin-bottom: 8px; display: flex;
        align-items: center; gap: 16px;
    }
    .rank-card.gold   { background: linear-gradient(135deg, #F7C948, #F5A623); color: #fff; }
    .rank-card.silver  { background: linear-gradient(135deg, #BCC6CC, #8E9EAB); color: #fff; }
    .rank-card.bronze  { background: linear-gradient(135deg, #C9956B, #A0724A); color: #fff; }
    .rank-card.normal  { background: #f0f2f6; color: #1a1a2e; }

    .rank-number { font-size: 28px; font-weight: 700; min-width: 40px; text-align: center; }
    .rank-name { font-size: 16px; font-weight: 600; flex: 1; }
    .rank-score { font-size: 16px; font-weight: 500; }

    div[data-testid="stSidebar"] { background: #1a1a2e; }
    div[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    div[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

#  PEMETAAN DATA & SKOR 

# Konversi jenis rangkaian teks kualitatif dari berkas CSV menjadi nilai tegas (1-5)
RANGKAIAN_MAP = {
    'Eksekutif New Generation Stainless Steel': 5,
    'New Generation Stainless Steel': 5,
    'Eksekutif New Generation Mild Steel': 4,
    'Eksekutif New Generation Modifikasi Mild Steel': 4,
    'New Generation Modifikasi': 4,
    'Eksekutif Mild Steel': 3,
    'Premium Stainless Steel': 3,
    'Premium Mild Steel': 2,
    'Premium Modifikasi Mild Steel': 2,
    'Ekonomi Modifikasi': 2,
    'Mild Steel PSO': 1,
}


@st.cache_data
def load_data():
    # Membaca data CSV dan membersihkan format penulisan titik pada nominal harga tiket
    df = pd.read_csv('Data KAI PSE-YK,LPN.csv', sep=';', dtype={'Harga (Rp)': str})
    df['Harga (Rp)'] = df['Harga (Rp)'].str.replace('.', '', regex=False).astype(int)
    return df


#  RUMUS KURVA KEANGGOTAAN FUZZY 

def linear_down(x, a, b):
    """Fungsi Kurva Linier Turun: Bernilai 1 saat x <= a, bernilai 0 saat x >= b."""
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)


def linear_up(x, a, b):
    """Fungsi Kurva Linier Naik: Bernilai 0 saat x <= a, bernilai 1 saat x >= b."""
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def triangular(x, a, b, c):
    """Fungsi Kurva Segitiga: Bernilai 0 di luar batas [a,c], bernilai puncak 1 tepat pada titik b."""
    if x <= a or x >= c:
        return 0.0
    if x <= b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


#  PROSES FUZZIFIKASI INPUT 

def fuzzify_biaya(val, lo, mid, hi):
    """Mengubah nilai riil harga menjadi derajat keanggotaan (Murah, Sedang, Mahal)"""
    return {
        'Murah': linear_down(val, lo, mid),
        'Sedang': triangular(val, lo, mid, hi),
        'Mahal': linear_up(val, mid, hi),
    }


def fuzzify_waktu(val, lo, mid, hi):
    """Mengubah nilai riil durasi menjadi derajat keanggotaan (Cepat, Normal, Lama)"""
    return {
        'Cepat': linear_down(val, lo, mid),
        'Normal': triangular(val, lo, mid, hi),
        'Lama': linear_up(val, mid, hi),
    }


def fuzzify_rangkaian(val):
    """Mengubah skor riil rangkaian (1-5) menjadi derajat keanggotaan (Kurang, Biasa, Bagus)"""
    return {
        'Kurang': linear_down(val, 1, 3),
        'Biasa': triangular(val, 1, 3, 5),
        'Bagus': linear_up(val, 3, 5),
    }


#  GENERATOR GRAFIK DIAGRAM 

def plot_membership_functions(title, lo, mid, hi, labels, current_val=None, is_currency=False):
    """Membuat gambar kurva grafik fungsi keanggotaan sesuai standar visual laboratorium"""
    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#1E222B')
    
    x_vals = np.linspace(lo - (hi - lo) * 0.1, hi + (hi - lo) * 0.1, 500)
    
    # Hitung data kurva berdasarkan fungsi matematika
    y_down = [linear_down(x, lo, mid) for x in x_vals]
    y_tri = [triangular(x, lo, mid, hi) for x in x_vals]
    y_up = [linear_up(x, mid, hi) for x in x_vals]
    
    # Plot kurva garis berwarna
    ax.plot(x_vals, y_down, label=labels[0], color='#2ecc71', linewidth=2)
    ax.plot(x_vals, y_tri, label=labels[1], color='#F5A623', linewidth=2)
    ax.plot(x_vals, y_up, label=labels[2], color='#e74c3c', linewidth=2)
    
    # Tambahkan garis vertikal putus-putus jika nilai spesifik kereta dipilih
    if current_val is not None:
        ax.axvline(x=current_val, color='#ffffff', linestyle='--', alpha=0.7)
        ax.scatter([current_val], [0], color='#ffffff', zorder=5, label=f"Nilai: {current_val:,.0f}" if is_currency else f"Nilai: {current_val}")

    ax.set_title(title, color='#e0e0e0', fontsize=10, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.tick_params(colors='#b0b0b0', labelsize=8)
    ax.grid(True, linestyle=':', alpha=0.3, color='#b0b0b0')
    
    # Penyederhanaan penulisan label ribuan pada sumbu X harga tiket (simbol k)
    if is_currency:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x/1000)}k" if x >= 1000 else f"{int(x)}"))
        
    legend = ax.legend(loc='upper right', fontsize=7, facecolor='#1E222B', edgecolor='none')
    for text in legend.get_texts():
        text.set_color('#e0e0e0')
        
    plt.tight_layout()
    return fig


#  KNOWLEDGE BASE / BASIS ATURAN HARCODED (27 RULES) 
# Struktur data basis aturan permanen penentu kesimpulan kualitatif dan bobot dasar (Z-Base)

RULES = [
    # --- KELOMPOK BIAYA: MURAH ---
    ('Murah', 'Cepat', 'Bagus', 'Sangat Direkomendasikan', 100.0),
    ('Murah', 'Cepat', 'Biasa', 'Direkomendasikan', 75.0),
    ('Murah', 'Cepat', 'Kurang', 'Direkomendasikan', 66.0),
    ('Murah', 'Normal', 'Bagus', 'Sangat Direkomendasikan', 85.0),
    ('Murah', 'Normal', 'Biasa', 'Direkomendasikan', 70.0),
    ('Murah', 'Normal', 'Kurang', 'Tidak Direkomendasikan', 45.0),
    ('Murah', 'Lama', 'Bagus', 'Tidak Direkomendasikan', 40.0),
    ('Murah', 'Lama', 'Biasa', 'Tidak Direkomendasikan', 35.0),
    ('Murah', 'Lama', 'Kurang', 'Sangat Tidak Direkomendasikan', 15.0),

    # --- KELOMPOK BIAYA: SEDANG ---
    ('Sedang', 'Cepat', 'Bagus', 'Sangat Direkomendasikan', 85.0),
    ('Sedang', 'Cepat', 'Biasa', 'Direkomendasikan', 70.0),
    ('Sedang', 'Cepat', 'Kurang', 'Tidak Direkomendasikan', 45.0),
    ('Sedang', 'Normal', 'Bagus', 'Direkomendasikan', 66.0),
    ('Sedang', 'Normal', 'Biasa', 'Tidak Direkomendasikan', 40.0),
    ('Sedang', 'Normal', 'Kurang', 'Tidak Direkomendasikan', 35.0),
    ('Sedang', 'Lama', 'Bagus', 'Tidak Direkomendasikan', 33.0),
    ('Sedang', 'Lama', 'Biasa', 'Sangat Tidak Direkomendasikan', 20.0),
    ('Sedang', 'Lama', 'Kurang', 'Sangat Tidak Direkomendasikan', 10.0),

    # --- KELOMPOK BIAYA: MAHAL ---
    ('Mahal', 'Cepat', 'Bagus', 'Direkomendasikan', 66.0),
    ('Mahal', 'Cepat', 'Biasa', 'Tidak Direkomendasikan', 40.0),
    ('Mahal', 'Cepat', 'Kurang', 'Tidak Direkomendasikan', 35.0),
    ('Mahal', 'Normal', 'Bagus', 'Tidak Direkomendasikan', 40.0),
    ('Mahal', 'Normal', 'Biasa', 'Sangat Tidak Direkomendasikan', 20.0),
    ('Mahal', 'Normal', 'Kurang', 'Sangat Tidak Direkomendasikan', 15.0),
    ('Mahal', 'Lama', 'Bagus', 'Sangat Tidak Direkomendasikan', 15.0),
    ('Mahal', 'Lama', 'Biasa', 'Sangat Tidak Direkomendasikan', 5.0),
    ('Mahal', 'Lama', 'Kurang', 'Sangat Tidak Direkomendasikan', 0.0),
]

# Kamus konversi internal penyelarasan penulisan string antar modul fungsi
_B_MAP = {'Murah': 'Murah', 'Sedang': 'Sedang', 'Mahal': 'Mahal'}
_W_MAP = {'Cepat': 'Cepat', 'Normal': 'Normal', 'Lama': 'Lama'}
_R_MAP = {'Bagus': 'Bagus', 'Biasa': 'Biasa', 'Kurang': 'Kurang'}


#  MESIN INFERENSI FUZZY TSUKAMOTO 

def tsukamoto(biaya_val, waktu_val, rangkaian_val, b_lo, b_mid, b_hi, w_lo, w_mid, w_hi):
    """Mengeksekusi proses inferensi MIN dan defuzzifikasi Tsukamoto rata-rata berbobot"""
    mu_b = fuzzify_biaya(biaya_val, b_lo, b_mid, b_hi)
    mu_w = fuzzify_waktu(waktu_val, w_lo, w_mid, w_hi)
    mu_r = fuzzify_rangkaian(rangkaian_val)

    sum_az = 0.0
    sum_a = 0.0
    rule_details = []

    for idx, (b_term, w_term, r_term, conseq, z_base) in enumerate(RULES, 1):
        b_key = _B_MAP[b_term]
        w_key = _W_MAP[w_term]
        r_key = _R_MAP[r_term]

        # Langkah Inferensi: Cari kekuatan aturan / alpha predikat menggunakan fungsi minimal (MIN)
        alpha = min(mu_b[b_key], mu_w[w_key], mu_r[r_key])
        
        # Langkah Implikasi: Hitung nilai tegas Z individual sesuai fungsi linier naik/turun rumpun output
        if conseq == 'Sangat Direkomendasikan':
            z = z_base + alpha * (100.0 - z_base)
        elif conseq == 'Direkomendasikan':
            z = z_base + alpha * (85.0 - z_base) if alpha > 0.5 else z_base - (1.0 - alpha) * 15.0
        elif conseq == 'Tidak Direkomendasikan':
            z = z_base * (1.0 - alpha) + alpha * 33.0
        else: # Sangat Tidak Direkomendasikan
            z = z_base * (1.0 - alpha)

        display_r_term = 'Bagus' if r_term == 'Bagus' else 'Biasa' if r_term == 'Kurang' else 'Kurang'

        rule_details.append({
            'Aturan': f"R{idx}",
            'Biaya': b_term,
            'Waktu': w_term,
            'Rangkaian': display_r_term,
            'mu_b': round(mu_b[b_key], 4),
            'mu_w': round(mu_w[w_key], 4),
            'mu_r': round(mu_r[r_key], 4),
            'alpha_predikat': round(alpha, 4),
            'Kesimpulan': conseq,
            'Z_Aturan': round(z, 2),
        })

        sum_az += alpha * z
        sum_a += alpha

    # Langkah Akhir Defuzzifikasi (Weighted Average)
    z_final = sum_az / sum_a if sum_a > 0 else 50.0
    return round(z_final, 2), rule_details, mu_b, mu_w, mu_r


#  ANTARMUKA UTAMA STREAMLIT 

def main():
    st.markdown(f'''
    <div class="kai-header">
        <img src="{KAI_LOGO}" alt="KAI Logo">
        <div class="kai-header-text">
            <h1>Sistem Pendukung Keputusan Pemilihan Kereta Api</h1>
            <p>Metode Fuzzy Tsukamoto &mdash; Rute: Pasar Senen (PSE) &rarr; Yogyakarta (YK) / Lempuyangan (LPN)</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    data = load_data()

    # Inisialisasi awal variabel kontrol session state Streamlit
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = None
    if 'hasil_fuzzy' not in st.session_state:
        st.session_state.hasil_fuzzy = None

    #  Panel Menu Samping (Sidebar) 
    with st.sidebar:
        st.image(KAI_LOGO, width=120)
        st.markdown("#### Langkah Analisis")

        steps = [
            "Penyaringan Kereta (Filter)",
            "Proses Komputasi Fuzzy",
            "Hasil Urutan Rekomendasi",
        ]
        for i, step_name in enumerate(steps, 1):
            if i < st.session_state.step:
                badge = "done"
            elif i == st.session_state.step:
                badge = ""
            else:
                badge = "inactive"
            st.markdown(
                f'<span class="step-badge {badge}">{i}</span> {step_name}',
                unsafe_allow_html=True,
            )

        st.divider()
        st.caption("Metode: Fuzzy Tsukamoto")
        st.caption("© Copyright 2026. All rights reserved")

    # Alur navigasi multi-halaman kontrol session state
    if st.session_state.step == 1:
        step1_filter(data)
    elif st.session_state.step == 2:
        step2_perhitungan()
    elif st.session_state.step == 3:
        step3_hasil()


#  HALAMAN 1 – PENYARINGAN KERETA (FILTER) 

def step1_filter(data):
    st.markdown('<div class="section-title">Penyaringan Kereta (Filter)</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        stasiun = st.selectbox(
            "Pilih Stasiun Tujuan Perjalanan",
            options=["YK", "LPN"],
            format_func=lambda x: "YOGYAKARTA (YK)" if x == "YK" else "LEMPUYANGAN (LPN)",
        )
    with col2:
        available_kelas = sorted(data[data['KodeStasiunTujuan'] == stasiun]['Kelas'].unique().tolist())
        kelas_options = ["Semua Kelas"] + available_kelas
        selected_kelas = st.selectbox("Pilih Kelas Kereta Api", options=kelas_options)

    # Penyaringan baris data dataframe berdasarkan kriteria terpilih
    df = data[data['KodeStasiunTujuan'] == stasiun].drop_duplicates(subset=['Nama Kereta', 'Kelas'])
    if selected_kelas != "Semua Kelas":
        df = df[df['Kelas'] == selected_kelas]
    df = df.reset_index(drop=True)

    st.info(f"Sistem berhasil menemukan **{len(df)}** jadwal perjalanan kereta api yang sesuai.")

    if len(df) > 0:
        display_df = df[['Nama Kereta', 'Kelas', 'Jenis Rangkaian', 'Harga (Rp)', 'Durasi (menit)']].copy()
        display_df['Harga (Rp)'] = display_df['Harga (Rp)'].apply(lambda x: f"Rp{x:,.0f}")
        st.dataframe(display_df, use_container_width=True)

        if st.button("Lanjutkan ke Proses Perhitungan Fuzzy ➡️", use_container_width=True, type="primary"):
            st.session_state.filtered_df = df
            st.session_state.step = 2
            st.rerun()
    else:
        st.warning("Maaf, tidak ada jadwal data kereta api yang memenuhi kriteria filter ini.")


#  HALAMAN 2 – PROSES KOMPUTASI FUZZY 

def step2_perhitungan():
    st.markdown('<div class="section-title">Proses Komputasi Logika Fuzzy Tsukamoto</div>', unsafe_allow_html=True)

    df = st.session_state.filtered_df
    if df is None or len(df) == 0:
        st.error("Data kosong. Silakan kembali ke langkah penyaringan pertama.")
        return

    df = df.copy()
    df['Skor_Rangkaian'] = df['Jenis Rangkaian'].map(RANGKAIAN_MAP).fillna(1).astype(int)

    # Penentuan batas semesta pembicaraan (Universe) secara dinamis dari tabel aktif
    b_lo = float(df['Harga (Rp)'].min())
    b_hi = float(df['Harga (Rp)'].max())
    b_mid = (b_lo + b_hi) / 2.0

    w_lo = float(df['Durasi (menit)'].min())
    w_hi = float(df['Durasi (menit)'].max())
    w_mid = (w_lo + w_hi) / 2.0

    st.markdown("##### Parameter Batas Otomatis Semesta Pembicaraan (Universe)")
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown(f"""
        **Variabel Biaya (Rupiah)** 
        - Batas Bawah Tiket (Murah Penuh): `Rp{b_lo:,.0f}`  
        - Titik Tengah (Median): `Rp{b_mid:,.0f}`  
        - Batas Atas Tiket (Mahal Penuh): `Rp{b_hi:,.0f}`
        """)
    with tc2:
        st.markdown(f"""
        **Variabel Waktu Tempuh (Menit)** 
        - Batas Bawah Durasi (Cepat Penuh): `{w_lo:.0f}` menit  
        - Titik Tengah (Median): `{w_mid:.0f}` menit  
        - Batas Atas Durasi (Lama Penuh): `{w_hi:.0f}` menit
        """)

    # Menampilkan visualisasi kurva semesta pembicaraan global variabel
    st.markdown("##### Representasi Grafik Visual Fungsi Keanggotaan Variabel")
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        fig_b = plot_membership_functions("Kurva Variabel: Biaya (Harga)", b_lo, b_mid, b_hi, ["Murah", "Sedang", "Mahal"], is_currency=True)
        st.pyplot(fig_b)
    with gc2:
        fig_w = plot_membership_functions("Kurva Variabel: Waktu Tempuh", w_lo, w_mid, w_hi, ["Cepat", "Normal", "Lama"])
        st.pyplot(fig_w)
    with gc3:
        fig_r = plot_membership_functions("Kurva Variabel: Jenis Rangkaian", 1, 3, 5, ["Kurang", "Biasa", "Bagus"])
        st.pyplot(fig_r)

    st.markdown("### Variabel Kualitatif Jenis Rangkaian (Skor Tegas 1-5)")
    with st.expander("📋 Tampilkan Tabel Aturan Konversi Jenis Rangkaian → Skor Tegas"):
        map_rows = []
        for name, score in sorted(RANGKAIAN_MAP.items(), key=lambda x: -x[1]):
            map_rows.append({'Nama Jenis Rangkaian Armada': name, 'Skor Konversi': score})
        st.dataframe(pd.DataFrame(map_rows), use_container_width=True)

    st.markdown("---")

    results = []
    all_details = {}

    progress = st.progress(0, text="Sedang menjalankan kalkulasi matematis...")
    total = len(df)

    # Looping perulangan kalkulasi otomatis fuzzy Tsukamoto untuk seluruh baris kereta
    for i, (_, row) in enumerate(df.iterrows()):
        biaya = float(row['Harga (Rp)'])
        waktu = float(row['Durasi (menit)'])
        r_score = float(row['Skor_Rangkaian'])

        z_final, rule_details, mu_b, mu_w, mu_r = tsukamoto(
            biaya, waktu, r_score, b_lo, b_mid, b_hi, w_lo, w_mid, w_hi
        )

        label = f"{row['Nama Kereta']} ({row['Kelas']})"
        results.append({
            'Nama Kereta': row['Nama Kereta'],
            'Kelas': row['Kelas'],
            'Jenis Rangkaian': row['Jenis Rangkaian'],
            'Skor_Rangkaian': int(r_score),
            'Harga (Rp)': int(biaya),
            'Durasi (menit)': int(waktu),
            'Skor_Fuzzy': z_final,
            '_label': label,
        })
        all_details[label] = {
            'rules': rule_details,
            'mu_biaya': mu_b,
            'mu_waktu': mu_w,
            'mu_rangkaian': mu_r,
            'z_final': z_final,
            'biaya': biaya,
            'waktu': waktu,
            'rangkaian_score': r_score,
        }

        progress.progress((i + 1) / total, text=f"Memproses kalkulasi data armada {i + 1}/{total} ...")

    progress.empty()

    result_df = pd.DataFrame(results).sort_values('Skor_Fuzzy', ascending=False).reset_index(drop=True)

    st.success(f"Proses kalkulasi berhasil! Sebanyak {len(result_df)} kereta api telah selesai dievaluasi.")

    st.markdown('<div class="section-title">Tabel Ringkasan Hasil Fuzzifikasi & Skor Akhir</div>', unsafe_allow_html=True)
    show_df = result_df[['Nama Kereta', 'Kelas', 'Jenis Rangkaian', 'Skor_Rangkaian', 'Harga (Rp)', 'Durasi (menit)', 'Skor_Fuzzy']].copy()
    show_df['Harga (Rp)'] = show_df['Harga (Rp)'].apply(lambda x: f"Rp{x:,.0f}")
    st.dataframe(show_df, use_container_width=True)

    # Penayangan komponen interaktif penelusuran visual irisan kurva individu per kereta
    st.markdown('<div class="section-title">Eksplorasi Detail Perhitungan Individu Kereta</div>', unsafe_allow_html=True)
    selected_train = st.selectbox("Pilih salah satu kereta untuk melihat irisan grafik & detail 27 aturan:", result_df['_label'].tolist())

    if selected_train:
        detail = all_details[selected_train]

        st.markdown(f"##### Kedudukan Irisan Nilai Riil Armada **{selected_train}** pada Grafik Fungsi Keanggotaan")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.pyplot(plot_membership_functions("μ Kedudukan Nilai Biaya Tiket", b_lo, b_mid, b_hi, ["Murah", "Sedang", "Mahal"], detail['biaya'], is_currency=True))
        with dc2:
            st.pyplot(plot_membership_functions("μ Kedudukan Nilai Waktu Tempuh", w_lo, w_mid, w_hi, ["Cepat", "Normal", "Lama"], detail['waktu']))
        with dc3:
            st.pyplot(plot_membership_functions("μ Kedudukan Nilai Jenis Rangkaian", 1, 3, 5, ["Kurang", "Biasa", "Bagus"], detail['rangkaian_score']))

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Nilai Derajat Keanggotaan (μ) Biaya**")
            for k, v in detail['mu_biaya'].items():
                st.write(f"- Himpunan {k}: {v:.4f}")
        with col_b:
            st.markdown("**Nilai Derajat Keanggotaan (μ) Waktu Tempuh**")
            for k, v in detail['mu_waktu'].items():
                st.write(f"- Himpunan {k}: {v:.4f}")
        with col_c:
            st.markdown("**Nilai Derajat Keanggotaan (μ) Jenis Rangkaian**")
            for k, v in detail['mu_rangkaian'].items():
                st.write(f"- Himpunan {k}: {v:.4f}")

        st.markdown(f"**Skor Hasil Defuzzifikasi Akhir (Z):** Berada pada angka tegas `{detail['z_final']:.2f}` dari batas maksimal 100")

        with st.expander("📊 Tampilkan Tabel Penilaian Evaluasi Detail Evaluasi 27 Aturan"):
            rules_df = pd.DataFrame(detail['rules'])
            st.dataframe(rules_df, use_container_width=True)

    with st.expander("📜 Tampilkan Dokumen Basis Pengetahuan Komparasi Statis (Rule Base)"):
        rule_data = []
        for i, (b, w, r, c, zb) in enumerate(RULES, 1):
            display_r_term = 'Bagus' if r == 'Murah' else 'Biasa' if r == 'Sedang' else 'Kurang'
            rule_data.append({
                'Nomor Aturan': f"R{i}",
                'Kondisi IF Biaya': b,
                'Kondisi AND Waktu Tempuh': w,
                'Kondisi AND Jenis Rangkaian': display_r_term,
                'Kondisi THEN Kesimpulan': c,
                'Nilai Dasar Z-Base': f"{round(zb, 1)}%",
            })
        st.dataframe(pd.DataFrame(rule_data), use_container_width=True)

    st.session_state.hasil_fuzzy = {
        'result_df': result_df,
        'all_details': all_details,
    }

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Lihat Hasil Urutan Rekomendasi Akhir ➡️", use_container_width=True, type="primary"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("← Kembali ke Langkah Pertama", use_container_width=True):
            st.session_state.step = 1
            st.rerun()


#  HALAMAN 3 – HASIL URUTAN REKOMENDASI 

def step3_hasil():
    st.markdown('<div class="section-title">Hasil Peringkat Urutan Rekomendasi Kereta</div>', unsafe_allow_html=True)

    if st.session_state.hasil_fuzzy is None:
        st.error("Data kosong. Silakan jalankan perhitungan kalkulasi fuzzy terlebih dahulu di langkah 2.")
        return

    result_df = st.session_state.hasil_fuzzy['result_df']
    all_details = st.session_state.hasil_fuzzy['all_details']

    sorted_df = result_df.sort_values('Skor_Fuzzy', ascending=False).reset_index(drop=True)

    # Penayangan visualisasi kartu ranking kustom medali
    rank_classes = ['gold', 'silver', 'bronze']
    for i, row in sorted_df.iterrows():
        cls = rank_classes[i] if i < 3 else 'normal'
        label = row['_label']
        skor = row['Skor_Fuzzy']
        st.markdown(
            f'<div class="rank-card {cls}">'
            f'<div class="rank-number">#{i + 1}</div>'
            f'<div class="rank-name">{label}</div>'
            f'<div class="rank-score">Skor Kelayakan: {skor:.2f} / 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"Tampilkan Informasi Detil Nilai Peringkat #{i + 1} — {label}"):
            d = all_details[label]
            st.write(f"Karakteristik Fisik -> Harga Tiket: Rp{d['biaya']:,.0f} | Durasi Tempuh: {d['waktu']:.0f} menit | Skor Rangkaian: {d['rangkaian_score']:.0f}")
            st.write(f"**Formulasi Nilai Defuzzifikasi Akhir (Z Final) = {d['z_final']:.2f}**")
            st.write(f"μ Kriteria Biaya → " + ", ".join(f"{k}={v:.4f}" for k, v in d['mu_biaya'].items()))
            st.write(f"μ Kriteria Waktu Tempuh → " + ", ".join(f"{k}={v:.4f}" for k, v in d['mu_waktu'].items()))
            st.write(f"μ Kriteria Jenis Rangkaian → " + ", ".join(f"{k}={v:.4f}" for k, v in d['mu_rangkaian'].items()))

    # Penayangan visualisasi diagram batang horizontal perbandingan nilai kelayakan
    st.markdown('<div class="section-title">Visualisasi Perbandingan Skor Kelayakan Seluruh Armada</div>', unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(sorted_df) * 0.45)))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    names = sorted_df['_label'].tolist()
    scores = sorted_df['Skor_Fuzzy'].tolist()
    bar_colors = (['#F5A623', '#8E9EAB', '#A0724A'] + ['#F26522'] * max(0, len(scores) - 3))[:len(scores)]

    bars = ax.barh(names, scores, color=bar_colors)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.tick_params(colors='#e0e0e0')
    ax.set_xlabel('Nilai Skor Kelayakan Tingkat Rekomendasi (0-100)', color='#e0e0e0')

    for bar, s in zip(bars, scores):
        ax.text(
            bar.get_width() + 1,
            bar.get_y() + bar.get_height() / 2,
            f'{s:.2f}',
            va='center', fontsize=9, color='#e0e0e0',
        )

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")
    st.markdown('<div class="section-title">Rekomendasi Utama Sistem</div>', unsafe_allow_html=True)
    best = sorted_df.iloc[0]
    st.success(
        f"**Berdasarkan hasil analisis perhitungan logika Fuzzy Tsukamoto, rekomendasi perjalanan terbaik Anda adalah:**\n\n"
        f"🏆 **{best['_label']}** dengan perolehan Skor Kelayakan tertinggi mencapai **{best['Skor_Fuzzy']:.2f} / 100**"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ulangi Analisis dari Awal Kembali ↺", use_container_width=True):
            for k in ['step', 'filtered_df', 'hasil_fuzzy']:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    with col2:
        if st.button("← Kembali ke Halaman Kalkulasi", use_container_width=True):
            st.session_state.step = 2
            st.rerun()


if __name__ == "__main__":
    main()