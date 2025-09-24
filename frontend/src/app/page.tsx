import { getArticles } from "@/lib/articles";
import ArticleBrowser from "@/components/ArticleBrowser";

// ISRを有効にする（キャッシュの有効期間を秒単位で指定）
// ここでは1時間 (3600秒) に設定
export const revalidate = 3600;

export default async function HomePage() {
  // サーバーサイドでデータを一度だけ取得
  const { japanArticles, overseasArticles, debugCounts } = await getArticles();

  return (
    <div className="bg-stone-50 min-h-screen text-stone-800">
      <header className="py-4 border-b border-stone-200 bg-white/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="container mx-auto px-6">
          <h1 className="text-3xl md:text-4xl font-serif text-stone-900">☕ Coffee News Summary  - コーヒーでつながる世界 -</h1>
          <p className="text-sm text-stone-500 mt-1">AIがまとめる世界のコーヒーニュース</p>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 md:py-12">
        <ArticleBrowser
          japanArticles={japanArticles}
          allOverseasArticles={overseasArticles}
          debugCounts={debugCounts}
        />
      </main>
      <footer className="text-center py-8 mt-8 border-t border-stone-200">
        <p className="text-sm text-stone-400">&copy; {new Date().getFullYear()} Coffee News. All rights reserved.</p>
      </footer>
    </div>
  );
}
