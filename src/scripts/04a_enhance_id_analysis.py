import sys
import pandas as pd
from pathlib import Path

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
COLUMN_TYPE_PATH = ANALYSIS_DIR / "column_type.csv"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"

# ユーザー提供のファイル名と年度の対応表
FILENAME_YEAR_MAP = {
    'database240918': 2023,
    'database240502': 2022,
    'database220524': 2021,
    'database_220427': 2020,
    'database2019_220427': 2019,
    'database2018_220427': 2018,
    'database2017': 2017,
    'database2016': 2016,
    'database2015': 2015,
    'database2014': 2014,
}

ID_CANDIDATE_COLUMNS = [
    '事業番号', '事業番号-1', '事業番号-2', 
    '事業番号-3', '事業番号-4', '事業番号-5'
]

def get_year_from_filename(filename):
    """ファイル名から正確な年度を取得する"""
    for key, year in FILENAME_YEAR_MAP.items():
        if key in filename:
            return year
    return None

def analyze_string_content(filepath, column_name):
    """指定されたCSVの文字列カラムの内容を分析する"""
    try:
        series = pd.read_csv(filepath, usecols=[column_name], squeeze=True).dropna()
        if series.empty:
            return 'empty', 0, 0
            
        str_series = series.astype(str)
        
        # 文字列の構成を判定
        contains_alpha = str_series.str.contains(r'[A-Za-zぁ-んァ-ヴ一-龠]').any()
        contains_digit = str_series.str.contains(r'[0-9]').any()
        
        if contains_alpha and contains_digit:
            content_type = 'mixed'
        elif contains_alpha:
            content_type = 'alpha_only'
        elif contains_digit:
            content_type = 'digit_only'
        else:
            content_type = 'symbol_or_empty'
            
        # 文字長の最大・最小
        lengths = str_series.str.len()
        return content_type, lengths.max(), lengths.min()

    except Exception:
        return 'error', None, None


def main():
    """
    column_type.csvを拡張し、ID候補列の詳細な特性分析を行う
    """
    print("--- 04a_enhance_id_analysis.py: Start ---")
    if not COLUMN_TYPE_PATH.exists():
        print(f"[Error] '{COLUMN_TYPE_PATH}' not found. Please run 03 first.")
        return

    df = pd.read_csv(COLUMN_TYPE_PATH)
    
    # ID候補列に絞り込み、正確な年度をマッピング
    id_df = df[df['column_name'].isin(ID_CANDIDATE_COLUMNS)].copy()
    id_df['year'] = id_df['filename'].apply(get_year_from_filename)
    id_df = id_df.dropna(subset=['year']).astype({'year': int})

    # --- 新しい分析指標を追加 ---
    new_metrics = []
    
    print("Analyzing column details (this may take some time)...")
    for _, row in id_df.iterrows():
        metrics = {}
        
        # 数値列の役割推測
        if row['column_type'] in ['integer', 'float']:
            min_val, max_val = row['min_val'], row['max_val']
            if 2010 <= min_val <= max_val <= 2030:
                metrics['role_guess'] = 'Year'
            elif max_val - min_val > 200: # 差が大きければ連番の可能性
                metrics['role_guess'] = 'Sequential Number'
            elif max_val < 100: # 100未満なら何かのコード値
                metrics['role_guess'] = 'Code Value'
            else:
                metrics['role_guess'] = 'Other Numeric'
        
        # 文字列列の内容分析
        elif row['column_type'] == 'string':
            filepath = NORMALIZED_DIR / row['filename']
            content_type, max_len, min_len = analyze_string_content(filepath, row['column_name'])
            metrics['str_content_type'] = content_type
            metrics['str_max_len'] = max_len
            metrics['str_min_len'] = min_len
            metrics['role_guess'] = 'String ID'

        new_metrics.append(metrics)
    
    # 分析結果を元のDataFrameに結合
    metrics_df = pd.DataFrame(new_metrics, index=id_df.index)
    enhanced_df = pd.concat([id_df, metrics_df], axis=1)

    # --- 結果を保存 ---
    output_path = ANALYSIS_DIR / 'id_structure_details.csv'
    enhanced_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nAnalysis complete. Results saved to '{output_path}'")
    
    print("\n--- 04a_enhance_id_analysis.py: Finished ---")


if __name__ == "__main__":
    main()