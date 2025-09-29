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

# Firebase Admin SDKを初期化するよ
initialize_app()

# ★超大事★ Cloud FunctionsのSecret ManagerからGeminiのAPIキーを安全に読み込む設定
options.set_global_options(secrets=["GEMINI_API_KEY"])

# この関数がURLで呼ばれたら実行される！
@https_fn.on_request(timeout_sec=540) # タイムアウトを9分に延長！
def fetch_and_summarize_articles(req: https_fn.Request) -> https_fn.Response:
    """
    Google NewsのRSSからコーヒー関連の記事を取得して、
    Geminiで要約してFirestoreに保存するHTTP関数だよん！
    Cloud Schedulerからの呼び出しを想定しているよ。
    """
    try:
        # 環境変数からAPIキーを取得してGeminiをセットアップ
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        db = firestore.client()
        model = genai.GenerativeModel('gemini-2.5-flash-lite')

        total_articles_saved = 0
        # Firestoreへの書き込みを効率化するためのバッチ処理オブジェクト
        batch = db.batch()
        # 1回の実行内で同じような記事を複数処理しないためのタイトル管理セット
        processed_title_prefixes = set()
        TITLE_PREFIX_LENGTH = 30 # タイトルの先頭何文字で重複判定するか
        # 今回の収集処理をグループ化するためのユニークID（実行開始時のタイムスタンプ）
        batch_id = int(time.time())

        # RSS取得時にボットと判定されるのを防ぐためのUser-Agentヘッダー
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 各フィードをループして処理
        for feed in config.FEEDS:
            print(f"カテゴリ '{feed['country_name']}' の記事を収集中...")
            try:
                # タイムアウトを設定して、RSSフィードの取得を試みる
                response = requests.get(feed['url'], headers=headers, timeout=15) # タイムアウトを設定
                response.raise_for_status() # HTTPエラーがあれば例外を発生
                root = ET.fromstring(response.content)
            except requests.exceptions.RequestException as e:
                print(f"  [エラー] '{feed['country_name']}' のRSSフィード取得に失敗しました: {e}")
                continue # この国の処理をスキップして次に進む
            except ET.ParseError as e:
                print(f"  [エラー] '{feed['country_name']}' のXMLパースに失敗しました: {e}")
                continue # この国の処理をスキップして次に進む

            # config.pyで国ごとに定義した取得件数を読み込む
            num_articles_to_fetch = feed['articles_to_fetch']
            # 記事の表示順を制御するためのカウンター（国ごとにリセット）
            sequence_counter = 0

            # RSSフィード内の各記事アイテムをループ処理
            for item in root.findall('.//item')[:num_articles_to_fetch]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date_str = item.find('pubDate').text

                # --- ▼▼▼ タイトルによる重複排除 ▼▼▼ ---
                title_prefix = title[:TITLE_PREFIX_LENGTH]
                if title_prefix in processed_title_prefixes:
                    print(f"  [スキップ] タイトルが類似した記事を既に処理済みです: {title}")
                    continue # この記事の処理をスキップ
                processed_title_prefixes.add(title_prefix) # 処理済みとしてセットに追加

                # Google Newsのリンクはリダイレクトされるため、最終的なURLを取得して重複チェックに利用する
                try:
                    # HEADリクエストで効率的に最終URLを取得（タイムアウトも設定）
                    head_response = requests.head(link, headers=headers, allow_redirects=True, timeout=10)
                    head_response.raise_for_status()
                    final_url = head_response.url
                except requests.exceptions.RequestException as e:
                    print(f"  [警告] 最終URLの取得に失敗しました: {e}。元のリンクをIDとして使用します。 Link: {link}")
                    final_url = link # 失敗した場合は元のリンクをそのまま使う

                # RSSの公開日時文字列をdatetimeオブジェクト（UTC）に変換
                try:
                    pub_date = parsedate_to_datetime(pub_date_str)
                except (TypeError, ValueError):
                    pub_date = datetime.now(timezone.utc) # パース失敗時は現在時刻をUTCで設定

                # 最終URLをハッシュ化してFirestoreのドキュメントIDにする（強力な重複防止！）
                doc_id = hashlib.sha256(final_url.encode('utf-8')).hexdigest()
                article_ref = db.collection('articles').document(doc_id)

                # --- ▼▼▼ データ移行期間用のお掃除機能 ▼▼▼ ---
                # 過去に`country_code`が国名（"日本"など）で保存されていた古いデータを新しい形式に更新するため、
                # 同じリンクを持つ古いドキュメントがあればバッチで削除する
                old_docs_query = db.collection('articles').where('link', '==', link)
                for old_doc in old_docs_query.stream():
                    old_data = old_doc.to_dict()
                    if len(old_data.get('country_code', '')) != 2:
                        print(f"  [クリーンアップ] 古い形式のドキュメントを削除します: {old_doc.id} (country_code: {old_data.get('country_code')})")
                        batch.delete(old_doc.reference) # バッチに削除操作を追加

                try:
                    print(f"  処理中の記事: {title}")

                    # Geminiくんに要約をお願いする！
                    prompt_text = feed['prompt'].format(title=title, link=link)
                    summary_response = model.generate_content(prompt_text)

                    try:
                        # Geminiからのレスポンスはマークダウンで返ってくることがあるので、```json ... ``` を取り除く
                        cleaned_response = summary_response.text.strip().replace("```json", "").replace("```", "")
                        result = json.loads(cleaned_response)
                        processed_title = result.get("title", title)
                        summary = result.get("summary", "要約の取得に失敗しました。") # 失敗時のデフォルト値
                        tags = result.get("tags", []) # Geminiが生成したタグを取得するよ
                    except (json.JSONDecodeError, AttributeError) as e:
                        print(f"    [警告] JSONのパースに失敗: {e}. レスポンス: {summary_response.text}")
                        processed_title = f"{title} (処理失敗)"
                        summary = "記事の処理に失敗しました。元の記事をご確認ください。"
                        tags = []

                    # Firestoreに保存する記事データを作成
                    article_data = {
                        'title': processed_title,
                        'link': link,
                        'original_link': final_url, # 最終的なURLも保存しておく
                        'summary': summary,
                        'tags': tags, # 生成したタグを保存
                        'published_at': pub_date,
                        'region': feed['region'],
                        'region_name': config.REGIONS[feed['region']],
                        'country_code': feed['country_code'],
                        'country_name': feed['country_name'],
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'batch_id': batch_id, # 収集バッチID
                        'sequence_id': sequence_counter # バッチ内での処理順
                    }
                    batch.set(article_ref, article_data, merge=True) # 存在すれば更新、なければ作成
                    total_articles_saved += 1

                except Exception as e:
                    print(f"  [エラー] 記事 '{title}' の処理中にエラーが発生しました: {e}")
                    continue # この記事の処理をスキップして次に進む
                finally:
                    # 成功・失敗に関わらずカウンターを増やす
                    sequence_counter += 1
            
            # 連続リクエストによる負荷を避けるため、国ごとに少し待機
            print("  次の国に行く前にちょっと休憩... ☕")
            time.sleep(1)

        # すべての国の処理が終わったら、溜めておいた書き込み処理を一度に実行
        if total_articles_saved > 0:
            print(f"合計 {total_articles_saved} 件の変更をFirestoreに一括コミットします。")
            batch.commit()
        return https_fn.Response(f"イケてる記事を合計 {total_articles_saved} 件GETして保存しといたよ！✨")

    except Exception as e:
        print(f"まじごめん、関数全体で予期せぬエラーが発生した: {e}")
        return https_fn.Response("内部でエラーでたわ…ごめんて🙏", status=500)