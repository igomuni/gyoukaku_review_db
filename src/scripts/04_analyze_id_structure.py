import sys
import pandas as pd
from pathlib import Path
from itertools import product

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
COLUMN_TYPE_PATH = ANALYSIS_DIR / "column_type.csv"

# 分析対象とする事業番号関連の列名
ID_CANDIDATE_COLUMNS = [
    '事業番号', '事業番号-1', '事業番号-2', 
    '事業番号-3', '事業番号-4', '事業番号-5'
]

def analyze_id_structure_evolution():
    """
    column_type.csvからID候補列のデータ型の変遷を分析する。
    """
    if not COLUMN_TYPE_PATH.exists():
        print(f"[Error] '{COLUMN_TYPE_PATH}' not found. Please run 03_analyze_columns.py first.")
        return None
        
    df = pd.read_csv(COLUMN_TYPE_PATH)
    
    # ID候補列のみに絞り込む
    id_df = df[df['column_name'].isin(ID_CANDIDATE_COLUMNS)].copy()
    
    # ファイル名から年度を抽出（例: database2014_... -> 2014）
    id_df['year'] = id_df['filename'].str.extract(r'(\d{4})')
    
    # シートタイプを抽出（レビューシート or セグメントシート）
    id_df['sheet_type'] = id_df['filename'].apply(
        lambda x: 'segment' if 'セグメント' in x else 'review'
    )
    
    # 年度とシートタイプごとに、各ID候補列がどの型だったかをピボットで集計
    pivot = id_df.pivot_table(
        index=['year', 'sheet_type'],
        columns='column_name',
        values='column_type',
        aggfunc='first' # 同じ年度/シートタイプに複数ファイルがあっても最初の一つを取る
    )
    
    # 列の順序を整える
    pivot = pivot.reindex(columns=ID_CANDIDATE_COLUMNS).fillna('-')
    
    return pivot

def analyze_id_combination_patterns():
    """
    各ファイル内のID候補列の非NULLの組み合わせパターンを分析する。
    """
    all_patterns = []
    
    csv_files = sorted(list(NORMALIZED_DIR.glob('*レビューシート.csv')) + list(NORMALIZED_DIR.glob('*セグメントシート.csv')))
    if not csv_files:
        print("[Warning] No review/segment sheet files found in 'data/normalized/'.")
        return pd.DataFrame()

    for i, filepath in enumerate(csv_files):
        print(f"({i+1}/{len(csv_files)}) Analyzing combination patterns in '{filepath.name}'...")
        try:
            df = pd.read_csv(filepath, usecols=lambda col: col in ID_CANDIDATE_COLUMNS, low_memory=True)
            
            # 存在しないID候補列を追加しておく
            for col in ID_CANDIDATE_COLUMNS:
                if col not in df.columns:
                    df[col] = None
            
            # 各列が非NULLかどうかのフラグを作成
            for col in ID_CANDIDATE_COLUMNS:
                df[f'{col}_exists'] = df[col].notna()
            
            exists_cols = [f'{col}_exists' for col in ID_CANDIDATE_COLUMNS]
            
            # パターンごとの出現回数をカウント
            pattern_counts = df[exists_cols].value_counts().reset_index(name='count')
            pattern_counts['filename'] = filepath.name
            
            all_patterns.append(pattern_counts)
            
        except Exception as e:
            print(f"  [Error] Failed to process {filepath.name}: {e}")
            
    if not all_patterns:
        return pd.DataFrame()
        
    result_df = pd.concat(all_patterns, ignore_index=True)
    return result_df

def main():
    """
    事業番号関連列の構造とパターンの分析を実行し、結果をCSVに出力する。
    """
    print("--- 04_analyze_id_structure.py: Start ---")
    ANALYSIS_DIR.mkdir(exist_ok=True)

    # --- 分析1: ID構造の変遷 ---
    print("\n[1/2] Analyzing ID structure evolution from column_type.csv...")
    evolution_df = analyze_id_structure_evolution()
    if evolution_df is not None:
        output_path = ANALYSIS_DIR / 'id_structure_evolution.csv'
        evolution_df.to_csv(output_path, encoding='utf-8-sig')
        print(f"  -> Saved to '{output_path}'")

    # --- 分析2: ID組み合わせパターン ---
    print("\n[2/2] Analyzing ID combination patterns from normalized CSVs...")
    combination_df = analyze_id_combination_patterns()
    if not combination_df.empty:
        output_path = ANALYSIS_DIR / 'id_combination_patterns.csv'
        combination_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"  -> Saved to '{output_path}'")
        
    print("\n--- 04_analyze_id_structure.py: Finished ---")

if __name__ == "__main__":
    main()