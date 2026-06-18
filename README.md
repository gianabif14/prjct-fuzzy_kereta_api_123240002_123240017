# 🚆 SPK Pemilihan Kereta Api dengan Fuzzy Tsukamoto

Sistem Pendukung Keputusan (SPK) untuk pemilihan kereta api terbaik menggunakan metode **Fuzzy Tsukamoto**. Aplikasi ini dibangun dengan **Streamlit** dan dirancang untuk membantu pengguna memilih kereta api dari Stasiun Pasarsenen (PSE) ke Yogyakarta (YK) atau Lempuyangan (LPN) berdasarkan kriteria **harga**, **jenis rangkaian**, dan **waktu tempuh**.

---

## 📌 Fitur Utama

- 🔍 **Filter Data** - Pengguna dapat memilih stasiun tujuan (YK/LPN) dan kelas kereta (Semua/Ekonomi/Eksekutif)
- 📊 **Perhitungan Fuzzy Tsukamoto** - Proses fuzzifikasi, inferensi (27 aturan), dan defuzzifikasi
- 📈 **Visualisasi Grafik** - Kurva fungsi keanggotaan untuk setiap kriteria
- 🏆 **Ranking Rekomendasi** - Urutan kereta terbaik dengan skor kelayakan (0-100)
- 📋 **Detail Perhitungan** - Tampilan rinci derajat keanggotaan dan aturan yang terpicu

---

## 🗂️ Struktur Proyek
prjct-fuzzy_kereta_api_123240002_123240017/  
├── Data KAI PSE-YK,LPN.csv # Dataset utama  
├── fuzzy.py # Aplikasi utama Streamlit  
└── README.md # Dokumentasi proyek  

---

## 📊 Dataset

Dataset berisi informasi jadwal kereta api dari Stasiun Pasarsenen (PSE) ke 22 stasiun tujuan di Pulau Jawa pada **Minggu, 24 Mei 2026**.

**Statistik Dataset:**
- Jumlah Data: **1.854** jadwal kereta
- Jumlah Tujuan: **22** stasiun
- Jumlah Kolom: **15** atribut
- Kelas: Ekonomi dan Eksekutif

**Sumber Dataset:**
[Kaggle - Jadwal KAI Pasarsenen 24 Mei 2026](https://gaf.my.id/dataset-kai)

---

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan buat *pull request* atau *issue* untuk saran dan perbaikan.

---

## 👨‍💻 Tim Pengembang

**Kelompok SCPK KAI**

- Fahri Hidayatullah (123240002)
- Gian Abi Firdaus (123240017)

---

## 📧 Kontak

Email: [contact@gaf.my.id](mailto:contact@gaf.my.id)
