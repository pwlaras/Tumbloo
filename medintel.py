import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import requests
from fpdf import FPDF # Menggunakan fpdf2 untuk pembuatan PDF

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Interactive Media Intelligence Dashboard",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inisialisasi State Sesi ---
# Variabel-variabel ini akan mempertahankan nilainya di seluruh interaksi pengguna
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = pd.DataFrame()
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = ""
if 'openrouter_api_key' not in st.session_state:
    st.session_state.openrouter_api_key = ""
if 'selected_openrouter_model' not in st.session_state:
    # Model default untuk OpenRouter
    st.session_state.selected_openrouter_model = "google/gemini-pro-1.5-flash" 
if 'manual_rows' not in st.session_state:
    st.session_state.manual_rows = [
        {'Date': '2023-01-01', 'Platform': 'Instagram', 'Sentiment': 'Positive', 'Location': 'Jakarta',
         'Engagements': 1500, 'Media Type': 'Image', 'Influencer Brand': 'BrandX', 'Post Type': 'Feed Post'}
    ]

# --- Fungsi Pembantu ---

def clean_data(df):
    """
    Membersihkan dan memproses DataFrame:
    - Mengkonversi 'Date' ke format datetime.
    - Mengisi 'Engagements' yang hilang dengan 0.
    - Menormalisasi nama kolom (huruf kecil, ganti spasi dengan underscore).
    - Memastikan kolom 'influencer_brand' dan 'post_type' ada.
    """
    if df.empty:
        return pd.DataFrame()

    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Mengkonversi kolom 'date'
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']) # Menghapus baris yang gagal dikonversi tanggal
    else:
        st.error("Error: Kolom 'Date' tidak ditemukan dalam data.")
        return pd.DataFrame()

    # Mengkonversi kolom 'engagements'
    if 'engagements' in df.columns:
        df['engagements'] = pd.to_numeric(df['engagements'], errors='coerce').fillna(0)
    else:
        st.warning("Peringatan: Kolom 'Engagements' tidak ditemukan. Mengatur semua engagement ke 0.")
        df['engagements'] = 0

    # Memastikan kolom-kolom lain yang diharapkan ada, isi dengan 'Unknown' jika hilang
    for col in ['platform', 'sentiment', 'location', 'media_type', 'influencer_brand', 'post_type']:
        if col not in df.columns:
            df[col] = 'Unknown'
        else:
            df[col] = df[col].fillna('Unknown') # Mengisi nilai NaN yang ada di kolom

    return df

def get_common_plotly_layout(title_text, is_dark_mode=False):
    """Mengembalikan layout Plotly umum dengan adaptasi tema."""
    text_color = "white" if is_dark_mode else "#2C3E50" # Warna teks untuk mode gelap/terang
    grid_color = "#4a5568" if is_dark_mode else "#e2e8f0" # Warna grid untuk mode gelap/terang
    
    return {
        'title': {'text': title_text, 'font': {'size': 24, 'color': text_color}},
        'paper_bgcolor': 'rgba(0,0,0,0)', # Latar belakang transparan
        'plot_bgcolor': 'rgba(0,0,0,0)', # Latar belakang transparan
        'height': 400,
        'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
        'font': {'color': text_color},
        'xaxis': {
            'gridcolor': grid_color,
            'linecolor': text_color,
            'tickfont': {'color': text_color},
            'titlefont': {'color': text_color}
        },
        'yaxis': {
            'gridcolor': grid_color,
            'linecolor': text_color,
            'tickfont': {'color': text_color},
            'titlefont': {'color': text_color}
        },
        'legend': {
            'font': {'color': text_color}
        }
    }

def get_chart_colors(is_dark_mode=False):
    """Mengembalikan daftar warna untuk grafik berdasarkan tema."""
    if is_dark_mode:
        return ['#66d9ef', '#a78bfa', '#ff66c4', '#66ff99', '#ffcc66'] # Biru muda, ungu muda, pink, hijau muda, oranye muda
    else:
        return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'] # Warna default Plotly

