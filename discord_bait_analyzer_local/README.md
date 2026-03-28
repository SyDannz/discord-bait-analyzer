# Discord Bait Analyzer

Program untuk membaca file `.txt` hasil export chat Discord dan mengekstrak nama world yang menjual bait.

## Cara pakai

1. Taruh file `.txt` di folder:
   `data/raw/`

2. Buat virtual environment:
   ```bash
   python -m venv venv

3. Aktifkan virtual environment:
   ```bash
   venv\Scripts\activate

4. Install dependency:
   ```bash
   pip install -r requirements.txt

5. Jalankan program:
   ```bash
   cd src
   python main.py

6. Hasil ada di:
   data/processed/extracted_worlds.csv
