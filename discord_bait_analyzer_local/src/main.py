from pathlib import Path
import pandas as pd

from preprocessor import analyze_and_extract_from_content

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
CSV_OUTPUT = PROCESSED_DIR / 'extracted_worlds.csv'
TXT_OUTPUT = PROCESSED_DIR / 'extracted_worlds.txt'


def read_txt_files(raw_dir: Path):
    """Yield (filename, content) untuk setiap file .txt di folder raw."""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Folder input tidak ditemukan: {raw_dir}")

    txt_files = sorted(
        [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() == '.txt']
    )

    if not txt_files:
        raise FileNotFoundError(
            f"Tidak ada file .txt di folder: {raw_dir}\n"
            "Taruh file export chat Discord ke folder data/raw terlebih dahulu."
        )

    for path in txt_files:
        with path.open('r', encoding='utf-8', errors='ignore') as f:
            yield path.name, f.read()



def save_results(worlds, csv_output: Path, txt_output: Path):
    csv_output.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({'World Name': worlds})
    df.to_csv(csv_output, index=False, encoding='utf-8')

    with txt_output.open('w', encoding='utf-8') as f:
        for world in worlds:
            f.write(world + '\n')



def main():
    print('Memulai analisis file lokal dari folder data/raw ...')

    all_worlds = set()
    processed_files = 0

    for filename, content in read_txt_files(RAW_DIR):
        processed_files += 1
        print(f"\n--- Memproses: {filename} ---")

        worlds = analyze_and_extract_from_content(content)
        print(f"Ditemukan {len(worlds)} world unik di file ini.")

        all_worlds.update(worlds)

    final_worlds = sorted(all_worlds)

    if not final_worlds:
        print('\nSelesai, tetapi tidak ada world yang berhasil diekstrak.')
        return

    save_results(final_worlds, CSV_OUTPUT, TXT_OUTPUT)

    print('\n---------------------------------')
    print(f'Jumlah file diproses : {processed_files}')
    print(f'Total world unik     : {len(final_worlds)}')
    print(f'CSV output           : {CSV_OUTPUT}')
    print(f'TXT output           : {TXT_OUTPUT}')
    print('Program selesai.')
    print('---------------------------------')


if __name__ == '__main__':
    main()
