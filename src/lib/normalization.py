# src/lib/normalization.py

import re
import unicodedata
import uuid

# --- 正規化ルールで使用する正規表現 (コンパイル済み) ---
HYPHEN_LIKE_CHARS = r'[\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFF0D]'
RE_HYPHEN_LIKE = re.compile(HYPHEN_LIKE_CHARS)
RE_KATAKANA_HYPHEN = re.compile(r'([ァ-ヴ])' + HYPHEN_LIKE_CHARS + r'(?=[ァ-ヴ])')
RE_WAREKI = re.compile(r'(平成|H|令和|R)(\d{1,2}|元)')

# カタカナ長音変換の「事前正規化」ルール
KATAKANA_HYPHEN_PRE_NORMALIZATION = {
    "リスト-グル-プ": "リスト-グループ"
}
# カタカナ長音変換の「例外」リスト
KATAKANA_HYPHEN_EXCLUSIONS = [
    "リスト-グループ"
]

def normalize_text(text: str) -> str:
    """
    単一のセル文字列に対して、定義された全ての日本語正規化ルールを適用する。
    """
    if not isinstance(text, str):
        return text

    text = unicodedata.normalize('NFKC', text)

    def convert_wareki_to_seireki(match):
        era, year_str = match.groups()
        year = 1 if year_str == '元' else int(year_str)
        if era in ('平成', 'H'): return str(1988 + year)
        if era in ('令和', 'R'): return str(2018 + year)
        return match.group(0)
    text = RE_WAREKI.sub(convert_wareki_to_seireki, text)

    # 事前正規化
    for wrong_pattern, correct_form in KATAKANA_HYPHEN_PRE_NORMALIZATION.items():
        pattern_str = HYPHEN_LIKE_CHARS.join(map(re.escape, wrong_pattern.split('-')))
        text = re.sub(pattern_str, correct_form, text)
        
    # 例外単語を一時的なプレースホルダーに置き換える
    placeholders = {}
    for exclusion in KATAKANA_HYPHEN_EXCLUSIONS:
        pattern_str = HYPHEN_LIKE_CHARS.join(map(re.escape, exclusion.split('-')))
        pattern = re.compile(pattern_str)
        
        def replacer(match):
            placeholder = f"__PLACEHOLDER_{uuid.uuid4().hex}__"
            placeholders[placeholder] = match.group(0)
            return placeholder
        
        text = pattern.sub(replacer, text)

    # 汎用ルール適用: カタカナ間のハイフン -> 長音記号
    text = RE_KATAKANA_HYPHEN.sub(r'\1ー', text)
    
    # ハイフン類似文字を標準的なハイフンマイナス(-)に統一
    text = RE_HYPHEN_LIKE.sub('-', text)
    
    # 不要なハイフンの除去 (日本語文字に挟まれたハイフン)
    text = re.sub(r'([ぁ-んァ-ヴ一-龠])-(?=[ぁ-んァ-ヴ一-龠])', r'\1', text)
    
    # 復元: 全てのハイフン処理が終わった後、最後にプレースホルダーを元の文字列に戻す
    for placeholder, original_value in placeholders.items():
        text = text.replace(placeholder, original_value)

    return text.strip()