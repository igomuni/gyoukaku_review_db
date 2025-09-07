import sys
import re
import pandas as pd
from pathlib import Path
from collections import Counter

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

# 列名分割用の正規表現
DELIMITER_REGEX = re.compile(r'[_\.｜\s\n/-]+')

# メモリを節約するため、一度に読み込む行数
CHUNKSIZE = 10000

def analyze_csv_content(filepath: Path) -> list:
    """
    CSVファイルをチャンクごとに読み込み、各列の詳細な統計情報を分析する。
    """
    try:
        # まずヘッダーだけを読み込む
        header = pd.read_csv(filepath, nrows=0, encoding='utf-8-sig').columns.tolist()
        if not header:
            return []
        
        # 各列の統計情報を保持する辞書を初期化
        col_metrics = {col: {
            'total_count': 0, 'null_count': 0, 'numeric_count': 0, 'integer_count': 0,
            'max_len': 0, 'max_val': -float('inf'), 'min_val': float('inf')
        } for col in header}

        # チャンクごとにファイルを読み込んで処理
        for chunk in pd.read_csv(filepath, chunksize=CHUNKSIZE, low_memory=True, encoding='utf-8-sig'):
            for col in header:
                metrics = col_metrics[col]
                
                # 基本統計
                metrics['total_count'] += len(chunk)
                metrics['null_count'] += chunk[col].isnull().sum()
                
                # 文字列長
                max_len_chunk = chunk[col].astype(str).str.len().max()
                if max_len_chunk > metrics['max_len']:
                    metrics['max_len'] = max_len_chunk
                    
                # 数値関連の統計
                numeric_series = pd.to_numeric(chunk[col], errors='coerce')
                metrics['numeric_count'] += numeric_series.notna().sum()
                
                # 整数判定（浮動小数点数でない数値）
                integer_series = numeric_series[numeric_series.notna() & (numeric_series == numeric_series.round(0))]
                metrics['integer_count'] += len(integer_series)

                # 最大値・最小値
                if not numeric_series.isnull().all():
                    max_val_chunk = numeric_series.max()
                    min_val_chunk = numeric_series.min()
                    if max_val_chunk > metrics['max_val']: metrics['max_val'] = max_val_chunk
                    if min_val_chunk < metrics['min_val']: metrics['min_val'] = min_val_chunk

        # 最終的な分析結果をリストにまとめる
        final_results = []
        for col, metrics in col_metrics.items():
            total_count = metrics['total_count']
            
            # データ型を推論
            col_type = 'string'
            non_null_count = total_count - metrics['null_count']
            if non_null_count == 0:
                col_type = 'empty'
            elif metrics['numeric_count'] == non_null_count:
                if metrics['integer_count'] == non_null_count:
                    col_type = 'integer'
                else:
                    col_type = 'float'
            
            final_results.append({
                'filename': filepath.name,
                'column_name': col,
                'column_type': col_type,
                'null_rate': metrics['null_count'] / total_count if total_count > 0 else 0,
                'only_num_rate': metrics['numeric_count'] / total_count if total_count > 0 else 0,
                'max_len': metrics['max_len'],
                'max_val': metrics['max_val'] if metrics['max_val'] != -float('inf') else None,
                'min_val': metrics['min_val'] if metrics['min_val'] != float('inf') else None,
            })
        
        return final_results
    except Exception as e:
        print(f"\n[Error] Failed to analyze {filepath.name}: {e}")
        return []

def main():
    """
    normalizedフォルダ内の全CSVを分析し、3つの分析ファイルを出力する。
    """
    print("--- 03_analyze_columns.py: Start ---")

    ANALYSIS_DIR.mkdir(exist_ok=True)
    print(f"Input directory: '{NORMALIZED_DIR}'")
    print(f"Output directory: '{ANALYSIS_DIR}'")

    csv_files = sorted(list(NORMALIZED_DIR.glob('*.csv')))
    if not csv_files:
        print("\n[Warning] No .csv files found in 'data/normalized/' directory.")
        return

    all_column_headers = []
    all_column_analysis = []

    for i, filepath in enumerate(csv_files):
        print(f"\n({i+1}/{len(csv_files)}) Analyzing '{filepath.name}'...")
        
        # 1. 列名マトリクス用のヘッダー情報を収集
        header = pd.read_csv(filepath, nrows=0, encoding='utf-8-sig').columns.tolist()
        for col in header:
            all_column_headers.append({'filename': filepath.name, 'column_name': col})
        
        # 2. 列の型や統計情報を分析
        print("  - Analyzing column contents (this may take a while)...")
        analysis_results = analyze_csv_content(filepath)
        all_column_analysis.extend(analysis_results)
        print(f"  - Analysis for '{filepath.name}' complete.")

    # --- 分析結果をCSVに出力 ---
    print("\nSaving analysis results...")

    # 1. column_name_matrix.csv の作成
    if all_column_headers:
        matrix_df = pd.DataFrame(all_column_headers)
        matrix_df['exists'] = 1
        matrix_pivot = matrix_df.pivot_table(index='column_name', columns='filename', values='exists', fill_value=0)
        matrix_pivot.to_csv(ANALYSIS_DIR / 'column_name_matrix.csv', encoding='utf-8-sig')
        print(f"  - Saved 'column_name_matrix.csv' ({len(matrix_pivot)} unique columns)")

    # 2. column_name_split_ranking.csv の作成
    if all_column_headers:
        all_columns = pd.DataFrame(all_column_headers)['column_name'].unique()
        split_words = []
        for col in all_columns:
            split_words.extend(DELIMITER_REGEX.split(col))
        ranking = Counter(filter(None, split_words)) # 空白を除外してカウント
        ranking_df = pd.DataFrame(ranking.items(), columns=['token', 'count']).sort_values(by='count', ascending=False)
        ranking_df.to_csv(ANALYSIS_DIR / 'column_name_split_ranking.csv', index=False, encoding='utf-8-sig')
        print(f"  - Saved 'column_name_split_ranking.csv' ({len(ranking_df)} unique tokens)")
        
    # 3. column_type.csv の作成
    if all_column_analysis:
        type_df = pd.DataFrame(all_column_analysis)
        type_df.to_csv(ANALYSIS_DIR / 'column_type.csv', index=False, encoding='utf-8-sig')
        print(f"  - Saved 'column_type.csv' ({len(type_df)} rows)")

    print("\n--- 03_analyze_columns.py: Finished ---")

if __name__ == "__main__":
    main()