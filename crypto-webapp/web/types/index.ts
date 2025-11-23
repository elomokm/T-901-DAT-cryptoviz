// Price data point for sparklines and charts
export interface PricePoint {
  timestamp: string;
  price: number;
}

// Summary data for a cryptocurrency
export interface CoinSummary {
  id: string;
  symbol: string;
  name: string;
  image?: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  total_volume: number;
  price_change_percentage_24h: number;
  price_change_percentage_7d?: number;
  circulating_supply: number;
  total_supply?: number;
  max_supply?: number;
  ath: number;
  ath_change_percentage: number;
  ath_date: string;
  sparkline_in_7d?: PricePoint[];
}

// Global market statistics
export interface GlobalStats {
  total_market_cap: number;
  total_volume: number;
  market_cap_percentage: {
    btc: number;
    eth: number;
  };
  market_cap_change_percentage_24h: number;
  active_cryptocurrencies: number;
  markets: number;
}

// Detailed coin history response
export interface CoinHistoryResponse {
  id: string;
  symbol: string;
  name: string;
  image?: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  total_volume: number;
  high_24h: number;
  low_24h: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  price_change_percentage_7d?: number;
  price_change_percentage_30d?: number;
  circulating_supply: number;
  total_supply?: number;
  max_supply?: number;
  ath: number;
  ath_change_percentage: number;
  ath_date: string;
  atl: number;
  atl_change_percentage: number;
  atl_date: string;
  description?: string;
  homepage?: string;
  whitepaper?: string;
  blockchain_site?: string[];
  prices: PricePoint[];
  // Multi-source metadata
  stale?: boolean;
  rate_limited?: boolean;
  source?: string;
  method?: string;
  spread_pct?: number;
  cmc_validated?: boolean;
}

// News article
export interface NewsArticle {
  id: string;
  title: string;
  description: string;
  url: string;
  source: string;
  image_url?: string;
  published_at: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
}

// News response
export interface NewsResponse {
  articles: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
}

// Fear and Greed Index response
export interface FearGreedResponse {
  value: number;
  value_classification: string;
  timestamp: string;
  time_until_update?: string;
}

// Crypto table data (extended CoinSummary for table display)
export interface CryptoTableData extends CoinSummary {
  isLoading?: boolean;
}

// Sort configuration
export type SortField =
  | 'market_cap_rank'
  | 'current_price'
  | 'price_change_percentage_24h'
  | 'price_change_percentage_7d'
  | 'market_cap'
  | 'total_volume';

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

// Order option for dropdowns
export interface OrderOption {
  value: SortField;
  label: string;
}

// Time period for charts
export type Period = '1h' | '24h' | '7d' | '30d' | '90d' | '1y' | 'all';

export interface PeriodOption {
  value: Period;
  label: string;
}

// API error response
export interface ApiErrorResponse {
  detail: string;
  status_code?: number;
}

// Toast notification
export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

// Fear and Greed classification
export interface FearGreedClassification {
  label: string;
  color: string;
  bgColor: string;
  textColor: string;
}

// Analytics data for a cryptocurrency
export interface CryptoAnalytics {
  crypto_id: string;
  symbol: string;
  name: string;
  price_mean: number;
  price_std: number;
  price_min: number;
  price_max: number;
  price_range: number;
  volatility_pct: number;
  volume_mean: number;
  volume_std: number;
  anomaly_count: number;
  data_points: number;
  timestamp: string;
}

// Comparison result
export interface ComparisonResult {
  cryptos: CryptoAnalytics[];
  period: string;
  comparison_time: string;
  rankings: {
    most_volatile: string[];
    highest_volume: string[];
    highest_price: string[];
  };
}

// Comparison criteria
export type ComparisonCriterion = 
  | 'volatility' 
  | 'volume' 
  | 'price' 
  | 'price_range' 
  | 'anomalies';

export interface ComparisonCriterionOption {
  value: ComparisonCriterion;
  label: string;
  description: string;
}
