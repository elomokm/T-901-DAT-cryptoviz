// API Client for CryptoViz Backend

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Types
export interface PricePoint {
  time: string;
  value: number;
}

export interface CoinSummary {
  id: string;
  symbol: string;
  name: string;
  price_usd: number;
  market_cap?: number;
  market_cap_rank?: number;
  volume_24h?: number;
  change_1h?: number;
  change_24h?: number;
  change_7d?: number;
  ath?: number;
  ath_change_pct?: number;
  atl?: number;
  atl_change_pct?: number;
  circulating_supply?: number;
  total_supply?: number;
  max_supply?: number;
  last_updated: string;
  sparkline_7d?: number[] | null;
}

export interface GlobalStats {
  total_market_cap: number;
  total_volume_24h: number;
  market_cap_change_24h?: number;
  count: number;
}

export interface CoinHistoryResponse {
  id: string;
  days: number;
  interval: string;
  series: PricePoint[];
}

export interface NewsArticle {
  title: string;
  link: string;
  published_date: string;
  source: string;
  description?: string;
  image_url?: string;
}

export interface NewsResponse {
  count: number;
  news: NewsArticle[];
}

export interface FearGreedResponse {
  value: number;
  time: string;
  source: string;
  measurement: string;
}

// API Functions
export async function getGlobal(): Promise<GlobalStats> {
  const response = await fetch(`${API_BASE}/global`);
  if (!response.ok) throw new Error('Failed to fetch global stats');
  return response.json();
}

export async function getCoins(
  limit: number = 50,
  page: number = 1,
  order: string = 'market_cap_desc'
): Promise<CoinSummary[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    page: page.toString(),
    order,
  });
  const response = await fetch(`${API_BASE}/coins?${params}`);
  if (!response.ok) throw new Error('Failed to fetch coins');
  return response.json();
}

export async function getCoin(id: string): Promise<CoinSummary> {
  const response = await fetch(`${API_BASE}/coins/${id}`);
  if (!response.ok) throw new Error(`Failed to fetch coin ${id}`);
  return response.json();
}

export async function getCoinHistory(
  id: string,
  days: number = 7,
  interval: string = '1h'
): Promise<CoinHistoryResponse> {
  const params = new URLSearchParams({
    days: days.toString(),
    interval,
  });
  const response = await fetch(`${API_BASE}/coins/${id}/history?${params}`);
  if (!response.ok) throw new Error(`Failed to fetch coin history for ${id}`);
  return response.json();
}

export async function getNews(
  limit: number = 20,
  source?: string,
  hours: number = 24
): Promise<NewsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    hours: hours.toString(),
  });
  if (source) params.append('source', source);
  
  const response = await fetch(`${API_BASE}/news?${params}`);
  if (!response.ok) throw new Error('Failed to fetch news');
  return response.json();
}

export async function getFearGreed(): Promise<FearGreedResponse> {
  const response = await fetch(`${API_BASE}/fear-greed`);
  if (!response.ok) throw new Error('Failed to fetch Fear & Greed index');
  return response.json();
}
