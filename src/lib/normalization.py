import re
import unicodedata
import uuid

# --- 正規表現定義 (役割ごとに整理) ---

# 1. 前処理用
RE_LIST_MARKER = re.compile(r'([①-⑳])')
RE_TILDE_VARIANTS = re.compile(r'\s*[~～]\s*')

# 2. 和暦変換用 (より賢く)
# パターン1: 「元号A年～B年」形式 (元号が省略された範囲指定)
RE_WAREKI_RANGE = re.compile(r'(明治|M|大正|T|昭和|S|平成|H|令和|R)(\d{1,2}|元)\s*～\s*(\d{1,2})')
# パターン2: 通常の「元号N年」形式
RE_WAREKI_SINGLE = re.compile(r'(明治|M|大正|T|昭和|S|平成|H|令和|R)(\d{1,2}|元)')

# 3. ハイフン処理用 (変更なし)
HYPHEN_LIKE_CHARS = r'[\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFF0D]'
RE_HYPHEN_LIKE = re.compile(HYPHEN_LIKE_CHARS)
RE_KATAKANA_HYPHEN = re.compile(r'([ァ-ヴ])' + HYPHEN_LIKE_CHARS + r'(?=[ァ-ヴ])')
KATAKANA_HYPHEN_PRE_NORMALIZATION = {"リスト-グル-プ": "リスト-グループ"}
KATAKANA_HYPHEN_EXCLUSIONS = ["リスト-グループ"]


# --- 変換ロジック ---

def _get_seireki(era, year_str):
    """元号と和暦年から西暦年を返すヘルパー関数"""
    year = 1 if year_str == '元' else int(year_str)
    if era in ('明治', 'M'): return 1867 + year
    if era in ('大正', 'T'): return 1911 + year
    if era in ('昭和', 'S'): return 1925 + year
    if era in ('平成', 'H'): return 1988 + year
    if era in ('令和', 'R'): return 2018 + year
    return None

def normalize_text(text: str) -> str:
    """
    単一のセル文字列に対して、定義された全ての日本語正規化ルールを適用する。
    """
    if not isinstance(text, str): return text

    # --- ステップ1: 前処理 (NFKC正規化の前に実施) ---
    
    # ①などのリストマーカーを「1. 」のように変換し、数値の連結を防ぐ
    def replace_list_marker(match):
        # NFKCで'①'は'1'に変換されるが、ここでは手動で変換テーブルを持つ
        marker_map = { '①':'1','②':'2','③':'3','④':'4','⑤':'5','⑥':'6','⑦':'7','⑧':'8','⑨':'9','⑩':'10',
                       '⑪':'11','⑫':'12','⑬':'13','⑭':'14','⑮':'15','⑯':'16','⑰':'17','⑱':'18','⑲':'19','⑳':'20'}
        return marker_map.get(match.group(1), match.group(1)) + '. '
    text = RE_LIST_MARKER.sub(replace_list_marker, text)

    # --- ステップ2: 基本正規化 ---
    text = unicodedata.normalize('NFKC', text)
    
    # ~ と ～ の揺れを、スペースも含めて統一
    text = RE_TILDE_VARIANTS.sub('～', text)

    # --- ステップ3: 和暦から西暦への変換 (複数パターン対応) ---
    
    # 3a. 「平成9～25年度」のような範囲指定を先に処理
    def convert_wareki_range(match):
        era, year1_str, year2_str = match.groups()
        seireki1 = _get_seireki(era, year1_str)
        seireki2 = _get_seireki(era, year2_str) # 省略された元号を補って変換
        if seireki1 is not None and seireki2 is not None:
            return f"{seireki1}～{seireki2}"
        return match.group(0) # 変換失敗時は元に戻す
    text = RE_WAREKI_RANGE.sub(convert_wareki_range, text)

    # 3b. 残りの単体の和暦を処理
    def convert_wareki_single(match):
        era, year_str = match.groups()
        seireki = _get_seireki(era, year_str)
        return str(seireki) if seireki is not None else match.group(0)
    text = RE_WAREKI_SINGLE.sub(convert_wareki_single, text)
    
    # --- ステップ4: ハイフン関連の処理 (変更なし) ---
    placeholders = {}
    # (ここから下のハイフン処理ロジックは前回から変更ありません)
    for wrong, correct in KATAKANA_HYPHEN_PRE_NORMALIZATION.items():
        pattern_str = HYPHEN_LIKE_CHARS.join(map(re.escape, wrong.split('-')))
        text = re.sub(pattern_str, correct, text)
    for exclusion in KATAKANA_HYPHEN_EXCLUSIONS:
        pattern_str = HYPHEN_LIKE_CHARS.join(map(re.escape, exclusion.split('-')))
        def replacer(match):
            placeholder = f"__PLACEHOLDER_{uuid.uuid4().hex}__"
            placeholders[placeholder] = match.group(0)
            return placeholder
        text = re.compile(pattern_str).sub(replacer, text)
    text = RE_KATAKANA_HYPHEN.sub(r'\1ー', text)
    text = RE_HYPHEN_LIKE.sub('-', text)
    text = re.sub(r'([ぁ-んァ-ヴ一-龠])-(?=[ぁ-んァ-ヴ一-龠])', r'\1', text)
    for placeholder, original_value in placeholders.items():
        text = text.replace(placeholder, original_value)

    return text.strip()