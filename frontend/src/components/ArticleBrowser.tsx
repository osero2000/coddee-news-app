"use client";

import { useState, useMemo } from "react";
import type { Article } from "@/lib/articles";

const countryFlags: { [key: string]: string } = {
  usa: "🇺🇸",
  australia: "🇦🇺",
  italy: "🇮🇹",
  germany: "🇩🇪",
  gb: "🇬🇧",
  france: "🇫🇷",
  es: "🇪🇸",
  pt: "🇵🇹",
  cn: "🇨🇳", tw: "🇹🇼", kr: "🇰🇷", vn: "🇻🇳", sg: "🇸🇬",
  brazil: "🇧🇷", colombia: "🇨🇴", cr: "🇨🇷", pa: "🇵🇦", sv: "🇸🇻", gt: "🇬🇹", mx: "🇲🇽", pe: "🇵🇪",
  et: "🇪🇹", ke: "🇰🇪", ug: "🇺🇬", rw: "🇷🇼",
};

const ArticleCard = ({ article }: { article: Article }) => (
  <article key={article.id} className="bg-white p-6 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 border border-stone-200 flex flex-col">
    <div className="flex-grow">
      {article.region !== 'japan' && (
        <div className="text-sm font-bold text-stone-500 mb-2 flex items-center gap-2">
          <span>{countryFlags[article.country_code] ?? '🌐'}</span>
          <span>{article.country_name}</span>
        </div>
      )}
      <h2 className="text-xl md:text-2xl font-bold text-stone-800 mb-3">{article.title}</h2>
      <p className="text-stone-600 leading-relaxed mb-4">{article.summary}</p>
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
      <time dateTime={article.published_at} className="text-xs text-stone-400">
        {article.published_at}
      </time>
    </div>
  </article>
);

type ArticleBrowserProps = {
  japanArticles: Article[];
  allOverseasArticles: Article[];
};

export default function ArticleBrowser({ japanArticles, allOverseasArticles }: ArticleBrowserProps) {
  const [selectedRegion, setSelectedRegion] = useState('eu_us');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const allTags = useMemo(() => {
    const tags = Array.from(new Set([
      ...japanArticles.flatMap(a => a.tags ?? []),
      ...allOverseasArticles.flatMap(a => a.tags ?? [])
    ]));
    return tags;
  }, [japanArticles, allOverseasArticles]);

  const handleTagClick = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleCountryClick = (countryCode: string) => {
    setSelectedCountries(prev =>
      prev.includes(countryCode)
        ? prev.filter(c => c !== countryCode)
        : [...prev, countryCode]
    );
  };

  const filterArticles = (articles: Article[]) => {
    if (selectedTags.length === 0) return articles;
    return articles.filter(a =>
      selectedTags.every(tag => a.tags?.includes(tag))
    );
  };

  const countriesInSelectedRegion = useMemo(() => {
    const articlesInRegion = allOverseasArticles.filter(a => a.region === selectedRegion);
    const countries = articlesInRegion.map(a => ({
      code: a.country_code,
      name: a.country_name,
    }));
    const uniqueCountries = Array.from(new Map(countries.map(c => [c.code, c])).values())
      .filter(c => c.code && c.name)
      .sort((a, b) => a.name.localeCompare(b.name, 'ja'));
    return uniqueCountries;
  }, [allOverseasArticles, selectedRegion]);

  const filteredJapanArticles = filterArticles(japanArticles);
  const filteredOverseasArticles = filterArticles(
    allOverseasArticles
      .filter(a => a.region === selectedRegion)
      .filter(a => selectedCountries.length === 0 || selectedCountries.includes(a.country_code))
  );

  return (
    <>
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
        <section>
          <h2 className="text-2xl font-serif font-bold text-stone-800 border-b-2 border-amber-700 pb-2 mb-6">
            日本の新着ニュース
          </h2>
          <div className="grid gap-6 md:gap-8">
            {filteredJapanArticles.length > 0 ? (
              filteredJapanArticles.map((article) => <ArticleCard key={article.id} article={article} />)
            ) : (
              <p className="text-stone-500">新しいニュースはありません。</p>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-serif font-bold text-stone-800 border-b-2 border-amber-700 pb-2 mb-6">
            海外のコーヒーニュース
          </h2>
          <div className="flex flex-wrap gap-2 mb-6 border-b border-stone-200 pb-4">
            {[
              { key: 'eu_us', name: '欧米' },
              { key: 'asia', name: 'アジア' },
              { key: 'latin_america', name: '中南米' },
              { key: 'africa', name: 'アフリカ' },
            ].map(region => (
              <button
                key={region.key}
                onClick={() => {
                  setSelectedRegion(region.key);
                  setSelectedCountries([]);
                }}
                className={`px-4 py-2 rounded-full font-bold text-sm transition-all ${selectedRegion === region.key ? 'bg-amber-700 text-white shadow-md' : 'bg-white text-stone-600 hover:bg-stone-100 border'}`}
              >
                {region.name}
              </button>
            ))}
          </div>

          {countriesInSelectedRegion.length > 1 && (
            <div className="mb-6">
              <div className="flex flex-wrap gap-2">
                {countriesInSelectedRegion.map(country => (
                  <button
                    key={country.code}
                    onClick={() => handleCountryClick(country.code)}
                    className={`px-3 py-1 rounded-full border text-xs font-bold transition-colors flex items-center gap-1.5 ${
                      selectedCountries.includes(country.code)
                        ? 'bg-sky-600 text-white border-sky-600'
                        : 'bg-white text-sky-700 border-sky-200 hover:bg-sky-50'
                    }`}
                  >
                    <span>{countryFlags[country.code] ?? '🌐'}</span>
                    <span>{country.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-6 md:gap-8">
            {filteredOverseasArticles.length > 0 ? (
              filteredOverseasArticles.map((article) => <ArticleCard key={article.id} article={article} />)
            ) : (
              <p className="text-stone-500">新しいニュースはありません。</p>
            )}
          </div>
        </section>
      </div>
    </>
  );
}