import sys
import pandas as pd
import re
from pathlib import Path

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

# --- ★★★ config.pyから府省庁マスター定義をインポート ★★★ ---
from src.config import MINISTRY_NAME_VARIATIONS, MINISTRY_MASTER_DATA

# --- 定数と設定 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
TARGET_BUSINESS_NAME = "高度情報通信ネットワーク社会推進経費"

FILENAME_YEAR_MAP = {
    'database240918': 2023, 'database240502': 2022, 'database220524': 2021,
    'database_220427': 2020, 'database2019_220427': 2019, 'database2018_220427': 2018,
    'database2017': 2017, 'database2016': 2016, 'database2015': 2015,
    'database2014': 2014,
}

# --- ★★★ 事前に府省庁名とIDの対応辞書を作成 ★★★ ---
MINISTRY_DF = pd.DataFrame(MINISTRY_MASTER_DATA)
MINISTRY_NAME_TO_ID = pd.Series(MINISTRY_DF.ministry_id.values, index=MINISTRY_DF.ministry_name).to_dict()

# --- データ変換ロジック ---

def get_year_from_filename(filename):
    for key, year in FILENAME_YEAR_MAP.items():
        if key in filename: return year
    return None

def generate_business_id(row, file_year, ministry_id):
    """府省庁IDを使って代理キーを生成する"""
    ministry_code = str(ministry_id).zfill(4) if pd.notna(ministry_id) else "XXXX"

    if file_year == 2014:
        num = str(row.get('事業番号', '')).zfill(4)
        return f"{file_year}-{ministry_code}-{num}-0000"
    elif 2015 <= file_year <= 2020:
        num = str(row.get('事業番号-2', '')).zfill(4)
        branch = str(row.get('事業番号-3', '')).zfill(4) if pd.notna(row.get('事業番号-3')) else "0000"
        return f"{file_year}-{ministry_code}-{num}-{branch}"
    elif file_year >= 2021:
        year = str(int(row.get('事業番号-1', file_year)))
        code = f"{str(row.get('事業番号-2', '')).zfill(2)}{str(row.get('事業番号-3', '')).zfill(2)}"
        num = str(row.get('事業番号-4', '')).zfill(4)
        branch = str(row.get('事業番号-5', '')).zfill(4) if pd.notna(row.get('事業番号-5')) else "0000"
        # 第2期の府省庁コードは事業番号-2,3に由来するが、ここでは仮にマスターIDを使う
        return f"{year}-{ministry_code}-{num}-{branch}"
    return None

# (process_budget_columns と process_expense_columns は変更なし)
def process_budget_columns(row, business_id):
    records = []
    pattern = re.compile(r'予算額.*-(\d{2,4})年度.*(?:予算の状況|状況|)?-?(.*)')
    for col, value in row.items():
        if pd.isna(value) or not str(col).startswith('予算額'): continue
        match = pattern.search(str(col))
        if match:
            year_str, item = match.groups()
            year = int(year_str) if len(year_str) == 4 else (1988 + int(year_str))
            records.append({'business_id': business_id, '年度': year, '予算項目': item.replace('要求', ''), '金額': value})
    return records

def process_expense_columns(row, business_id):
    records = []
    base_col_name = "費目・使途(「資金の流れ」においてブロックごとに最大の金額が支出されている者について記載する。費目と使途の双方で実情が分かるように記載)-"
    for block in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        for i in range(10): 
            suffix = f'.{i}' if i > 0 else ''
            himoku_col = f'{base_col_name}{block}.支払先費目{suffix}'
            if himoku_col in row and pd.notna(row[himoku_col]):
                shito_col = himoku_col.replace('費目', '使途')
                kingaku_col = himoku_col.replace('費目', '金額(百万円)')
                records.append({'business_id': business_id, '支払ブロックID': block, '明細連番': i + 1, '費目': row.get(himoku_col), '使途': row.get(shito_col), '金額': row.get(kingaku_col)})
            elif i == 0 and himoku_col not in row: break
    return records

def main():
    print(f"--- Exhibition Tracker for: '{TARGET_BUSINESS_NAME}' ---")
    master_records, budget_records, expense_records = [], [], []
    
    files_to_process = sorted([p for p in NORMALIZED_DIR.glob('*.csv') if 'セグメント' not in p.name])

    for filepath in files_to_process:
        file_year = get_year_from_filename(filepath.name)
        if not file_year: continue

        print(f"\n[Processing {file_year}] Reading '{filepath.name}'...")
        df = pd.read_csv(filepath, low_memory=False)
        
        if '事業名' not in df.columns:
            print("  -> '事業名' column not found. Skipping.")
            continue
            
        target_rows = df[df['事業名'] == TARGET_BUSINESS_NAME]
        
        if target_rows.empty:
            print("  -> Target business not found in this file.")
            continue
            
        target_row = target_rows.iloc[0].copy()
        print(f"  -> Found target business.")
        
        # --- ★★★ 府省庁IDの確定ロジック ★★★ ---
        ministry_col_name = '府省' if '府省' in target_row else '府省庁'
        ministry_name = target_row.get(ministry_col_name)
        # 揺れを吸収
        normalized_ministry_name = MINISTRY_NAME_VARIATIONS.get(ministry_name, ministry_name)
        # マスターからIDを検索
        ministry_id = MINISTRY_NAME_TO_ID.get(normalized_ministry_name)
        
        business_id = generate_business_id(target_row, file_year, ministry_id)
        
        master_records.append({
            'business_id': business_id, 'file_year': file_year,
            '事業名': target_row.get('事業名'), 'ministry_id': ministry_id,
        })
        
        budget_records.extend(process_budget_columns(target_row, business_id))
        expense_records.extend(process_expense_columns(target_row, business_id))

    print("\n\n--- Conversion Results ---")
    if not master_records:
        print("Target business could not be tracked in any file.")
        return

    master_df = pd.DataFrame(master_records)
    budget_df = pd.DataFrame(budget_records)
    expense_df = pd.DataFrame(expense_records)

    print("\n1. 事業マスタ (business_master)")
    print("="*60)
    print(master_df.to_string())
    # (以下、表示部分は変更なし)
    print("\n\n2. 予算執行 (budget_execution) - Sample")
    print("="*60)
    print(budget_df.head(10).to_string())
    print("\n\n3. 費目使途 (expense_details) - Sample")
    print("="*60)
    print(expense_df.head(10).to_string())

if __name__ == "__main__":
    main()