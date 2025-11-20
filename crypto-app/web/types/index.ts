/**
 * Types centralisés pour CryptoViz
 */

// Prix/valeur dans le temps
export interface PricePoint {
  time: string;
  value: number;
}

// Résumé d'une cryptomonnaie
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

// Stats globales du marché
export interface GlobalStats {
  total_market_cap: number;
  total_volume_24h: number;
  market_cap_change_24h?: number;
  count: number;
}

// Historique d'une crypto
export interface CoinHistoryResponse {
  id: string;
  days: number;
  interval: string;
  series: PricePoint[];
}

// Article d'actualité
export interface NewsArticle {
  title: string;
  link: string;
  published_date: string;
  source: string;
  description?: string;
  image_url?: string;
}

// Réponse liste d'actualités
export interface NewsResponse {
  count: number;
  news: NewsArticle[];
}

// Fear & Greed Index
export interface FearGreedResponse {
  value: number;
  time: string;
  source: string;
  measurement: string;
}

// Source de news
export interface NewsSource {
  id: string;
  name: string;
  url: string;
}

// Réponse sources de news
export interface NewsSourcesResponse {
  sources: NewsSource[];
}

// Données pour le tableau
export interface CryptoTableData {
  rank: number;
  id: string;
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  change_7d: number;
  volume_24h: number;
  market_cap: number;
}

// Options de tri
export type SortField = 'rank' | 'name' | 'price' | 'change_24h' | 'change_7d' | 'volume_24h' | 'market_cap';
export type SortDirection = 'asc' | 'desc';

// Options d'ordre API
export type OrderOption =
  | 'market_cap_desc'
  | 'market_cap_asc'
  | 'price_desc'
  | 'price_asc'
  | 'volume_desc'
  | 'volume_asc';

// Périodes pour historique
export type Period = '1d' | '7d' | '30d' | '365d';

// Mapping période vers jours
export const PERIOD_DAYS: Record<Period, number> = {
  '1d': 1,
  '7d': 7,
  '30d': 30,
  '365d': 365,
};

// Mapping période vers intervalle
export const PERIOD_INTERVALS: Record<Period, string> = {
  '1d': '5m',
  '7d': '1h',
  '30d': '4h',
  '365d': '1d',
};