def display_insights_text(insights_data):
    """Menampilkan wawasan dalam bentuk daftar."""
    if insights_data:
        for insight in insights_data:
            st.markdown(f"- {insight}")
    else:
        st.markdown(f"- Tidak ada wawasan yang tersedia untuk grafik ini.")

def summarize_data_for_ai(df):
    """Meringkas data yang telah dibersihkan untuk prompt AI."""
    if df.empty:
        return "Tidak ada data yang tersedia."

    summary_data = {
        "totalEntries": len(df),
        "sentimentCounts": df['sentiment'].value_counts().to_dict(),
        "platformEngagements": df.groupby('platform')['engagements'].sum().to_dict(),
        "mediaTypeCounts": df['media_type'].value_counts().to_dict(),
        "topLocations": df['location'].value_counts().head(3).to_dict(),
    }

    # Ringkasan tren engagement
    df_sorted = df.sort_values('date')
    engagement_trend_summary = "Tidak ada tren engagement yang jelas."
    if len(df_sorted) > 1:
        first_engagement = df_sorted['engagements'].iloc[0]
        last_engagement = df_sorted['engagements'].iloc[-1]
        if last_engagement > first_engagement:
            engagement_trend_summary = "Ada tren peningkatan engagement secara keseluruhan."
        elif last_engagement < first_engagement:
            engagement_trend_summary = "Ada tren penurunan engagement secara keseluruhan."

    prompt_summary = f"""
    Total entri data: {summary_data['totalEntries']}
    Distribusi Sentimen Teratas: {summary_data['sentimentCounts']}
    Engagement Platform Teratas: {summary_data['platformEngagements']}
    Distribusi Tipe Media Teratas: {summary_data['mediaTypeCounts']}
    Lokasi Teratas: {summary_data['topLocations']}
    Ringkasan Tren Engagement: {engagement_trend_summary}
    """
    return prompt_summary

# --- Layout Dashboard Utama ---

st.title("☁️ Interactive Media Intelligence Dashboard ☁️")

st.markdown("""
Dashboard ini memungkinkan Anda menganalisis data intelijen media melalui grafik interaktif dan wawasan bertenaga AI.
""")

# --- Sidebar untuk Bantuan ---
with st.sidebar:
    st.header("Panduan Penggunaan Dashboard")
    st.markdown("""
    ### Cara Menggunakan
    1.  **Masukkan Data Manual:** Isi kolom input untuk setiap entri data di bawah "Manual Data Entry". Klik "Add New Row" untuk entri tambahan. Klik "Process Manual Data & Generate Charts" untuk menggunakan data ini.
    2.  **Unggah File CSV:** Atau, unggah file CSV di bawah "Upload CSV File". Sistem akan secara otomatis memprosesnya dan menghasilkan grafik.
    3.  **Pembersihan Data Otomatis:** Data yang Anda masukkan/unggah akan secara otomatis dibersihkan (konversi tanggal, mengisi nilai yang hilang, menormalisasi nama kolom).
    4.  **Lihat Grafik Interaktif:** Setelah data bersih, lima grafik akan muncul. Anda dapat mengarahkan kursor ke elemen grafik untuk melihat detailnya.
    5.  **Hasilkan Analisis AI:** Klik salah satu tombol "Generate AI Analysis" untuk mendapatkan ringkasan dan rekomendasi dari model AI berdasarkan data yang diproses. Untuk OpenRouter AI, pastikan Anda telah memasukkan API Key dan memilih model.
    6.  **Unduh Laporan:** Gunakan tombol "Download Report as PDF" untuk menyimpan seluruh dashboard sebagai dokumen PDF (laporan berbasis teks).
    7.  **Toggle Mode:** Gunakan ikon bulan/matahari di kanan atas aplikasi Streamlit untuk beralih antara mode terang dan gelap (tema asli Streamlit).
    """)

    st.header("Penjelasan Kolom CSV")
    st.markdown("""
    -   **Date:** Tanggal data dikumpulkan (format YYYY-MM-DD disarankan).
    -   **Platform:** Media sosial atau platform lain (misal: Instagram, Twitter, Blog).
    -   **Sentiment:** Sentimen yang terkait dengan data (misal: Positif, Negatif, Netral).
    -   **Location:** Lokasi di mana data berasal atau relevan.
    -   **Engagements:** Jumlah interaksi (suka, komentar, bagikan, dll.).
    -   **Media Type:** Jenis media (misal: Gambar, Video, Teks).
    -   **Influencer Brand:** Nama brand influencer (jika berlaku).
    -   **Post Type:** Tipe postingan (misal: Story, Feed Post, Reel).
    """)

    st.header("FAQ (Pertanyaan yang Sering Diajukan)")
    st.markdown("""
    -   **Q: Mengapa grafik tidak muncul setelah memproses data?**
        -   A: Pastikan semua kolom yang diperlukan diisi dengan benar (untuk input manual) atau format CSV Anda benar (untuk unggahan CSV). Periksa konsol Streamlit untuk kesalahan.
    -   **Q: Bisakah saya mengunduh grafik secara langsung?**
        -   A: Grafik Plotly Streamlit memungkinkan pengunduhan langsung sebagai PNG/SVG dari modebar grafik.
    -   **Q: Apakah data saya disimpan?**
        -   A: Tidak, data Anda hanya diproses di browser/sesi Streamlit Anda dan tidak disimpan di server mana pun.
    -   **Q: Bagaimana cara menggunakan OpenRouter AI?**
        -   A: Anda perlu memasukkan API Key OpenRouter Anda di kolom yang tersedia dan memilih model AI dari dropdown.
    """)

