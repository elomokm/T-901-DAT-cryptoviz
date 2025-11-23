/**
 * Custom SWR hooks for data fetching with intelligent caching
 */
import useSWR from 'swr';
import { getBootstrap, getNews } from './api';
import { CoinSummary, GlobalStats, FearGreedResponse, NewsArticle } from '@/types';

interface BootstrapResponse {
  coins: CoinSummary[];
  global: GlobalStats | null;
  fearGreed: FearGreedResponse | null;
  stale?: boolean;
  rate_limited?: boolean;
}

/**
 * Hook for fetching bootstrap data (coins + global stats + fear/greed)
 * Uses SWR for intelligent caching and auto-revalidation
 */
export function useBootstrap(limit: number = 50, sparkline: boolean = true) {
  const { data, error, isLoading, mutate } = useSWR(
    `/bootstrap?limit=${limit}&sparkline=${sparkline}`,
    () => getBootstrap(limit, sparkline),
    {
      refreshInterval: 60000, // Refresh every 60s
      revalidateOnFocus: false,
      dedupingInterval: 30000, // Dedupe requests within 30s
    }
  );

  return {
    coins: data?.coins || [],
    global: data?.global || null,
    fearGreed: data?.fearGreed || null,
    isLoading,
    isError: error,
    stale: data?.stale || false,
    rateLimited: data?.rate_limited || false,
    mutate,
  };
}

/**
 * Hook for fetching news articles
 */
export function useNews(pageSize: number = 10) {
  const { data, error, isLoading } = useSWR(
    `/news?page_size=${pageSize}`,
    () => getNews({ page_size: pageSize }),
    {
      refreshInterval: 300000, // Refresh every 5 min
      revalidateOnFocus: false,
    }
  );

  return {
    articles: data?.articles || [],
    total: data?.total || 0,
    isLoading,
    isError: error,
  };
}
