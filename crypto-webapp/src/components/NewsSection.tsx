import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { getNews, NewsArticle } from '@/lib/api';
import { formatRelativeTime } from '@/utils/formatters';
import { Skeleton } from './ui/skeleton';
import { ExternalLink, Newspaper } from 'lucide-react';
import { Badge } from './ui/badge';

export default function NewsSection() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const response = await getNews(10, undefined, 24);
        setNews(response.news);
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
    const interval = setInterval(fetchNews, 5 * 60 * 1000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'coindesk':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      case 'cointelegraph':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      default:
        return 'bg-primary/10 text-primary border-primary/20';
    }
  };

  if (loading) {
    return (
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="w-5 h-5" />
            Latest News
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3 pb-4 border-b border-border/50 last:border-0">
                <Skeleton className="w-16 h-16 rounded-lg flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-3 w-1/4" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="w-5 h-5" />
          Latest News
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {news.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No recent news available</p>
          ) : (
            news.map((article, index) => (
              <a
                key={index}
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex gap-3 pb-4 border-b border-border/50 last:border-0 hover:bg-secondary/20 -mx-2 px-2 py-2 rounded-lg transition-colors group"
              >
                {article.image_url && (
                  <img
                    src={article.image_url}
                    alt=""
                    className="w-16 h-16 rounded-lg object-cover flex-shrink-0 bg-secondary"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm leading-snug mb-2 group-hover:text-primary transition-colors line-clamp-2">
                    {article.title}
                  </h4>
                  {article.description && (
                    <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                      {article.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className={`text-xs ${getSourceColor(article.source)}`}>
                      {article.source}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(article.published_date)}
                    </span>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