# --- Bagian Input Data ---
st.header("1. Masukkan Data Anda")
st.write("Pilih bagaimana Anda ingin memasukkan data Anda: secara manual atau dengan mengunggah file CSV.")

data_input_method = st.radio(
    "Pilih metode input data:",
    ("Input Data Manual", "Unggah File CSV"),
    key="data_input_method_radio"
)

# Kontainer untuk pesan kesalahan input data manual atau CSV
data_status_container = st.empty()

if data_input_method == "Input Data Manual":
    st.subheader("Input Data Manual")
    
    # Editor data Streamlit untuk input manual
    edited_df = st.data_editor(
        pd.DataFrame(st.session_state.manual_rows),
        num_rows="dynamic", # Memungkinkan penambahan/penghapusan baris
        use_container_width=True,
        key="data_editor_manual_input" # Key unik
    )

    if st.button("Proses Data Manual & Hasilkan Grafik", key="process_manual_button"):
        if not edited_df.empty:
            st.session_state.cleaned_data = clean_data(edited_df.copy())
            if st.session_state.cleaned_data.empty:
                data_status_container.error("Tidak ada data valid yang ditemukan setelah pembersihan. Harap periksa entri manual Anda.")
                st.session_state.ai_recommendations = "" # Bersihkan rekomendasi AI
            else:
                data_status_container.success("Data manual berhasil diproses! Grafik dan analisis AI siap.")
                st.session_state.ai_recommendations = "" # Bersihkan rekomendasi AI lama jika ada
        else:
            data_status_container.error("Harap tambahkan baris data di tabel sebelum memproses.")

elif data_input_method == "Unggah File CSV":
    st.subheader("Unggah File CSV")
    uploaded_file = st.file_uploader(
        "Unggah file CSV dengan kolom: Date, Platform, Sentiment, Location, Engagements, Media Type, Influencer Brand, Post Type",
        type=["csv"],
        key="csv_uploader" # Key unik
    )

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.session_state.cleaned_data = clean_data(df_uploaded.copy())
            if st.session_state.cleaned_data.empty:
                data_status_container.error("Tidak ada data valid yang ditemukan dalam CSV setelah pembersihan. Harap periksa format dan konten file CSV Anda.")
                st.session_state.ai_recommendations = "" # Bersihkan rekomendasi AI
            else:
                data_status_container.success("File CSV berhasil diproses! Grafik dan analisis AI siap.")
                st.write("5 baris pertama data yang diproses:")
                st.dataframe(st.session_state.cleaned_data.head())
                st.session_state.ai_recommendations = "" # Bersihkan rekomendasi AI lama jika ada
        except Exception as e:
            data_status_container.error(f"Error membaca file CSV: {e}")
            st.session_state.cleaned_data = pd.DataFrame() # Bersihkan data saat terjadi kesalahan
            st.session_state.ai_recommendations = "" # Bersihkan rekomendasi AI

