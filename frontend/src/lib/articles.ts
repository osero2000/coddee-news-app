import { db } from "@/lib/firebase";
import {
  collection,
  getDocs,
  orderBy,
  query,
  limit,
  where,
  QuerySnapshot,
} from "firebase/firestore";

// Articleの型をpage.tsxからコピー
export type Article = {
  id: string;
  title: string;
  summary: string;
  link: string;
  published_at: string;
  region: string;
  region_name: string;
  country_code: string;
  country_name: string;
  created_at: string;
  tags?: string[];
};

// FirestoreのデータをArticle型に変換するヘルパー関数
const processSnapshot = (snapshot: QuerySnapshot): Article[] => {
  return snapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      id: doc.id,
      ...data,
      published_at: data.published_at
        ? (typeof data.published_at.toDate === 'function'
          ? data.published_at.toDate()
          : new Date(data.published_at)
        ).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
        : '公開日時不明',
      created_at: data.created_at
        ? data.created_at.toDate().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
        : '取得日時不明',
    } as Article;
  });
};

const MAX_JAPAN_ARTICLES_COUNT = 15;
const MAX_US_ARTICLES_COUNT = 15;
const MAX_OTHER_REGIONS_ARTICLES_COUNT = 50;

export const getArticles = async () => {
  const articlesCollection = collection(db, "articles");

  // Promise.allを使用して、日本と海外のニュース取得を並列実行し高速化
  const [japanSnapshot, ...overseasSnapshots] = await Promise.all([
    // 日本の記事を15件取得
    getDocs(query(articlesCollection, where("region", "==", "japan"), orderBy("published_at", "desc"), limit(MAX_JAPAN_ARTICLES_COUNT))),
    // アメリカの記事を15件取得
    getDocs(query(articlesCollection, where("region", "==", "us"), orderBy("published_at", "desc"), limit(MAX_US_ARTICLES_COUNT))),
    // その他の海外リージョンの記事をそれぞれ50件ずつ取得
    ...["europe", "asia", "latin_america", "africa"].map(region =>
      getDocs(query(articlesCollection, where("region", "==", region), orderBy("published_at", "desc"), limit(MAX_OTHER_REGIONS_ARTICLES_COUNT)))
    ),
  ]);

  const japanArticles = processSnapshot(japanSnapshot);
  const overseasArticles = overseasSnapshots.flatMap(snap => processSnapshot(snap));

  // デバッグ用に各スナップショットの件数を返す
  const debugCounts = {
    japan: japanSnapshot.size,
    overseas: overseasSnapshots.reduce((acc, snap) => acc + snap.size, 0),
  };

  return { japanArticles, overseasArticles, debugCounts };
};