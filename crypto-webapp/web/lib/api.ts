import {
  CoinSummary,
  GlobalStats,
  CoinHistoryResponse,
  NewsResponse,
  FearGreedResponse,
  Period,
  CryptoAnalytics,
  ComparisonResult,
} from '@/types';

// API base URL
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Custom API error class
export class ApiError extends Error {
  status: number;
  endpoint: string;

  constructor(message: string, status: number, endpoint: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.endpoint = endpoint;
  }
}

// Fetch with timeout
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = 10000
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('Request timeout', 408, url);
    }
    throw error;
  }
}

// Generic API fetch function
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetchWithTimeout(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Ignore JSON parse errors
      }
      throw new ApiError(errorMessage, response.status, endpoint);
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error) {
      throw new ApiError(error.message, 0, endpoint);
    }
    throw new ApiError('Unknown error occurred', 0, endpoint);
  }
}

/**
 * Get global market statistics
 */
export async function getGlobal(): Promise<GlobalStats> {
  return apiFetch<GlobalStats>('/api/v1/global');
}

/**
 * Get list of coins with optional pagination and filtering
 */
export async function getCoins(params?: {
  page?: number;
  per_page?: number;
  order?: string;
  sparkline?: boolean;
}): Promise<CoinSummary[]> {
  const searchParams = new URLSearchParams();

  if (params?.page) searchParams.append('page', params.page.toString());
  if (params?.per_page) searchParams.append('limit', params.per_page.toString()); // Changed from per_page to limit
  if (params?.order) searchParams.append('order', params.order);
  if (params?.sparkline !== undefined) {
    searchParams.append('sparkline', params.sparkline.toString());
  }

  const query = searchParams.toString();
  const response = await apiFetch<{ coins: CoinSummary[], total: number, page: number, limit: number, total_pages: number }>(`/api/v1/coins${query ? `?${query}` : ''}`);
  return response.coins; // Extract coins array from paginated response
}

/**
 * Get detailed information for a specific coin
 */
export async function getCoin(id: string): Promise<CoinHistoryResponse> {
  return apiFetch<CoinHistoryResponse>(`/api/v1/coins/${id}`);
}

/**
 * Get historical price data for a coin
 */
export async function getCoinHistory(
  id: string,
  period: Period = '7d'
): Promise<CoinHistoryResponse> {
  // Map frontend period to backend parameters
  const periodToParams: Record<Period, { days?: number; hours?: number; interval: string }> = {
    '1h': { hours: 1, interval: '5m' },
    '24h': { days: 1, interval: '1h' },
    '7d': { days: 7, interval: '4h' },
    '30d': { days: 30, interval: '1d' },
    '90d': { days: 90, interval: '1d' },
    '1y': { days: 365, interval: '1d' },
    'all': { days: 365 * 5, interval: '1d' }  // 5 years for "all"
  };
  
  const params = periodToParams[period] || { days: 7, interval: '4h' };
  const searchParams = new URLSearchParams();
  
  if (params.hours) {
    searchParams.append('hours', params.hours.toString());
    searchParams.append('days', '0');
  } else if (params.days) {
    searchParams.append('days', params.days.toString());
  }
  searchParams.append('interval', params.interval);
  
  return apiFetch<CoinHistoryResponse>(`/api/v1/coins/${id}/history?${searchParams.toString()}`);
}

/**
 * Get crypto news articles
 */
export async function getNews(params?: {
  page?: number;
  page_size?: number;
  source?: string;
  search?: string;
}): Promise<NewsResponse> {
  const searchParams = new URLSearchParams();

  if (params?.page) searchParams.append('page', params.page.toString());
  if (params?.page_size) searchParams.append('limit', params.page_size.toString()); // Changed to limit
  if (params?.source) searchParams.append('source', params.source);
  if (params?.search) searchParams.append('search', params.search);

  const query = searchParams.toString();
  const articles = await apiFetch<any[]>(`/api/v1/news${query ? `?${query}` : ''}`);
  
  // Transform API response to match NewsResponse interface
  return {
    articles: articles.map(article => ({
      id: article.link, // Use link as ID since API doesn't provide one
      title: article.title,
      description: article.description || '',
      url: article.link,
      source: article.source,
      image_url: article.image_url,
      published_at: article.published_date,
      sentiment: undefined // Not provided by API yet
    })),
    total: articles.length,
    page: params?.page || 1,
    page_size: params?.page_size || articles.length
  };
}

/**
 * Get available news sources
 */
export async function getNewsSources(): Promise<string[]> {
  return apiFetch<string[]>('/api/v1/news/sources');
}

/**
 * Get Fear & Greed Index
 */
export async function getFearGreed(): Promise<FearGreedResponse> {
  return apiFetch<FearGreedResponse>('/api/v1/fear-greed');
}

/**
 * Search for coins by name or symbol
 */
export async function searchCoins(query: string): Promise<CoinSummary[]> {
  return apiFetch<CoinSummary[]>(`/api/v1/search?q=${encodeURIComponent(query)}`);
}

/**
 * Get analytics for specific cryptos
 */
export async function getAnalytics(params?: {
  crypto_ids?: string[];
  limit?: number;
}): Promise<CryptoAnalytics[]> {
  const searchParams = new URLSearchParams();
  
  if (params?.crypto_ids && params.crypto_ids.length > 0) {
    searchParams.append('crypto_ids', params.crypto_ids.join(','));
  }
  if (params?.limit) {
    searchParams.append('limit', params.limit.toString());
  }
  
  const query = searchParams.toString();
  return apiFetch<CryptoAnalytics[]>(`/api/v1/analytics${query ? `?${query}` : ''}`);
}

/**
 * Compare multiple cryptocurrencies
 */
export async function compareCryptos(
  cryptoIds: string[],
  period: '1h' | '24h' | '7d' | '30d' = '24h'
): Promise<ComparisonResult> {
  const searchParams = new URLSearchParams();
  searchParams.append('crypto_ids', cryptoIds.join(','));
  searchParams.append('period', period);
  
  return apiFetch<ComparisonResult>(`/api/v1/analytics/compare?${searchParams.toString()}`);
}

/**
 * Get top volatile cryptocurrencies
 */
export async function getTopVolatile(limit: number = 10): Promise<CryptoAnalytics[]> {
  return apiFetch<CryptoAnalytics[]>(`/api/v1/analytics/top-volatile?limit=${limit}`);
}
