# -*- coding: utf-8 -*-

# --- ▼▼▼ 設定はここにまとめるのがおすすめ！ ▼▼▼ ---

# AIに生成させるタグの候補リストだよ。ここを編集すればタグを自由に変えられる！
ALLOWED_TAGS = [
    "コーヒー豆", "カフェ", "イベント", "サステナビリティ", "健康", "研究",
    "ビジネス", "カルチャー", "レシピ", "スペシャルティコーヒー", "産地",
    "ハンドドリップ", "エスプレッソ", "コールドブリュー", "トレンド", "歴史"
]
# プロンプトで使いやすいように、タグリストを文字列に変換しとく
ALLOWED_TAGS_TEXT = ", ".join(ALLOWED_TAGS)

# Geminiに渡すプロンプトのテンプレートだよ
_COMMON_PROMPT_PART = f"さらに、記事の内容に最も関連性の高いタグを、下記のリストの中から最大3つまで選び、配列形式で生成してください。リストに適切なタグがない場合は、無理に選ばず空の配列 `[]` としてください。\n\nタグのリスト: [{ALLOWED_TAGS_TEXT}]\n\n"

JAPAN_PROMPT = "以下のニュース記事を、日本のコーヒー好きの読者向けに、150字程度で親しみやすく要約してください。" + _COMMON_PROMPT_PART + "結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"{title}\",\n  \"summary\": \"ここに要約した内容\",\n  \"tags\": [\"選んだタグ1\", \"選んだタグ2\"]\n}}\n\nタイトル: {title}\n記事の元リンク: {link}"
OVERSEAS_PROMPT = "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。" + _COMMON_PROMPT_PART + "結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\",\n  \"tags\": [\"選んだタグ1\", \"選んだタグ2\"]\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"

# --- リージョン（地域）の定義 ---
REGIONS = {
    "japan": "日本",
    "asia": "アジア",
    "eu_us": "欧米",
    "latin_america": "中南米",
    "africa": "アフリカ"
}

# 収集するRSSフィードのリスト
FEEDS = [
    # --- 日本 ---
    {
        "region": "japan",
        "country_code": "japan",
        "country_name": "日本",
        "url": "https://news.google.com/rss/search?q=coffee&hl=ja&gl=JP&ceid=JP:ja",
        "prompt": JAPAN_PROMPT,
        "articles_to_fetch": 15
    },
    # --- アジア ---
    {
        "region": "asia",
        "country_code": "cn",
        "country_name": "中国",
        "url": "https://news.google.com/rss/search?q=咖啡&hl=zh-CN&gl=CN&ceid=CN:zh-CN",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "asia",
        "country_code": "tw",
        "country_name": "台湾",
        "url": "https://news.google.com/rss/search?q=咖啡&hl=zh-TW&gl=TW&ceid=TW:zh-TW",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "asia",
        "country_code": "kr",
        "country_name": "韓国",
        "url": "https://news.google.com/rss/search?q=커피&hl=ko&gl=KR&ceid=KR:ko",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "asia",
        "country_code": "vn",
        "country_name": "ベトナム",
        "url": "https://news.google.com/rss/search?q=cà phê&hl=vi&gl=VN&ceid=VN:vi",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "asia",
        "country_code": "sg",
        "country_name": "シンガポール",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-SG&gl=SG&ceid=SG:en-SG",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    # --- 欧米 ---
    {
        "region": "eu_us",
        "country_code": "usa",
        "country_name": "アメリカ",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-US&gl=US&ceid=US:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "australia",
        "country_name": "オーストラリア",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-AU&gl=AU&ceid=AU:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "italy",
        "country_name": "イタリア",
        "url": "https://news.google.com/rss/search?q=caffè&hl=it&gl=IT&ceid=IT:it",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "germany",
        "country_name": "ドイツ",
        "url": "https://news.google.com/rss/search?q=kaffee&hl=de&gl=DE&ceid=DE:de",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "gb",
        "country_name": "イギリス",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-GB&gl=GB&ceid=GB:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "france",
        "country_name": "フランス",
        "url": "https://news.google.com/rss/search?q=café&hl=fr&gl=FR&ceid=FR:fr",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "es",
        "country_name": "スペイン",
        "url": "https://news.google.com/rss/search?q=café&hl=es&gl=ES&ceid=ES:es",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "eu_us",
        "country_code": "pt",
        "country_name": "ポルトガル",
        "url": "https://news.google.com/rss/search?q=café&hl=pt-PT&gl=PT&ceid=PT:pt-PT",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    # --- 中南米 ---
    {
        "region": "latin_america",
        "country_code": "brazil",
        "country_name": "ブラジル",
        "url": "https://news.google.com/rss/search?q=café&hl=pt-BR&gl=BR&ceid=BR:pt-BR",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "colombia",
        "country_name": "コロンビア",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=CO&ceid=CO:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "cr",
        "country_name": "コスタリカ",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=CR&ceid=CR:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "pa",
        "country_name": "パナマ",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=PA&ceid=PA:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "sv",
        "country_name": "エルサルバドル",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=SV&ceid=SV:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "gt",
        "country_name": "グァテマラ",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=GT&ceid=GT:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "mx",
        "country_name": "メキシコ",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=MX&ceid=MX:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "latin_america",
        "country_code": "pe",
        "country_name": "ペルー",
        "url": "https://news.google.com/rss/search?q=café&hl=es-419&gl=PE&ceid=PE:es-419",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    # --- アフリカ ---
    {
        "region": "africa",
        "country_code": "et",
        "country_name": "エチオピア",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-ET&gl=ET&ceid=ET:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "africa",
        "country_code": "ke",
        "country_name": "ケニア",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-KE&gl=KE&ceid=KE:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "africa",
        "country_code": "ug",
        "country_name": "ウガンダ",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-UG&gl=UG&ceid=UG:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    },
    {
        "region": "africa",
        "country_code": "rw",
        "country_name": "ルワンダ",
        "url": "https://news.google.com/rss/search?q=coffee&hl=en-RW&gl=RW&ceid=RW:en",
        "prompt": OVERSEAS_PROMPT,
        "articles_to_fetch": 5
    }
]