# --- Status Pembersihan Data ---
if not st.session_state.cleaned_data.empty:
    st.header("2. Pembersihan Data")
    st.info("Pembersihan data selesai. Melanjutkan untuk menghasilkan grafik.")


# --- Bagian Grafik ---
if not st.session_state.cleaned_data.empty:
    st.header("3. Grafik & Wawasan Interaktif")
    df = st.session_state.cleaned_data
    
    # Mendapatkan tema Streamlit saat ini
    # Gunakan st.query_params untuk mendeteksi tema jika theme.base tidak langsung berubah untuk beberapa elemen
    current_theme_query = st.query_params.get("theme")
    is_dark_mode = (st.get_option("theme.base") == "dark") or (current_theme_query == "dark")

    chart_colors = get_chart_colors(is_dark_mode)

    # Grafik 1: Distribusi Sentimen (Pie Chart)
    st.subheader("Distribusi Sentimen")
    sentiment_counts = df['sentiment'].value_counts()
    fig_sentiment = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        hole=0.4,
        marker_colors=px.colors.sequential.Bluyl if is_dark_mode else px.colors.sequential.Blues,
        hoverinfo='label+percent+value',
        textinfo='percent',
        textposition='inside'
    )])
    fig_sentiment.update_layout(get_common_plotly_layout("Distribusi Sentimen", is_dark_mode))
    st.plotly_chart(fig_sentiment, use_container_width=True)
    display_insights_text([
        f"Sentimen '{sentiment_counts.index[0]}' paling dominan, menyumbang {sentiment_counts.iloc[0]/sentiment_counts.sum():.1%} dari total." if len(sentiment_counts) > 0 else "Tidak ada data sentimen.",
        f"Sentimen kedua yang paling umum adalah '{sentiment_counts.index[1]}'." if len(sentiment_counts) > 1 else "",
        f"Terdapat perbedaan mencolok antara dua sentimen teratas dengan '{sentiment_counts.index[2]}'." if len(sentiment_counts) > 2 else ""
    ])


    # Grafik 2: Tren Engagement Seiring Waktu (Line Chart)
    st.subheader("Tren Engagement Seiring Waktu")
    daily_engagements = df.groupby(df['date'].dt.date)['engagements'].sum().reset_index()
    daily_engagements['date'] = pd.to_datetime(daily_engagements['date']) # Konversi kembali ke datetime untuk plotly
    fig_engagement_trend = px.line(
        daily_engagements,
        x='date',
        y='engagements',
        markers=True,
        color_discrete_sequence=[chart_colors[0]]
    )
    fig_engagement_trend.update_layout(get_common_plotly_layout("Tren Engagement Seiring Waktu", is_dark_mode))
    st.plotly_chart(fig_engagement_trend, use_container_width=True)
    
    engagement_insights = []
    if len(daily_engagements) > 1:
        first_engagement = daily_engagements['engagements'].iloc[0]
        last_engagement = daily_engagements['engagements'].iloc[-1]
        if last_engagement > first_engagement:
            engagement_insights.append("Secara keseluruhan, terlihat tren peningkatan engagement seiring waktu.")
        elif last_engagement < first_engagement:
            engagement_insights.append("Secara keseluruhan, terlihat tren penurunan engagement seiring waktu.")
        else:
            engagement_insights.append("Engagement cenderung stabil selama periode yang diamati.")

        peak_day_row = daily_engagements.loc[daily_engagements['engagements'].idxmax()]
        engagement_insights.append(f"Engagement tertinggi tercatat pada tanggal {peak_day_row['date'].strftime('%Y-%m-%d')} dengan {int(peak_day_row['engagements'])} engagement.")

        lowest_day_row = daily_engagements.loc[daily_engagements['engagements'].idxmin()]
        engagement_insights.append(f"Engagement terendah diamati pada tanggal {lowest_day_row['date'].strftime('%Y-%m-%d')} dengan {int(lowest_day_row['engagements'])} engagement.")
    else:
        engagement_insights.append("Tidak cukup data untuk menentukan tren engagement.")
    display_insights_text(engagement_insights)


    # Grafik 3: Engagement Berdasarkan Platform (Bar Chart)
    st.subheader("Engagement Berdasarkan Platform")
    platform_engagements = df.groupby('platform')['engagements'].sum().sort_values(ascending=False).reset_index()
    platform_engagements.columns = ['platform', 'engagements'] # Memastikan nama kolom
    fig_platform = px.bar(
        platform_engagements,
        x='platform',
        y='engagements',
        color_discrete_sequence=[chart_colors[1]]
    )
    fig_platform.update_layout(get_common_plotly_layout("Total Engagement per Platform", is_dark_mode))
    st.plotly_chart(fig_platform, use_container_width=True)
    display_insights_text([
        f"'{platform_engagements['platform'].iloc[0]}' adalah platform dengan kinerja terbaik dalam hal total engagement, menunjukkan jangkauan yang kuat." if len(platform_engagements) > 0 else "Tidak ada data platform.",
        f"'{platform_engagements['platform'].iloc[1]}' menyusul sebagai platform dengan engagement tertinggi kedua." if len(platform_engagements) > 1 else "",
        f"Terdapat penurunan engagement yang signifikan setelah dua platform teratas, dengan '{platform_engagements['platform'].iloc[2]}' tertinggal di belakang." if len(platform_engagements) > 2 else ""
    ])


    # Grafik 4: Campuran Tipe Media (Pie Chart)
    st.subheader("Campuran Tipe Media")
    media_type_counts = df['media_type'].value_counts()
    fig_media_type = go.Figure(data=[go.Pie(
        labels=media_type_counts.index,
        values=media_type_counts.values,
        hole=0.4,
        marker_colors=px.colors.sequential.Aggrnyl if is_dark_mode else px.colors.sequential.Greens,
        hoverinfo='label+percent+value',
        textinfo='percent',
        textposition='inside'
    )])
    fig_media_type.update_layout(get_common_plotly_layout("Campuran Tipe Media", is_dark_mode))
    st.plotly_chart(fig_media_type, use_container_width=True)
    display_insights_text([
        f"Tipe media yang paling sering digunakan adalah '{media_type_counts.index[0]}', menunjukkan bahwa itu adalah format konten utama." if len(media_type_counts) > 0 else "Tidak ada data tipe media.",
        f"'{media_type_counts.index[1]}' mewakili pangsa media terbesar kedua." if len(media_type_counts) > 1 else "",
        f"Terdapat campuran tipe media yang beragam, namun '{media_type_counts.index[2]}' menunjukkan kontribusi yang moderat." if len(media_type_counts) > 2 else ""
    ])


    # Grafik 5: Top 5 Lokasi (Bar Chart)
    st.subheader("Top 5 Lokasi")
    location_counts = df['location'].value_counts().head(5).reset_index()
    location_counts.columns = ['location', 'count'] # Mengubah nama kolom untuk kejelasan
    fig_locations = px.bar(
        location_counts,
        x='location',
        y='count',
        color_discrete_sequence=[chart_colors[2]]
    )
    fig_locations.update_layout(get_common_plotly_layout("Top 5 Lokasi berdasarkan Jumlah Aktivitas", is_dark_mode))
    st.plotly_chart(fig_locations, use_container_width=True)
    display_insights_text([
        f"'{location_counts['location'].iloc[0]}' adalah lokasi paling aktif, menunjukkan konsentrasi tinggi aktivitas intelijen media di sini." if len(location_counts) > 0 else "Tidak ada data lokasi.",
        f"'{location_counts['location'].iloc[1]}' menempati peringkat kedua, menunjukkan area geografis kunci lain untuk aktivitas media." if len(location_counts) > 1 else "",
        f"Tiga lokasi teratas, termasuk '{location_counts['location'].iloc[2]}', secara kolektif mewakili porsi signifikan dari total aktivitas yang tercatat." if len(location_counts) > 2 else ""
    ])


