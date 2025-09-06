# src/scripts/02_normalize_data.py

import sys
import csv
from pathlib import Path

# このスクリプトの親のさらに親をPythonのモジュール検索パスに追加
# これにより `python -m` なしでも `src` を見つけられる
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

from src.lib.normalization import normalize_text

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"

def process_csv_file(input_path: Path, output_path: Path):
    """
    単一のCSVファイルを読み込み、全セルを正規化して別ファイルに保存する。
    出力時は全セルをダブルクォーテーションで囲む。
    """
    try:
        with open(input_path, 'r', encoding='utf-8-sig') as infile, \
             open(output_path, 'w', encoding='utf-8-sig', newline='') as outfile:
            
            reader = csv.reader(infile)
            # 全てのフィールドをダブルクォーテーションで囲むように設定
            writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            
            header = next(reader, None)
            if header:
                normalized_header = [normalize_text(cell) for cell in header]
                writer.writerow(normalized_header)
            
            processed_rows = 0
            for row in reader:
                normalized_row = [normalize_text(cell) for cell in row]
                writer.writerow(normalized_row)
                
                processed_rows += 1
                if processed_rows % 500 == 0:
                    print(f"  - Processed {processed_rows} rows...", end='\r')
            
            print(f"  - Processed {processed_rows} total rows. Done. ")

    except Exception as e:
        print(f"\n[Error] Failed to process {input_path.name}: {e}")

def main():
    """
    rawフォルダ内の全CSVを正規化し、normalizedフォルダに出力するメイン関数。
    """
    print("--- 02_normalize_data.py (Force Quoting): Start ---")

    NORMALIZED_DIR.mkdir(exist_ok=True)
    print(f"Output directory: '{NORMALIZED_DIR}'")

    csv_files = list(RAW_DIR.glob('*.csv'))
    
    if not csv_files:
        print("\n[Warning] No .csv files found in 'data/raw/' directory.")
        print("Please run '01_convert_to_csv.py' first.")
        print("--- 02_normalize_data.py: Finished ---")
        return
        
    print(f"\nFound {len(csv_files)} CSV files to normalize.")

    for input_path in csv_files:
        print(f"\nProcessing '{input_path.name}'...")
        output_path = NORMALIZED_DIR / input_path.name
        process_csv_file(input_path, output_path)

    print("\n--- 02_normalize_data.py: Finished ---")

if __name__ == "__main__":
    main()