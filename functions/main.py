# -*- coding: utf-8 -*-

import os
import requests
import xml.etree.ElementTree as ET
import time
import json
import google.generativeai as genai
from firebase_admin import firestore, initialize_app
from firebase_functions import https_fn, options

# FirebaseとGeminiを初期化するよ
initialize_app()

# ★超大事★ GeminiのAPIキーを安全な場所から読み込む設定
options.set_global_options(secrets=["GEMINI_API_KEY"])

# この関数がURLで呼ばれたら実行される！
@https_fn.on_request()
def fetch_and_summarize_articles(req: https_fn.Request) -> https_fn.Response:
    """
    Google NewsのRSSからコーヒー関連の記事を取得して、
    Geminiで要約してFirestoreに保存するHTTP関数だよん！
    """

    # ★★★ここがポイント！★★★ 関数が呼ばれてからGeminiの準備をする！
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Firestoreのデータベースに接続！
    db = firestore.client()

    # 収集するRSSフィードのリスト
    feeds = [
        {
            "category": "japan",
            "name": "日本",
            "url": "https://news.google.com/rss/search?q=coffee&hl=ja&gl=JP&ceid=JP:ja",
            "prompt": "以下のニュース記事を、日本のコーヒー好きの読者向けに、150字程度で親しみやすく要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"{title}\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\nタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "usa",
            "name": "アメリカ",
            "url": "https://news.google.com/rss/search?q=coffee&hl=en-US&gl=US&ceid=US:en",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "australia",
            "name": "オーストラリア",
            "url": "https://news.google.com/rss/search?q=coffee&hl=en-AU&gl=AU&ceid=AU:en",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "italy",
            "name": "イタリア",
            "url": "https://news.google.com/rss/search?q=coffee&hl=it&gl=IT&ceid=IT:it",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "germany",
            "name": "ドイツ",
            "url": "https://news.google.com/rss/search?q=coffee&hl=de&gl=DE&ceid=DE:de",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "gb",
            "name": "イギリス",
            "url": "https://news.google.com/rss/search?q=coffee&hl=en-GB&gl=GB&ceid=GB:en",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        },
        {
            "category": "france",
            "name": "フランス",
            "url": "https://news.google.com/rss/search?q=coffee&hl=fr&gl=FR&ceid=FR:fr",
            "prompt": "以下の海外のニュース記事について、タイトルを日本語に翻訳し、内容を日本語で150字程度に要約してください。結果は必ず以下のJSON形式で返してください:\n{{\n  \"title\": \"ここに翻訳したタイトル\",\n  \"summary\": \"ここに要約した内容\"\n}}\n\n元のタイトル: {title}\n記事の元リンク: {link}"
        }
    ]

    total_articles_saved = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # 各フィードをループして処理
        for feed in feeds:
            print(f"カテゴリ '{feed['name']}' の記事を収集中...")
            response = requests.get(feed['url'], headers=headers)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # 各カテゴリから最新5件の記事を処理するよ
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text

                print(f"  処理中の記事: {title}")

                # Geminiくんに要約をお願いする！
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt_text = feed['prompt'].format(title=title, link=link)
                
                summary_response = model.generate_content(prompt_text)
                
                try:
                    # Geminiからのレスポンスはマークダウンで返ってくることがあるので、```json ... ``` を取り除く
                    cleaned_response = summary_response.text.strip().replace("```json", "").replace("```", "")
                    result = json.loads(cleaned_response)
                    processed_title = result.get("title", title)
                    summary = result.get("summary", "要約の取得に失敗しました。")
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"  JSONのパースに失敗: {e}. レスポンス: {summary_response.text}")
                    processed_title = f"{title} (処理失敗)"
                    summary = "記事の処理に失敗しました。元の記事をご確認ください。"

                # データベースに保存するデータを作成
                article_data = {
                    'title': processed_title, # ★処理済みのタイトルに更新
                    'link': link,
                    'summary': summary,
                    'published_at': pub_date,
                    'category': feed['category'], # ★カテゴリを追加！
                    'category_name': feed['name'], # ★カテゴリ名も追加！
                    'created_at': firestore.SERVER_TIMESTAMP
                }
                # Firestoreに保存するために、記事のリンクをIDにする（重複防止！）
                doc_id = link.replace('/', '_').replace(':', '_') # IDに使えない文字を置換
                article_ref = db.collection('articles').document(doc_id)
                article_ref.set(article_data, merge=True) # merge=Trueで既存の記事を上書き（更新）
                
                total_articles_saved += 1
            
            # サーバーに負荷をかけないように、ちょっと待つ
            print("  次の国に行く前にちょっと休憩... ☕")
            time.sleep(1)

        return https_fn.Response(f"イケてる記事を合計 {total_articles_saved} 件GETして保存しといたよ！✨")

    except Exception as e:
        print(f"まじごめん、エラーでた: {e}")
        return https_fn.Response("内部でエラーでたわ…ごめんて🙏", status=500)