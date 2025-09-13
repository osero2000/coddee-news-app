import { db } from "@/lib/firebase";
import { collection, getDocs, orderBy, query, limit, where, QuerySnapshot } from "firebase/firestore";

// Articleの型を定義しとく
type Article = {
  id: string;
  title: string;
  summary: string;
  link: string;
  published_at: string;
  category: string; // カテゴリを柔軟に
  category_name: string; // 表示用のカテゴリ名
  created_at: string; // ★取得日時を追加
};

// FirestoreのデータをArticle型に変換するヘルパー関数
const processSnapshot = (snapshot: QuerySnapshot): Article[] => {
  return snapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      id: doc.id,
      ...data,
      created_at: data.created_at
        ? data.created_at.toDate().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
        : '取得日時不明',
    } as Article;
  });
};

export default async function HomePage() {
  const articlesCollection = collection(db, "articles");

  // 日本の記事を最新30件取得
  const japanQuery = query(articlesCollection, where("category", "==", "japan"), orderBy("created_at", "desc"), limit(30));
  
  // 海外の記事を最新30件取得
  const worldCategories = ["usa", "australia", "italy", "germany", "gb", "france"];
  const worldQuery = query(articlesCollection, where("category", "in", worldCategories), orderBy("created_at", "desc"), limit(30));

  // 日本と海外の記事を同時に取得するよ
  const [japanSnapshot, worldSnapshot] = await Promise.all([
    getDocs(japanQuery),
    getDocs(worldQuery)
  ]);

  const japanArticles = processSnapshot(japanSnapshot);
  const worldArticles = processSnapshot(worldSnapshot);

  // カテゴリごとの国旗
  const categoryFlags: { [key: string]: string } = {
    usa: "🇺🇸",
    australia: "🇦🇺",
    italy: "🇮🇹",
    germany: "🇩🇪",
    gb: "🇬🇧",
    france: "🇫🇷",
  };

  // 記事カードのコンポーネント
  const ArticleCard = ({ article }: { article: Article }) => (
    <article key={article.id} className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-stone-200 flex flex-col">
      <div className="flex-grow">
        {article.category !== 'japan' && (
          <div className="text-sm font-bold text-stone-500 mb-2 flex items-center gap-2">
            <span>{categoryFlags[article.category] ?? '🌐'}</span>
            <span>{article.category_name}</span>
          </div>
        )}
        <h2 className="text-xl md:text-2xl font-bold text-stone-800 mb-3">{article.title}</h2>
        <p className="text-stone-600 leading-relaxed mb-4">{article.summary}</p>
      </div>
      <div className="mt-auto pt-4 border-t border-stone-100 flex justify-between items-center">
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-amber-700 hover:text-amber-800 font-bold transition-colors"
        >
          元記事を読む &rarr;
        </a>
        <time dateTime={article.created_at} className="text-xs text-stone-400">
          {article.created_at} 取得
        </time>
      </div>
    </article>
  );

  return (
    <div className="bg-stone-50 min-h-screen text-stone-800">
      <header className="py-4 border-b border-stone-200 bg-white/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="container mx-auto px-6">
          <h1 className="text-3xl md:text-4xl font-serif text-stone-900">☕ Coffee News Summary  - コーヒーでつながる世界 -</h1>
          <p className="text-sm text-stone-500 mt-1">AIがまとめる世界のコーヒーニュース</p>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 md:py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          
          {/* 日本のニュースセクション */}
          <section>
            <h2 className="text-2xl font-serif font-bold text-stone-800 border-b-2 border-amber-700 pb-2 mb-6">
              日本の新着ニュース
            </h2>
            <div className="grid gap-6 md:gap-8">
              {japanArticles.length > 0 ? (
                japanArticles.map((article) => <ArticleCard key={article.id} article={article} />)
              ) : (
                <p className="text-stone-500">新しいニュースはありません。</p>
              )}
            </div>
          </section>

          {/* 海外のニュースセクション */}
          <section>
            <h2 className="text-2xl font-serif font-bold text-stone-800 border-b-2 border-amber-700 pb-2 mb-6">
              海外のコーヒーニュース
            </h2>
            <div className="grid gap-6 md:gap-8">
              {worldArticles.length > 0 ? (
                worldArticles.map((article) => <ArticleCard key={article.id} article={article} />)
              ) : (
                <p className="text-stone-500">新しいニュースはありません。</p>
              )}
            </div>
          </section>

        </div>
      </main>
      
      <footer className="text-center py-8 mt-8 border-t border-stone-200">
        <p className="text-sm text-stone-400">&copy; {new Date().getFullYear()} Coffee News. All rights reserved.</p>
      </footer>
    </div>
  );
}
