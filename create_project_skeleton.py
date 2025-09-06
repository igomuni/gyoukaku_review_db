import os

# --- 設定 ---
# 作成するプロジェクトのルートフォルダ名
PROJECT_ROOT = "gyoukaku_review_db"

# 作成するフォルダのリスト
# (os.path.joinを使ってOSの違いを吸収します)
DIRECTORIES = [
    os.path.join(PROJECT_ROOT, "data", "download"),
    os.path.join(PROJECT_ROOT, "data", "raw"),
    os.path.join(PROJECT_ROOT, "data", "normalized"),
    os.path.join(PROJECT_ROOT, "data", "processed"),
    os.path.join(PROJECT_ROOT, "src", "lib"),
    os.path.join(PROJECT_ROOT, "src", "scripts"),
    os.path.join(PROJECT_ROOT, "analysis"),
]

# 作成するファイルとその内容の辞書
# 内容が空文字列 "" の場合は空ファイルが作成されます
FILES = {
    os.path.join(PROJECT_ROOT, ".gitignore"): """\
# Data files
data/download/
data/raw/
data/normalized/
data/processed/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Analysis files (if needed)
analysis/*.csv
""",
    os.path.join(PROJECT_ROOT, "README.md"): "# 行政事業レビューDB\n",
    os.path.join(PROJECT_ROOT, "requirements.txt"): "pandas\n",
    os.path.join(PROJECT_ROOT, "src", "config.py"): "",
    os.path.join(PROJECT_ROOT, "src", "main_split.py"): "",
    os.path.join(PROJECT_ROOT, "src", "processor.py"): "",
    os.path.join(PROJECT_ROOT, "src", "lib", "normalization.py"): "",
    os.path.join(PROJECT_ROOT, "src", "scripts", "01_convert_to_csv.py"): "",
    os.path.join(PROJECT_ROOT, "src", "scripts", "02_normalize_data.py"): "",
    os.path.join(PROJECT_ROOT, "src", "scripts", "03_analyze_columns.py"): "",
    os.path.join(PROJECT_ROOT, "analysis", "column_name_matrix.csv"): "",
    os.path.join(PROJECT_ROOT, "analysis", "column_name_split_ranking.csv"): "",
    os.path.join(PROJECT_ROOT, "analysis", "csv_split_rules.md"): "# CSV分割ルール\n",
}

# --- 実行 ---
def create_skeleton():
    """プロジェクトのスケルトンを作成するメイン関数"""
    print(f"プロジェクトフォルダ '{PROJECT_ROOT}' を作成しています...")

    # ルートフォルダの作成
    if not os.path.exists(PROJECT_ROOT):
        os.makedirs(PROJECT_ROOT)

    # サブディレクトリの作成
    for directory in DIRECTORIES:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  [OK] Directory: {directory}")
        except OSError as e:
            print(f"  [Error] Failed to create directory {directory}: {e}")

    # ファイルの作成
    for filepath, content in FILES.items():
        try:
            # encoding='utf-8' を明示的に指定することで文字化けを防ぐ
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [OK] File:      {filepath}")
        except IOError as e:
            print(f"  [Error] Failed to create file {filepath}: {e}")
    
    print("\n---------------------------------")
    print("プロジェクトのスケルトン作成が完了しました。")
    print(f"カレントディレクトリに '{PROJECT_ROOT}' フォルダが作成されました。")
    print("---------------------------------")


if __name__ == "__main__":
    create_skeleton()