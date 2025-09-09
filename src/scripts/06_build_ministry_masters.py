import sys
import pandas as pd
from pathlib import Path

# --- モジュール検索パス設定 ---
PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT_FOR_IMPORT))

from src.config import MINISTRY_MASTER_DATA

# --- 定数定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def main():
    """
    config.pyに定義されたマスターデータを元に、
    最終的なマスターCSVファイルを生成する。
    """
    print("--- 06_build_ministry_masters.py: Start ---")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # --- 府省庁マスターの生成 ---
    print("  - Building ministry_master.csv...")
    ministry_df = pd.DataFrame(MINISTRY_MASTER_DATA)
    
    output_path = PROCESSED_DIR / 'ministry_master.csv'
    ministry_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"    -> Saved to '{output_path}'")
    print("\n--- Generated Ministry Master ---")
    print(ministry_df.to_string())
    
    # (将来的に他のマスター（例: 年度マスタ）もここで生成できる)

    print("\n--- 06_build_ministry_masters.py: Finished ---")


if __name__ == "__main__":
    main()