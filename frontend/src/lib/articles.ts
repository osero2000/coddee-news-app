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
  batch_id?: number; // 収集バッチID
  sequence_id?: number; // 新しいフィールドを追加
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

  // 各リージョンごとに記事を取得する関数
  const fetchArticlesForRegion = (region: string, limitCount: number) => {
    const q = query(
      articlesCollection,
      where("region", "==", region),
      orderBy("batch_id", "desc"),
      orderBy("sequence_id", "asc"),
      limit(limitCount)
    );
    return getDocs(q);
  };

  const [japanSnapshot, usSnapshot, ...otherRegionsSnapshots] = await Promise.all([
    fetchArticlesForRegion("japan", MAX_JAPAN_ARTICLES_COUNT),
    fetchArticlesForRegion("us", MAX_US_ARTICLES_COUNT),
    ...["europe", "asia", "latin_america", "africa"].map(region =>
      fetchArticlesForRegion(region, MAX_OTHER_REGIONS_ARTICLES_COUNT)
    ),
  ]);

  const japanArticles = processSnapshot(japanSnapshot);
  const overseasArticles = [
    ...processSnapshot(usSnapshot),
    ...otherRegionsSnapshots.flatMap(snap => processSnapshot(snap)),
  ];

  // デバッグ用に各スナップショットの件数を返す
  const debugCounts = {
    japan: japanSnapshot.size,
    overseas: usSnapshot.size + otherRegionsSnapshots.reduce((acc, snap) => acc + snap.size, 0),
  };

  return { japanArticles, overseasArticles, debugCounts };
};