import {
  CoinSummary,
  GlobalStats,
  CoinHistoryResponse,
  NewsResponse,
  FearGreedResponse,
  Period,
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
  // Map frontend period to backend days parameter
  const periodToDays: Record<Period, number> = {
    '24h': 1,
    '7d': 7,
    '30d': 30,
    '90d': 90,
    '1y': 365,
    'all': 365 * 5  // 5 years for "all"
  };
  
  const days = periodToDays[period] || 7;
  const interval = period === '24h' ? '1h' : period === '7d' ? '4h' : '1d';
  
  return apiFetch<CoinHistoryResponse>(`/api/v1/coins/${id}/history?days=${days}&interval=${interval}`);
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