# --- Bagian Analisis & Rekomendasi AI ---
if not st.session_state.cleaned_data.empty:
    st.header("4. Analisis & Rekomendasi AI")
    st.write("Pilih model AI untuk mendapatkan ringkasan strategis dan rekomendasi berdasarkan data Anda.")

    # Konfigurasi OpenRouter AI
    st.subheader("Konfigurasi OpenRouter AI")
    openrouter_api_key = st.text_input(
        "OpenRouter API Key:",
        type="password",
        value=st.session_state.openrouter_api_key,
        key="openrouter_api_key_input_ai"
    )
    st.session_state.openrouter_api_key = openrouter_api_key # Perbarui state sesi

    openrouter_models = {
        "Gemini 1.5 Flash (Google)": "google/gemini-pro-1.5-flash",
        "GPT-4o (OpenAI)": "openai/gpt-4o",
        "Claude 3 Sonnet (Anthropic)": "anthropic/claude-3-sonnet",
        "Mistral 7B Instruct (MistralAI)": "mistralai/mistral-7b-instruct",
        "Mixtral 8x7B Instruct (MistralAI)": "mistralai/mixtral-8x7b-instruct",
        "Nous Hermes 2 Mixtral (NousResearch)": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
        "Llama 3 8B Instruct (Meta)": "meta-llama/llama-3-8b-instruct",
        "Llama 3 70B Instruct (Meta)": "meta-llama/llama-3-70b-instruct",
        "OpenRouter Auto (Default)": "openrouter/auto"
    }
    selected_openrouter_model_name = st.selectbox(
        "Pilih Model AI:",
        options=list(openrouter_models.keys()),
        index=list(openrouter_models.keys()).index(st.session_state.selected_openrouter_model) if st.session_state.selected_openrouter_model in openrouter_models.values() else 0,
        key="openrouter_model_select_ai"
    )
    st.session_state.selected_openrouter_model = openrouter_models[selected_openrouter_model_name] # Perbarui state sesi

    col_gemini_btn, col_openrouter_btn = st.columns(2)

    with col_gemini_btn:
        gemini_button = st.button(
            "Hasilkan Analisis AI (Gemini Flash)",
            key="gemini_analysis_button_ai",
            disabled=st.session_state.cleaned_data.empty # Nonaktifkan jika tidak ada data
        )
    with col_openrouter_btn:
        openrouter_button = st.button(
            "Hasilkan Analisis AI (OpenRouter)",
            key="openrouter_analysis_button_ai",
            disabled=st.session_state.cleaned_data.empty or not st.session_state.openrouter_api_key # Nonaktifkan jika tidak ada data atau API key tidak ada
        )

    if gemini_button:
        try:
            with st.spinner("Menghasilkan wawasan dengan Gemini Flash..."):
                prompt_summary_data = summarize_data_for_ai(df)
                
                # Mengumpulkan semua wawasan grafik yang sudah ditampilkan
                all_chart_insights = []
                # Ini adalah contoh cara mengumpulkan wawasan. Dalam aplikasi nyata,
                # Anda akan menyimpan wawasan ini di session_state setelah grafik dibuat.
                # Untuk demo, ini akan mengambil wawasan sederhana.
                if not df['sentiment'].empty and len(df['sentiment'].value_counts()) >= 1:
                    all_chart_insights.append(f"Analisis sentimen menunjukkan bahwa '{df['sentiment'].value_counts().index[0]}' dominan.")
                if not df.empty and len(df.groupby('platform')['engagements'].sum()) >= 1:
                    all_chart_insights.append(f"Platform '{df.groupby('platform')['engagements'].sum().idxmax()}' memiliki engagement tertinggi.")
                if not df['media_type'].empty and len(df['media_type'].value_counts()) >= 1:
                    all_chart_insights.append(f"Tipe media '{df['media_type'].value_counts().index[0]}' paling sering.")
                if not df['location'].empty and len(df['location'].value_counts()) >= 1:
                    all_chart_insights.append(f"Lokasi '{df['location'].value_counts().index[0]}' paling aktif.")
                
                final_prompt = f"""
                Berdasarkan ringkasan data intelijen media berikut:
                {prompt_summary_data}

                Wawasan utama dari grafik:
                - {'; '.join(all_chart_insights) if all_chart_insights else "Tidak ada wawasan spesifik dari grafik."}

                Berikan ringkasan singkat data dari 5 grafik di atas (maksimal 2 paragraf) dan kemudian berikan 3 rekomendasi kampanye yang dapat ditindaklanjuti untuk mengoptimalkan strategi di masa depan.
                """
                
                try:
                    # Mengakses GOOGLE_API_KEY dari Streamlit Secrets
                    gemini_api_key = st.secrets["GOOGLE_API_KEY"]
                    genai.configure(api_key=gemini_api_key)
                except KeyError:
                    st.error("GOOGLE_API_KEY tidak ditemukan di st.secrets. Harap konfigurasikan.")
                    st.stop()
                    
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(final_prompt)
                st.session_state.ai_recommendations = response.text
        except Exception as e:
            st.error(f"Error menghasilkan rekomendasi AI Gemini: {e}")
            st.session_state.ai_recommendations = ""

    if openrouter_button:
        if not st.session_state.openrouter_api_key:
            st.error("Harap masukkan OpenRouter API Key Anda di bagian konfigurasi.")
            st.session_state.ai_recommendations = ""
        else:
            try:
                with st.spinner(f"Menghasilkan wawasan dengan OpenRouter ({st.session_state.selected_openrouter_model})..."):
                    prompt_summary_data = summarize_data_for_ai(df)
                    
                    # Mengumpulkan semua wawasan grafik yang sudah ditampilkan
                    all_chart_insights = []
                    # Sama seperti Gemini, Anda akan menarik wawasan aktual jika disimpan atau dihasilkan sebelumnya
                    if not df['sentiment'].empty and len(df['sentiment'].value_counts()) >= 1:
                        all_chart_insights.append(f"Analisis sentimen menunjukkan bahwa '{df['sentiment'].value_counts().index[0]}' dominan.")
                    if not df.empty and len(df.groupby('platform')['engagements'].sum()) >= 1:
                        all_chart_insights.append(f"Platform '{df.groupby('platform')['engagements'].sum().idxmax()}' memiliki engagement tertinggi.")
                    if not df['media_type'].empty and len(df['media_type'].value_counts()) >= 1:
                        all_chart_insights.append(f"Tipe media '{df['media_type'].value_counts().index[0]}' paling sering.")
                    if not df['location'].empty and len(df['location'].value_counts()) >= 1:
                        all_chart_insights.append(f"Lokasi '{df['location'].value_counts().index[0]}' paling aktif.")
                    
                    final_prompt = f"""
                    Berdasarkan ringkasan data intelijen media berikut:
                    {prompt_summary_data}

                    Wawasan utama dari grafik:
                    - {'; '.join(all_chart_insights) if all_chart_insights else "Tidak ada wawasan spesifik dari grafik."}

                    Berikan ringkasan singkat data dari 5 grafik di atas (maksimal 2 paragraf) dan kemudian berikan 3 rekomendasi kampanye yang dapat ditindaklanjutkan untuk mengoptimalkan strategi di masa depan.
                    """

                    headers = {
                        "Authorization": f"Bearer {st.session_state.openrouter_api_key}",
                        "Content-Type": "application/json",
                        # 'HTTP-Referer': 'https://your-streamlit-app.streamlit.app', # Opsional: ganti dengan URL aplikasi Anda untuk peringkat OpenRouter
                        # 'X-Title': 'Media Dashboard Streamlit' # Opsional: ganti dengan judul aplikasi Anda
                    }
                    payload = {
                        "model": st.session_state.selected_openrouter_model,
                        "messages": [{"role": "user", "content": final_prompt}]
                    }
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                    response.raise_for_status() # Menimbulkan pengecualian untuk kesalahan HTTP
                    result = response.json()
                    st.session_state.ai_recommendations = result["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                st.error(f"Error koneksi ke OpenRouter: {e}")
                st.session_state.ai_recommendations = ""
            except Exception as e:
                st.error(f"Error menghasilkan rekomendasi AI OpenRouter: {e}")
                st.session_state.ai_recommendations = ""

    if st.session_state.ai_recommendations:
        st.subheader("Ringkasan dan Rekomendasi yang Dihasilkan AI")
        st.write(st.session_state.ai_recommendations)


# --- Bagian Unduh Laporan ---
if not st.session_state.cleaned_data.empty:
    st.header("5. Unduh Laporan")
    
    # Aktifkan tombol unduh hanya jika analisis AI juga ada
    download_pdf_disabled = not bool(st.session_state.ai_recommendations)

    if st.button("Unduh Laporan sebagai PDF", disabled=download_pdf_disabled, key="download_pdf_button_streamlit"):
        # Buat laporan PDF dasar
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Laporan Intelijen Media", ln=True, align="C")
        pdf.ln(10)

        # Tambahkan Rekomendasi AI
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, txt="Ringkasan dan Rekomendasi yang Dihasilkan AI:")
        pdf.set_font("Arial", size=10)
        # Handle karakter non-latin1 dengan encode/decode
        pdf.multi_cell(0, 5, st.session_state.ai_recommendations.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(10)

        # Tambahkan ringkasan data (dari wawasan saat ini)
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, txt="Wawasan Utama dari Grafik:")
        pdf.set_font("Arial", size=10)
        
        # Mengumpulkan kembali wawasan untuk PDF
        all_chart_insights_for_pdf = []
        sentiment_counts_pdf = df['sentiment'].value_counts()
        if len(sentiment_counts_pdf) > 0:
            all_chart_insights_for_pdf.append(f"- Sentimen '{sentiment_counts_pdf.index[0]}' paling dominan.")
        
        daily_engagements_pdf = df.groupby(df['date'].dt.date)['engagements'].sum().reset_index()
        if len(daily_engagements_pdf) > 1:
            first_engagement_pdf = daily_engagements_pdf['engagements'].iloc[0]
            last_engagement_pdf = daily_engagements_pdf['engagements'].iloc[-1]
            if last_engagement_pdf > first_engagement_pdf:
                all_chart_insights_for_pdf.append("- Secara keseluruhan, terlihat tren peningkatan engagement.")
            else:
                all_chart_insights_for_pdf.append("- Tren engagement relatif stabil atau menurun.")

        platform_engagements_pdf = df.groupby('platform')['engagements'].sum().sort_values(ascending=False).reset_index()
        if not platform_engagements_pdf.empty:
            all_chart_insights_for_pdf.append(f"- Platform '{platform_engagements_pdf['platform'].iloc[0]}' adalah platform dengan kinerja terbaik.")

        media_type_counts_pdf = df['media_type'].value_counts()
        if not media_type_counts_pdf.empty:
            all_chart_insights_for_pdf.append(f"- Tipe media yang paling sering digunakan adalah '{media_type_counts_pdf.index[0]}'.")

        location_counts_pdf = df['location'].value_counts().head(5).reset_index()
        if not location_counts_pdf.empty:
            all_chart_insights_for_pdf.append(f"- Lokasi paling aktif adalah '{location_counts_pdf['location'].iloc[0]}'.")

        for insight in all_chart_insights_for_pdf:
            pdf.multi_cell(0, 5, insight.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(10)

        # Footer
        pdf.set_font("Arial", size=8)
        pdf.cell(200, 10, txt="Powered by Gemini AI", ln=True, align="C")
        pdf.cell(200, 5, txt="© Copyright Media Intelligence Vokasi UI @LARASDTH", ln=True, align="C")

        # Menyediakan PDF untuk diunduh
        st.download_button(
            label="Klik untuk mengunduh PDF",
            data=pdf.output(dest='S').encode('latin1'),
            file_name="Laporan_Intelijen_Media.pdf",
            mime="application/pdf",
            key="download_pdf_button_final_streamlit"
        )
        st.success("Laporan PDF berhasil dibuat dan siap diunduh!")

# --- Branding Footer (Streamlit apps typically don't have a direct HTML footer, so placed at the bottom) ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Powered by Gemini AI</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'>&copy; Copyright Media Intelligence Vokasi UI @LARASDTH</p>", unsafe_allow_html=True)
