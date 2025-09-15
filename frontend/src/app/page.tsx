"use client";
import { db } from "@/lib/firebase";
import { collection, getDocs, orderBy, query, limit, where, QuerySnapshot } from "firebase/firestore";

// Articleの型を定義しとく
type Article = {
  id: string;
  title: string;
  summary: string;
  link: string;
  published_at: string;
  category: string;
  category_name: string;
  created_at: string;
  tags?: string[]; // タグ追加
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


import { useState, useEffect } from "react";

export default function HomePage() {
  const [japanArticles, setJapanArticles] = useState<Article[]>([]);
  const [worldArticles, setWorldArticles] = useState<Article[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const articlesCollection = collection(db, "articles");
      const japanQuery = query(
        articlesCollection,
        where("category", "==", "japan"),
        orderBy("created_at", "desc"),
        limit(15)
      );
      const japanSnapshot = await getDocs(japanQuery);
      const japan = processSnapshot(japanSnapshot);

      const worldCategories = ["usa", "australia", "italy", "germany", "gb", "france"];
      const worldQuery = query(
        articlesCollection,
        where("category", "in", worldCategories),
        orderBy("created_at", "desc"),
        limit(30)
      );
      const worldSnapshot = await getDocs(worldQuery);
      const world = processSnapshot(worldSnapshot);

      setJapanArticles(japan);
      setWorldArticles(world);

      // 全タグ抽出（日本・海外両方から）
      const tags = Array.from(new Set([
        ...japan.flatMap(a => a.tags ?? []),
        ...world.flatMap(a => a.tags ?? [])
      ]));
      setAllTags(tags);
    };
    fetchData();
  }, []);

  // タグ選択/解除
  const handleTagClick = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  // AND検索で絞り込み
  const filterArticles = (articles: Article[]) => {
    if (selectedTags.length === 0) return articles;
    return articles.filter(a =>
      selectedTags.every(tag => a.tags?.includes(tag))
    );
  };

  const categoryFlags: { [key: string]: string } = {
    usa: "🇺🇸",
    australia: "🇦🇺",
    italy: "🇮🇹",
    germany: "🇩🇪",
    gb: "🇬🇧",
    france: "🇫🇷",
  };

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
        {/* タグ表示 */}
        <div className="flex flex-wrap gap-2 mt-2">
          {article.tags?.map(tag => (
            <span key={tag} className="px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-bold">{tag}</span>
          ))}
        </div>
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
        {/* タグ一覧表示＆複数選択UI */}
        <div className="mb-8">
          <h3 className="text-lg font-bold mb-2">タグで絞り込み♡</h3>
          <div className="flex flex-wrap gap-2">
            {allTags.map(tag => (
              <button
                key={tag}
                className={`px-3 py-1 rounded-full border font-bold text-xs transition-colors ${selectedTags.includes(tag) ? 'bg-amber-700 text-white border-amber-700' : 'bg-amber-100 text-amber-700 border-amber-200'}`}
                onClick={() => handleTagClick(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* 日本のニュースセクション */}
          <section>
            <h2 className="text-2xl font-serif font-bold text-stone-800 border-b-2 border-amber-700 pb-2 mb-6">
              日本の新着ニュース
            </h2>
            <div className="grid gap-6 md:gap-8">
              {filterArticles(japanArticles).length > 0 ? (
                filterArticles(japanArticles).map((article) => <ArticleCard key={article.id} article={article} />)
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
              {filterArticles(worldArticles).length > 0 ? (
                filterArticles(worldArticles).map((article) => <ArticleCard key={article.id} article={article} />)
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
