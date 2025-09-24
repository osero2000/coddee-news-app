# -*- coding: utf-8 -*-

import os
import requests
import xml.etree.ElementTree as ET
import hashlib
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import google.generativeai as genai
from firebase_admin import firestore, initialize_app
from firebase_functions import https_fn, options

# 設定ファイルをインポートするよ
import config 

# FirebaseとGeminiを初期化するよ
initialize_app() 

# ★超大事★ GeminiのAPIキーを安全な場所から読み込む設定
options.set_global_options(secrets=["GEMINI_API_KEY"]) 

# この関数がURLで呼ばれたら実行される！
@https_fn.on_request(timeout_sec=540) # タイムアウトを9分に延長！(処理時間の上限)
def fetch_and_summarize_articles(req: https_fn.Request) -> https_fn.Response:
    """
    Google NewsのRSSからコーヒー関連の記事を取得して、
    Geminiで要約してFirestoreに保存するHTTP関数だよん！
    Cloud Schedulerからの呼び出しを想定しているよ。(定期実行)
    """
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        db = firestore.client()
        model = genai.GenerativeModel('gemini-1.5-flash')

        total_articles_saved = 0
        # バッチ処理用のオブジェクトを準備 (Firestoreへの書き込みを効率化)
        batch = db.batch()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 各フィードをループして処理 (国ごとに設定されたRSSフィード)
        for feed in config.FEEDS:
            print(f"カテゴリ '{feed['country_name']}' の記事を収集中...") 
            try:
                response = requests.get(feed['url'], headers=headers, timeout=15) # タイムアウトを設定
                response.raise_for_status() # HTTPエラーがあれば例外を発生
                root = ET.fromstring(response.content)
            except requests.exceptions.RequestException as e:
                print(f"  [エラー] '{feed['country_name']}' のRSSフィード取得に失敗しました: {e}")
                continue # この国の処理をスキップして次に進む
            except ET.ParseError as e:
                print(f"  [エラー] '{feed['country_name']}' のXMLパースに失敗しました: {e}")
                continue # この国の処理をスキップして次に進む

            # 設定ファイルから取得件数を読み込むよ (各フィードで取得する記事数)
            num_articles_to_fetch = feed['articles_to_fetch']

            # 各カテゴリから最新の記事を処理するよ (RSSフィード内の記事)
            for item in root.findall('.//item')[:num_articles_to_fetch]:
                title = item.find('title').text # 記事のタイトル
                link = item.find('link').text # 記事のURL
                pub_date_str = item.find('pubDate').text

                # RSSの公開日時をパースしてdatetimeオブジェクトに変換するよ
                try:
                    pub_date = parsedate_to_datetime(pub_date_str)
                except (TypeError, ValueError):
                    pub_date = datetime.now(timezone.utc) # パース失敗したら今の時間

                # Firestoreに保存するために、記事のリンクをIDにする（重複防止！）
                doc_id = hashlib.sha256(link.encode('utf-8')).hexdigest()
                article_ref = db.collection('articles').document(doc_id) 

                # --- 古いデータのお掃除機能 ---
                # もし同じリンクで、country_codeが2文字じゃない古いデータがあったら削除する (データの正規化)
                old_docs_query = db.collection('articles').where('link', '==', link)
                for old_doc in old_docs_query.stream():
                    old_data = old_doc.to_dict()
                    if len(old_data.get('country_code', '')) != 2:
                        print(f"  [クリーンアップ] 古い形式のドキュメントを削除します: {old_doc.id} (country_code: {old_data.get('country_code')})")
                        batch.delete(old_doc.reference) # バッチに削除操作を追加 (Firestoreから古いデータを削除)
                # --- ここまで ---

                try:
                    print(f"  処理中の記事: {title}") 

                    # Geminiくんに要約をお願いする！ (AIによる記事の要約)
                    prompt_text = feed['prompt'].format(title=title, link=link)
                    summary_response = model.generate_content(prompt_text)

                    try: 
                        # Geminiからのレスポンスはマークダウンで返ってくることがあるので、```json ... ``` を取り除く
                        cleaned_response = summary_response.text.strip().replace("```json", "").replace("```", "")
                        result = json.loads(cleaned_response)
                        processed_title = result.get("title", title)
                        summary = result.get("summary", "要約の取得に失敗しました。")
                        tags = result.get("tags", []) # Geminiが生成したタグを取得するよ
                    except (json.JSONDecodeError, AttributeError) as e:
                        print(f"    [警告] JSONのパースに失敗: {e}. レスポンス: {summary_response.text}")
                        processed_title = f"{title} (処理失敗)"
                        summary = "記事の処理に失敗しました。元の記事をご確認ください。"
                        tags = []

                    # データベースに保存するデータを作成
                    article_data = {
                        'title': processed_title,
                        'link': link,
                        'summary': summary,
                        'tags': tags, # 生成したタグを保存
                        'published_at': pub_date,
                        'region': feed['region'],
                        'region_name': config.REGIONS[feed['region']],
                        'country_code': feed['country_code'],
                        'country_name': feed['country_name'],
                        'created_at': firestore.SERVER_TIMESTAMP
                    }
                    batch.set(article_ref, article_data, merge=True) # バッチに書き込み操作を追加
                    total_articles_saved += 1

                except Exception as e:
                    print(f"  [エラー] 記事 '{title}' の処理中にエラーが発生しました: {e}")
                    continue # この記事の処理をスキップして次に進む
            
            # サーバーに負荷をかけないように、ちょっと待つ
            print("  次の国に行く前にちょっと休憩... ☕")
            time.sleep(1)

        # ループが終わったら、バッチ処理をまとめて実行！
        if total_articles_saved > 0:
            print(f"合計 {total_articles_saved} 件の変更をFirestoreに一括コミットします。")
            batch.commit()
        return https_fn.Response(f"イケてる記事を合計 {total_articles_saved} 件GETして保存しといたよ！✨")

    except Exception as e:
        print(f"まじごめん、エラーでた: {e}")
        return https_fn.Response("内部でエラーでたわ…ごめんて🙏", status=500)
