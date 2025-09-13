# Coffee News App

## 概要
世界中のコーヒーニュースを収集・要約し、日本語で表示するWebアプリです。Google News RSSから記事を取得し、Gemini APIで日本語要約・翻訳、Firebase Firestoreに保存、Next.jsフロントエンドで表示します。

## 構成
- **フロントエンド**: Next.js（TypeScript, Tailwind CSS）
- **バックエンド**: Firebase Functions（Python, Gemini API）
- **データベース**: Firebase Firestore
- **インフラ**: Firebase Hosting

## ディレクトリ構成
```
frontend/      # Next.jsフロントエンド
functions/     # Firebase Functions（Python）
memo/          # システム設計メモ
```

## セットアップ手順
1. **Firebaseプロジェクト作成**
2. **Firestore有効化**
3. **Gemini APIキー取得 & Firebase Functionsのsecretsに登録**
4. **依存パッケージインストール**
   - `frontend`: `npm install`
   - `functions`: `pip install -r requirements.txt`
5. **ローカル開発**
   - `frontend`: `npm run dev`
   - `functions`: `firebase emulators:start`
6. **Firebaseデプロイ**
   - `firebase deploy`
7. **Vercelで公開**
   - VercelにGitHubリポジトリを連携し、`frontend`ディレクトリをプロジェクトルートとして設定
   - 環境変数（Firebase設定など）をVercelのダッシュボードで登録
   - プッシュで自動デプロイ

## 主要ファイル
- `frontend/src/app/page.tsx` : 記事一覧表示
- `frontend/src/lib/firebase.ts` : Firestore連携
- `functions/main.py` : ニュース収集・要約・保存

## 運用・開発・セキュリティのポイント
- Cloud Scheduler等で定期実行（OCI認証付き）を推奨。外部からのFunctions実行は認証で保護。
- Firestoreのセキュリティルールは「articlesコレクションのみ誰でも読み取りOK、書き込みはFunctionsのみ」。クライアントからの書き込みは完全禁止。
- APIキー（Gemini/Firebase）はsecretsや.envで厳重管理。`.gitignore`で漏洩防止。
- ニュースソースはGoogle News RSSのみ。信頼性が高いため、Firestore保存時のバリデーションやXSS対策は最低限でOK。
   （他ソース追加時はバリデーション・サニタイズ強化推奨）
- CORS設定は現状不要（OIDC認証で外部アクセス不可）。将来フロントから直接APIを呼ぶ場合は、必要なオリジンのみ許可。
- 記事カテゴリ追加は`main.py`のRSSリスト編集で対応。

## ライセンス
MIT
