/**
 * Client API pour CryptoViz
 * Gestion des appels avec timeout, erreurs et types stricts
 */

import type {
  CoinSummary,
  GlobalStats,
  CoinHistoryResponse,
  NewsResponse,
  FearGreedResponse,
  NewsSourcesResponse,
  OrderOption,
} from '@/types';

// Configuration
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const DEFAULT_TIMEOUT = 10000; // 10 secondes

// Classe d'erreur personnalisée
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public endpoint?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Fonction fetch avec timeout
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Fonction générique pour les appels API
async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetchWithTimeout(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new ApiError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        endpoint
      );
    }

    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiError(`Request timeout for ${endpoint}`, undefined, endpoint);
      }
      throw new ApiError(error.message, undefined, endpoint);
    }

    throw new ApiError('Unknown error occurred', undefined, endpoint);
  }
}

/**
 * Récupère les stats globales du marché
 */
export async function getGlobal(): Promise<GlobalStats> {
  return fetchJson<GlobalStats>('/global');
}

/**
 * Récupère la liste des cryptomonnaies
 */
export async function getCoins(
  limit: number = 50,
  page: number = 1,
  order: OrderOption = 'market_cap_desc'
): Promise<CoinSummary[]> {
  return fetchJson<CoinSummary[]>(`/coins?limit=${limit}&page=${page}&order=${order}`);
}

/**
 * Récupère les détails d'une crypto
 */
export async function getCoin(id: string): Promise<CoinSummary> {
  if (!id || id.trim() === '') {
    throw new ApiError('Coin ID is required', 400, `/coins/${id}`);
  }
  return fetchJson<CoinSummary>(`/coins/${encodeURIComponent(id)}`);
}

/**
 * Récupère l'historique des prix d'une crypto
 */
export async function getCoinHistory(
  id: string,
  days: number = 7,
  interval: string = '1h'
): Promise<CoinHistoryResponse> {
  if (!id || id.trim() === '') {
    throw new ApiError('Coin ID is required', 400, `/coins/${id}/history`);
  }
  return fetchJson<CoinHistoryResponse>(
    `/coins/${encodeURIComponent(id)}/history?days=${days}&interval=${interval}`
  );
}

/**
 * Récupère les actualités crypto
 */
export async function getNews(
  limit: number = 20,
  source?: string,
  hours: number = 24
): Promise<NewsResponse> {
  let url = `/news?limit=${limit}&hours=${hours}`;
  if (source && source.trim() !== '') {
    url += `&source=${encodeURIComponent(source)}`;
  }
  return fetchJson<NewsResponse>(url);
}

/**
 * Récupère les sources de news disponibles
 */
export async function getNewsSources(): Promise<NewsSourcesResponse> {
  return fetchJson<NewsSourcesResponse>('/news/sources');
}

/**
 * Récupère l'index Fear & Greed
 */
export async function getFearGreed(): Promise<FearGreedResponse> {
  return fetchJson<FearGreedResponse>('/fear-greed');
}

/**
 * Vérifie la santé de l'API
 */
export async function checkHealth(): Promise<{ status: string }> {
  return fetchJson<{ status: string }>('/health');
}

// Export des types pour commodité
export type {
  CoinSummary,
  GlobalStats,
  CoinHistoryResponse,
  NewsResponse,
  NewsArticle,
  FearGreedResponse,
  PricePoint,
} from '@/types';
