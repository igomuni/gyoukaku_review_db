import sys
import pandas as pd
import re
from pathlib import Path

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
COLUMN_TYPE_PATH = ANALYSIS_DIR / "column_type.csv"

# 分析したい列名のパターンを正規表現で定義
# (?P<name>...) はマッチした部分に名前を付ける記法
COLUMN_PATTERNS = {
    '費目・使途': re.compile(r'^費目・使途.*'),
    '支出先上位10者リスト': re.compile(r'^支出先上位10者リスト.*'),
    '国庫債務負担行為等': re.compile(r'^国庫債務負担行為等.*'),
    '予算額・執行額': re.compile(r'^予算額・執行額.*'),
    '成果目標及び成果実績': re.compile(r'^成果目標及び成果実績.*'),
    '事業番号': re.compile(r'^事業番号.*'),
}

def main():
    """
    column_type.csvを読み込み、列名をパターンで集約・分析する
    """
    print("--- 05_analyze_column_patterns.py: Start ---")
    if not COLUMN_TYPE_PATH.exists():
        print(f"[Error] '{COLUMN_TYPE_PATH}' not found. Please run 03 first.")
        return

    df = pd.read_csv(COLUMN_TYPE_PATH)

    # 各列がどのパターンに属するかを判定する
    def classify_column(column_name):
        for pattern_name, regex in COLUMN_PATTERNS.items():
            if regex.match(str(column_name)):
                return pattern_name
        return 'Other' # どのパターンにも一致しないもの

    print("Classifying columns by patterns...")
    df['pattern_group'] = df['column_name'].apply(classify_column)

    # パターンごとに統計情報を集計
    print("Aggregating statistics by pattern group...")
    
    # 代表的なデータ型を抽出（最も出現回数の多いもの）
    agg_funcs = {
        'column_name': 'count',
        'column_type': lambda x: x.mode()[0] if not x.empty else None,
        'null_rate': 'mean',
        'only_num_rate': 'mean',
        'max_len': 'max',
    }

    summary_df = df.groupby('pattern_group').agg(agg_funcs).rename(
        columns={
            'column_name': 'column_count',
            'column_type': 'dominant_column_type',
            'null_rate': 'avg_null_rate',
            'only_num_rate': 'avg_only_num_rate',
            'max_len': 'overall_max_len'
        }
    ).sort_values(by='column_count', ascending=False)

    # --- 結果を保存 ---
    output_path = ANALYSIS_DIR / 'column_patterns_summary.csv'
    summary_df.to_csv(output_path, encoding='utf-8-sig')
    
    print(f"\nAnalysis complete. Results saved to '{output_path}'")
    print("\n--- Summary ---")
    print(summary_df)
    print("\n--- 05_analyze_column_patterns.py: Finished ---")


if __name__ == "__main__":
    main()