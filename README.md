# Analisis Data Kriminalitas Los Angeles

Repositori ini berisi analisis data komprehensif tentang data kriminalitas di Los Angeles. Proyek ini mencakup seluruh alur kerja ilmu data, mulai dari pembersihan data mentah dan *exploratory data analysis (EDA)* hingga analisis statistik deskriptif dan visualisasi *insight* utama.

Tujuan utama dari proyek ini adalah untuk mengidentifikasi pola, tren, dan *hotspot* kejahatan berdasarkan lokasi (Area) dan waktu (Jam Kejadian), memberikan pemahaman yang lebih baik tentang dinamika kriminalitas di kota Los Angeles.

## 📂 Struktur Repositori

Proyek ini dibagi menjadi dua *notebook* Jupyter utama:

1. **`00_prototype.ipynb`**:

   * Fokus pada *data acquisition*, *exploratory data analysis (EDA)* awal, dan *preprocessing* data.
   * Menangani nilai-nilai anomali (seperti `vict_age` = 120).
   * Analisis frekuensi untuk kategori langka (kurang dari 1%).
   * Eksplorasi data geospasial menggunakan `geopandas` dan `shapely`.

2. **`01_final.ipynb`**:

   * Memuat data yang sudah bersih (`Crime_Data_Clean.csv`).
   * Melakukan analisis **Statistika Deskriptif** mendalam.
   * Membuat visualisasi akhir, termasuk *heatmap* untuk mengidentifikasi *hotspot* dan waktu rawan kejahatan di 10 area teratas.

## 🛠️ Metodologi

Alur kerja analisis yang digunakan dalam proyek ini adalah sebagai berikut:

1. **Data Acquisition**: Mengimpor *library* yang diperlukan dan memuat data.
2. **Data Cleaning**: Membersihkan data, menangani nilai *null*, duplikat, dan *outlier* (anomali) untuk memastikan kualitas data.
3. **Exploratory Data Analysis (EDA)**: Menganalisis distribusi variabel, frekuensi, dan korelasi awal. Ini termasuk analisis geospasial untuk memahami sebaran kejahatan.
4. **Analisis Statistik & Visualisasi**: Menerapkan statistika deskriptif untuk merangkum data dan membuat visualisasi (seperti *heatmap* dan plot lainnya) untuk menyajikan temuan secara efektif.

## 📊 Hasil Utama: Hotspot & Waktu Rawan

Salah satu temuan kunci dari analisis ini adalah identifikasi *hotspot* kejahatan dan jam-jam paling rawan. Ini divisualisasikan menggunakan *heatmap* yang memetakan jumlah kejahatan berdasarkan "Nama Area" dan "Jam Kejadian".

Visualisasi ini (ditemukan di `01_final.ipynb`) menyoroti:

* **Area Paling Rawan**: Area mana (dari 10 teratas) yang memiliki volume kejahatan tertinggi.
* **Jam Sibuk Kejahatan**: Jam-jam spesifik (dari 0-23) di mana kejahatan paling sering terjadi di area-area tersebut.

## 🔗 Sumber Data

Berikut adalah sumber data yang digunakan dalam proyek ini:

1. **Data Kriminalitas**:
   Data utama diambil dari portal data terbuka Kota Los Angeles:

   * [Crime Data from 2020 to Present](https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8/about_data)

2. **Data Distrik**:
   Data distrik Los Angeles yang digunakan untuk pemetaan geospasial dapat ditemukan di:

   * [Los Angeles Districts Map](https://geohub.lacity.org/datasets/76104f230e384f38871eb3c4782f903d_13/about)

3. **Data Petugas Kepolisian**:
   Data petugas yang terlibat dalam penanganan kriminalitas dapat diakses di:

   * [Watch the Watchers: Police Officer Rosters](https://watchthewatchers.net/rosters)

4. **Data Populasi**:
   Data demografis Los Angeles menurut distrik dapat ditemukan di:

   * [Census Data by Council District](https://catalog.data.gov/dataset/census-data-by-council-district?)

## 🚀 Instalasi & Penggunaan

Untuk menjalankan proyek ini secara lokal, ikuti langkah-langkah berikut:

1. **Clone repositori ini**:

   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. **(Opsional) Buat dan aktifkan *virtual environment***:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk macOS/Linux
   .\venv\Scripts\activate   # Untuk Windows
   ```

3. **Instal dependensi yang diperlukan**:
   Buat file `requirements.txt` dengan isi di bawah ini, lalu jalankan `pip install -r requirements.txt`.

   ```txt
   pandas
   numpy
   matplotlib
   seaborn
   scipy
   geopandas
   shapely
   dash
   dash-bootstrap-components
   plotly
   ```

4. **Jalankan Notebook**

   Buka file `00_prototype.ipynb` atau `01_final.ipynb` untuk melihat analisis.

## 👥 Acknowledgments

Proyek ini tidak akan selesai tanpa kontribusi dari berbagai individu yang berperan penting dalam berbagai tahap analisis. Terima kasih kepada tim yang luar biasa yang telah berkolaborasi dengan semangat tinggi, yaitu:

1. **Data Wrangler** (Erlina): Bertanggung jawab atas pengumpulan, pembersihan, dan transformasi data untuk memastikan kualitas dan konsistensi dataset.
2. **Statistical Analyst** (Johanes): Menganalisis data dengan teknik statistik dan menerapkan metode untuk merangkum hasil dan menarik kesimpulan yang valid.
3. **Visualization Engineer** (Baihaqi): Membuat visualisasi yang efektif dan informatif, seperti heatmap dan diagram lainnya, untuk membantu memahami tren dan pola yang ada.
4. **Storyteller** (Desi): Mengembangkan narasi yang kuat untuk menyampaikan temuan proyek ini dengan cara yang jelas dan mudah dipahami oleh audiens.
5. **Data Lead**: Memimpin proyek ini, memastikan bahwa semua bagian proyek berjalan dengan baik, dari perencanaan hingga eksekusi akhir.

Terima kasih juga kepada sumber-sumber data yang telah disediakan dan memungkinkan analisis ini untuk dilakukan.

