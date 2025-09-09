import sys
import pandas as pd
from pathlib import Path

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

from src.config import MINISTRY_NAME_VARIATIONS, MINISTRY_MASTER_DATA
from src.lib.normalization import normalize_text

# --- 定数と設定 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

FILENAME_YEAR_MAP = {
    'database240918': 2023, 'database240502': 2022, 'database220524': 2021,
    'database_220427': 2020, 'database2019_220427': 2019, 'database2018_220427': 2018,
    'database2017': 2017, 'database2016': 2016, 'database2015': 2015,
    'database2014': 2014,
}

# --- マスターデータの準備 ---
MINISTRY_DF = pd.DataFrame(MINISTRY_MASTER_DATA)
MINISTRY_NAME_TO_ID = pd.Series(MINISTRY_DF.ministry_id.values, index=MINISTRY_DF.ministry_name).to_dict()

def get_year_from_filename(filename):
    for key, year in FILENAME_YEAR_MAP.items():
        if key in filename: return year
    return None

def split_start_end_years(series):
    """事業開始・終了年度を分割する堅牢かつシンプルな関数"""
    s = series.astype(str).str.strip()
    
    result_df = pd.DataFrame(index=s.index, columns=['start_year', 'end_year'])
    
    # 1. '終了(予定)なし' のパターンを処理
    no_end_mask = (s == '終了(予定)なし')
    result_df.loc[no_end_mask, 'start_year'] = None
    result_df.loc[no_end_mask, 'end_year'] = '終了(予定)なし'
    
    # 2. 残りのデータ（'終了(予定)なし'ではないもの）を処理
    remaining_s = s[~no_end_mask]
    remaining_s = remaining_s.str.replace(r'[～~]', '・', regex=True)
    
    split_parts = remaining_s.str.split('・', n=1, expand=True)
    
    result_df.loc[~no_end_mask, 'start_year'] = split_parts[0]
    result_df.loc[~no_end_mask, 'end_year'] = split_parts[1]
    
    # 3. 各列を正規化して返す (normalize_textはNoneをそのまま返す)
    start_year = result_df['start_year'].str.strip().replace('', None).apply(normalize_text)
    end_year = result_df['end_year'].str.strip().replace('', None).apply(
        lambda x: normalize_text(x) if x != '終了(予定)なし' else x
    )
    
    return start_year, end_year

def main():
    print("--- 07_build_business_master.py (Robust Version): Start ---")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    all_master_records = []
    
    review_sheets = sorted(
        list(NORMALIZED_DIR.glob('*レビューシート.csv')) + 
        list(NORMALIZED_DIR.glob('*データベース.csv')) +
        list(NORMALIZED_DIR.glob('*_Sheet1.csv'))
    )

    for filepath in review_sheets:
        file_year = get_year_from_filename(filepath.name)
        if not file_year: continue
        print(f"  - Processing '{filepath.name}' (Year: {file_year})...")
        
        try:
            df = pd.read_csv(filepath, low_memory=False)
            
            for col in ['事業番号-3', '事業番号-4', '事業番号-5']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

            df.rename(columns={'府省': '府省庁', '事業開始・終了(予定)年度': '事業開始年度_raw'}, inplace=True)
            
            df['id'] = [f"{file_year}-{str(i+1).zfill(5)}" for i in range(len(df))]
            
            if '府省庁' in df.columns:
                df['normalized_ministry_name'] = df['府省庁'].replace(MINISTRY_NAME_VARIATIONS)
                df['ministry_id'] = df['normalized_ministry_name'].map(MINISTRY_NAME_TO_ID).astype('Int64')
            else:
                df['ministry_id'] = pd.Series(dtype='Int64')
                
            if '事業開始年度_raw' in df.columns:
                df['事業開始年度'], df['事業終了(予定)年度'] = split_start_end_years(df['事業開始年度_raw'])
            
            all_master_records.append(df)

        except Exception as e:
            print(f"    [Error] Failed to process {filepath.name}: {e}")

    master_df = pd.concat(all_master_records, ignore_index=True)

    final_output_columns = [
        'id', 'ministry_id', '府省庁',
        '事業番号', '事業番号-1', '事業番号-2', '事業番号-3', '事業番号-4', '事業番号-5',
        '事業名', '事業開始年度', '事業終了(予定)年度'
    ]
    
    final_df = master_df.reindex(columns=final_output_columns)
    final_df.sort_values(by='id', inplace=True)
    
    output_path = PROCESSED_DIR / 'business_master.csv'
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\nBusiness master creation complete. Total {len(final_df)} records.")
    print(f"Result saved to '{output_path}'")
    print("\n--- Generated Business Master (Sample) ---")
    print(final_df.head().to_string())
    print("...")
    print(final_df.tail().to_string())
    
    print("\n--- 07_build_business_master.py: Finished ---")


if __name__ == "__main__":
    main()