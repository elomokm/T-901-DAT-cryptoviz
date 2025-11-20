'use client';

import { useEffect, useState } from 'react';
import { Newspaper, ExternalLink } from 'lucide-react';
import { getNews, ApiError } from '@/lib/api';
import type { NewsArticle } from '@/types';
import { formatRelativeTime, cn } from '@/lib/utils';

interface NewsSectionProps {
  limit?: number;
  hours?: number;
}

const SOURCES = [
  { id: '', label: 'All sources' },
  { id: 'coindesk', label: 'CoinDesk' },
  { id: 'cointelegraph', label: 'CoinTelegraph' },
];

export default function NewsSection({ limit = 10, hours = 24 }: NewsSectionProps) {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState('');

  useEffect(() => {
    let mounted = true;

    async function fetchNews() {
      try {
        setLoading(true);
        const response = await getNews(limit, source || undefined, hours);
        if (mounted) {
          setNews(response.news);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError('Failed to load news');
          }
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchNews();

    // Refresh news every 5 minutes
    const interval = setInterval(fetchNews, 5 * 60 * 1000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [limit, hours, source]);

  const getSourceColor = (src: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      coindesk: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
      cointelegraph: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
    };
    return colors[src] || { bg: 'bg-gray-500/20', text: 'text-gray-400' };
  };

  return (
    <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl overflow-hidden backdrop-blur-xl">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gray-800/50">
            <Newspaper className="w-5 h-5 text-gray-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Latest News</h2>
            <p className="text-xs text-gray-500">Real-time crypto updates</p>
          </div>
        </div>

        {/* Source filter */}
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="bg-gray-800/70 border border-gray-700/60 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          aria-label="Filter by source"
        >
          {SOURCES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      <div className="divide-y divide-gray-800/60 max-h-[500px] overflow-y-auto">
        {loading && news.length === 0 ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="px-6 py-4">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-800/50 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-800/50 rounded w-1/2 mb-3" />
                <div className="flex gap-2">
                  <div className="h-5 bg-gray-800/50 rounded w-20" />
                  <div className="h-5 bg-gray-800/50 rounded w-16" />
                </div>
              </div>
            </div>
          ))
        ) : error && news.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">{error}</div>
        ) : news.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            No news articles available
          </div>
        ) : (
          news.map((article, index) => {
            const sourceColor = getSourceColor(article.source);
            return (
              <a
                key={index}
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="block px-6 py-4 hover:bg-gray-800/30 transition-colors group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    {article.description && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {article.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-2">
                      <span
                        className={cn(
                          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                          sourceColor.bg,
                          sourceColor.text
                        )}
                      >
                        {article.source}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(article.published_date)}
                      </span>
                    </div>
                  </div>

                  <ExternalLink className="w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors flex-shrink-0 mt-1" />
                </div>
              </a>
            );
          })
        )}
      </div>

      {/* Footer */}
      {news.length > 0 && (
        <div className="px-6 py-3 border-t border-gray-800/60 text-center text-xs text-gray-500">
          {news.length} article{news.length !== 1 ? 's' : ''} from the last {hours}h
        </div>
      )}
    </div>
  );
}
