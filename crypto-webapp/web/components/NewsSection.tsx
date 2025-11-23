'use client';

import { Newspaper, ExternalLink, Clock } from 'lucide-react';
import { NewsResponse, NewsArticle } from '@/types';
import { formatRelativeTime, truncateText } from '@/lib/utils';

interface NewsSectionProps {
  news: NewsResponse | null;
  loading?: boolean;
}

export default function NewsSection({ news, loading }: NewsSectionProps) {
  if (loading) {
    return (
      <div className="glass-card h-full">
        <div className="p-4 border-b border-gray-800/60">
          <div className="skeleton h-6 w-32 rounded" />
        </div>
        <div className="p-4 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="skeleton h-4 w-full rounded" />
              <div className="skeleton h-4 w-3/4 rounded" />
              <div className="skeleton h-3 w-24 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const articles = news?.articles || [];

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="p-4 border-b border-gray-800/60 flex items-center gap-2">
        <Newspaper className="w-4 h-4 text-blue-400" />
        <h2 className="text-lg font-semibold">Latest News</h2>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {articles.length === 0 ? (
          <div className="p-4 text-center text-gray-400">
            No news articles available
          </div>
        ) : (
          <div className="divide-y divide-gray-800/40">
            {articles.map((article: NewsArticle) => (
              <a
                key={article.id}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 hover:bg-gray-800/30 transition-colors group"
              >
                <div className="flex gap-3">
                  {article.image_url && (
                    <img
                      src={article.image_url}
                      alt=""
                      className="w-16 h-16 rounded object-cover flex-shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm mb-1 group-hover:text-blue-400 transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    <p className="text-xs text-gray-400 mb-2 line-clamp-2">
                      {truncateText(article.description, 100)}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelativeTime(article.published_at)}
                      </span>
                      <span className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400">
                        Read more
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
