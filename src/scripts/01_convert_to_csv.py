# src/scripts/01_convert_to_csv.py

import csv
import zipfile
import openpyxl
from pathlib import Path

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOWNLOAD_DIR = PROJECT_ROOT / "data" / "download"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

def convert_excel_to_csv_low_memory(excel_source, file_stem, output_dir):
    """
    Excelファイルを低メモリ消費で読み込み、シートごとにCSVへ変換する。
    セル内の改行は '\\n' にエスケープし、全セルをダブルクォートで囲む。
    """
    try:
        workbook = openpyxl.load_workbook(excel_source, read_only=True)
        
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            output_filename = f"{file_stem}_{sheet_name}.csv"
            output_path = output_dir / output_filename
            
            print(f"  - Saving sheet: '{sheet_name}' -> '{output_path.name}'")
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                # 全てのフィールドをダブルクォーテーションで囲むように設定
                csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
                
                for row in worksheet.iter_rows(values_only=True):
                    escaped_row = []
                    for cell in row:
                        cell_str = str(cell) if cell is not None else ""
                        # 改行コードをエスケープされた文字列に置換
                        escaped_str = cell_str.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\r')
                        escaped_row.append(escaped_str)
                    
                    csv_writer.writerow(escaped_row)

    except Exception as e:
        print(f"  [Error] Failed to process {file_stem}: {e}")

def main():
    """
    downloadフォルダ内のzipとxlsxを処理し、rawフォルダにCSVを出力するメイン関数
    """
    print("--- 01_convert_to_csv.py (Force Quoting & Escape Newlines): Start ---")

    RAW_DIR.mkdir(exist_ok=True)
    print(f"Output directory: '{RAW_DIR}'")

    source_paths = list(DOWNLOAD_DIR.glob('*.zip')) + list(DOWNLOAD_DIR.glob('*.xlsx'))
    
    if not source_paths:
        print("\n[Warning] No .zip or .xlsx files found in 'data/download/' directory.")
        print("Please run this script after downloading the source data.")
        print("--- 01_convert_to_csv.py: Finished ---")
        return

    print(f"\nFound {len(source_paths)} files to process.")

    for path in source_paths:
        print(f"\nProcessing '{path.name}'...")
        
        if path.suffix == '.zip':
            try:
                with zipfile.ZipFile(path, 'r') as zf:
                    for file_in_zip in zf.namelist():
                        if file_in_zip.endswith('.xlsx'):
                            file_stem = Path(file_in_zip).stem
                            print(f"  - Found Excel file in zip: '{file_in_zip}'")
                            with zf.open(file_in_zip) as excel_stream:
                                convert_excel_to_csv_low_memory(excel_stream, file_stem, RAW_DIR)
            except Exception as e:
                print(f"  [Error] Failed to process zip file {path.name}: {e}")

        elif path.suffix == '.xlsx':
            convert_excel_to_csv_low_memory(path, path.stem, RAW_DIR)

    print("\n--- 01_convert_to_csv.py: Finished ---")

if __name__ == "__main__":
    main()