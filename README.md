Platform Analisis Data Media Sosial Interaktif


Deskripsi Proyek


Pembuatan aplikasi web interaktif berupa dashboard yang mudah digunakan untuk membersihkan, memvisualisasikan, dan menganalisis data kampanye dari media sosial secara cepat dan tepat menggunakan bantuan Kecerdasan Buatan (AI). Aplikasi ini dirancang untuk memungkinkan pengguna memasukkan data secara manual atau mengunggahnya melalui file CSV, kemudian langsung menghasilkan visualisasi yang mendalam dan wawasan strategis.

Tujuan Proyek
Perancangan & Pengembangan: Merancang, mengembangkan, dan menyebarkan aplikasi web dashboard interaktif yang berfokus pada kemudahan penggunaan dan kecepatan analisis kampanye media sosial.

Pemanfaatan AI: Menggunakan AI secara bijaksana dan efektif untuk membantu menyelesaikan masalah analisis data yang ada di industri kreatif saat ini, dengan memberikan ringkasan data yang komprehensif dan rekomendasi strategis yang actionable.

Kolaborasi & Akses Publik: Memanfaatkan alat-alat kolaborasi modern seperti GitHub dan platform deployment Streamlit Cloud untuk menghasilkan solusi yang transparan, mudah dikelola, dan bisa diakses oleh publik.

Fitur-fitur Utama
Aplikasi dashboard ini dilengkapi dengan fitur-fitur utama berikut:

Pilihan Input Data Fleksibel:

Pengguna dapat memasukkan data kampanye secara manual melalui tabel interaktif yang dapat diedit.

Alternatifnya, pengguna dapat mengunggah data langsung dari file CSV dengan struktur kolom yang telah ditentukan.

Pembersihan Data Otomatis:

Data yang dimasukkan (baik manual maupun CSV) akan secara otomatis dibersihkan dan dinormalisasi. Ini termasuk konversi format tanggal, pengisian nilai kosong (misalnya Engagements dengan 0), dan normalisasi nama kolom untuk konsistensi (misalnya dari "Media Type" menjadi "media_type").

Visualisasi Interaktif:

Pembuatan lima grafik interaktif yang berwarna menggunakan Plotly untuk memvisualisasikan data yang telah dibersihkan dan dirapihkan:

Pie Chart Sentimen: Menampilkan distribusi sentimen (Positif, Negatif, Netral).

Line Chart Tren Engagement: Menggambarkan perubahan tren engagement seiring waktu.

Bar Chart Engagement Platform: Membandingkan total engagement di berbagai platform.

Pie Chart Campuran Tipe Media: Menganalisis komposisi tipe media yang digunakan.

Bar Chart Top 5 Lokasi: Menyoroti lokasi paling aktif berdasarkan jumlah entri data.

Wawasan Utama per Grafik:

Setiap grafik dilengkapi dengan tiga wawasan utama yang dihasilkan secara otomatis, bertujuan untuk mempermudah pembacaan poin-poin penting dan interpretasi data bagi pengguna.

Analisis dan Rekomendasi AI:

Pengguna memiliki opsi untuk memilih model AI (Gemini Flash atau melalui OpenRouter API) untuk mendapatkan ringkasan data yang komprehensif dan 3 rekomendasi kampanye yang actionable guna mengoptimalkan strategi di masa depan.

Pengunduhan Laporan PDF:

Kemampuan untuk mengunduh laporan ringkasan dalam format PDF. Laporan ini mencakup wawasan utama dari setiap grafik dan hasil analisis serta rekomendasi yang dihasilkan oleh AI.

(Catatan: Laporan PDF saat ini berbasis teks dan belum menyertakan grafik interaktif langsung sebagai gambar).

Mode Tampilan Fleksibel:

Dashboard mendukung mode tampilan terang dan gelap yang dapat diubah melalui pengaturan bawaan Streamlit, meningkatkan kenyamanan visual bagi berbagai preferensi pengguna.

(Catatan: Antarmuka aplikasi dashboard utama saat ini dalam bahasa Inggris, dan analisis AI akan merespons dalam bahasa prompt yang diberikan).

Tech Stack
Proyek ini dibangun menggunakan teknologi dan pustaka berikut:

Framework Aplikasi Web: Streamlit

Visualisasi Data: Plotly

Model AI:

Google Gemini (via Google Generative AI API)


OpenRouter AI (untuk integrasi dengan berbagai model AI lain)

Manajemen Kode & Kolaborasi: GitHub

Platform Deployment: Streamlit Cloudflare

Link streamlit: https://tumbloo-8svbp6rzgkn5n3beciramk.streamlit.app/

Link cloudflare: https://uasmedintel.pages.dev/
