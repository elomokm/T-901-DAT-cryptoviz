'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ExternalLink, Globe, TrendingUp, TrendingDown, Plus, X } from 'lucide-react';
import MultiChart, { ChartType } from '@/components/MultiChart';
import ChartTypeSelector from '@/components/ChartTypeSelector';
import PriceRangeBar from '@/components/PriceRangeBar';
import { CoinHistoryResponse, Period, CoinSummary } from '@/types';
import { getCoinHistory } from '@/lib/api';
import { useBootstrap } from '@/lib/hooks';
import {
  formatPrice,
  formatLargeNumber,
  formatPercent,
  formatSupply,
  getChangeColor,
  formatRelativeTime,
} from '@/lib/utils';
import ComparisonChart from '@/components/ComparisonChart';

export default function CoinPage() {
  const params = useParams();
  const coinId = params.id as string;

  const [coin, setCoin] = useState<CoinHistoryResponse | null>(null);
  const [period, setPeriod] = useState<Period>('7d');
  const [chartType, setChartType] = useState<ChartType>('line');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Comparaison multi-coins
  const [compareCoins, setCompareCoins] = useState<CoinHistoryResponse[]>([]);
  const [showCoinSelector, setShowCoinSelector] = useState(false);
  const { coins: availableCoins } = useBootstrap(100, false);
  
  // Mode silencieux: pas de warnings affichés, fallback transparent

  // Fonction pour ajouter une crypto à comparer
  const addCompareC = async (id: string) => {
    if (compareCoins.find(c => c.id === id) || id === coinId) return;
    
    try {
      const data = await getCoinHistory(id, period);
      setCompareCoins(prev => [...prev, data]);
    } catch (err) {
      console.error(`Failed to fetch ${id}:`, err);
    }
  };

  const removeCompareCoin = (id: string) => {
    setCompareCoins(prev => prev.filter(c => c.id !== id));
  };

  useEffect(() => {
    const fetchCoin = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await getCoinHistory(coinId, period);
        setCoin(data);
        
        // Log silencieux pour debug uniquement (pas de UI warnings)
        if (data.stale || data.rate_limited) {
          console.log(`[${coinId}] Using fallback data: source=${data.source}, stale=${data.stale}, rate_limited=${data.rate_limited}`);
        }
      } catch (err) {
        console.error('Error fetching coin data:', err);
        setError('Failed to load coin data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (coinId) {
      fetchCoin();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coinId, period]);

  // Refetch compare coins when period changes
  useEffect(() => {
    const refetchCompareCoins = async () => {
      const ids = compareCoins.map(c => c.id);
      if (ids.length === 0) return;

      try {
        const newData = await Promise.all(
          ids.map(id => getCoinHistory(id, period))
        );
        setCompareCoins(newData);
      } catch (err) {
        console.error('Failed to refetch compare coins:', err);
      }
    };

    refetchCompareCoins();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-32 rounded" />
        <div className="glass-card p-6">
          <div className="skeleton h-64 rounded" />
        </div>
      </div>
    );
  }

  if (error || !coin) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="glass-card p-8 text-center">
          <p className="text-red-400 mb-4">{error || 'Coin not found'}</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const priceChange = coin.price_change_percentage_24h || 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="space-y-6">
      {/* Mode silencieux: pas de banners de warning */}

      {/* Back Button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Coin Header */}
      <div className="glass-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {coin.image && (
              <img src={coin.image} alt={coin.name} className="w-12 h-12 rounded-full" />
            )}
            <div>
              <h1 className="text-2xl font-bold">{coin.name}</h1>
              <p className="text-gray-400">{coin.symbol.toUpperCase()}</p>
            </div>
            {coin.market_cap_rank && (
              <span className="px-2 py-1 bg-gray-700 rounded text-sm">
                Rank #{coin.market_cap_rank}
              </span>
            )}
          </div>

          <div className="flex items-end gap-4">
            <div className="text-right">
              <p className="text-3xl font-bold">{formatPrice(coin.current_price)}</p>
              <div className={`flex items-center justify-end gap-1 ${getChangeColor(priceChange)}`}>
                {isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span>{formatPercent(priceChange)}</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* 24h Price Range */}
        {coin.low_24h && coin.high_24h && (
          <div className="mt-6">
            <PriceRangeBar
              low={coin.low_24h}
              high={coin.high_24h}
              current={coin.current_price}
            />
          </div>
        )}
      </div>

      {/* Price Chart */}
      <div className="glass-card p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">
              {compareCoins.length > 0 ? 'Comparaison' : 'Price History'}
            </h2>
            {compareCoins.length === 0 && (
              <ChartTypeSelector selected={chartType} onChange={setChartType} />
            )}
          </div>
          <div className="flex gap-2 flex-wrap">
            {(['1h', '24h', '7d', '30d', '90d', '1y'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  period === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Coin selector for comparison */}
        <div className="mb-4">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <button
              onClick={() => setShowCoinSelector(!showCoinSelector)}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Comparer
            </button>
            
            {compareCoins.map((compareCoin) => (
              <div
                key={compareCoin.id}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 rounded text-sm"
              >
                <span>{compareCoin.name}</span>
                <button
                  onClick={() => removeCompareCoin(compareCoin.id)}
                  className="hover:text-red-400 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          {showCoinSelector && (
            <div className="glass-card p-3 max-h-60 overflow-y-auto">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {availableCoins
                  .filter(c => c.id !== coinId && !compareCoins.find(cc => cc.id === c.id))
                  .slice(0, 20)
                  .map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        addCompareC(c.id);
                        setShowCoinSelector(false);
                      }}
                      className="flex items-center gap-2 p-2 hover:bg-gray-700 rounded text-sm text-left transition-colors"
                    >
                      {c.image && (
                        <img src={c.image} alt={c.name} className="w-5 h-5 rounded-full" />
                      )}
                      <span className="truncate">{c.name}</span>
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>

        {compareCoins.length > 0 ? (
          <ComparisonChart 
            coinsData={[coin, ...compareCoins]}
            mainCoinId={coinId}
          />
        ) : (
          <MultiChart 
            data={coin.prices} 
            type={chartType}
            color={priceChange >= 0 ? '#10b981' : '#ef4444'}
            name={coin.name}
          />
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Market Stats */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Market Stats</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Market Cap</span>
              <span className="font-medium">{formatLargeNumber(coin.market_cap)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">24h Volume</span>
              <span className="font-medium">{formatLargeNumber(coin.total_volume)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">24h High</span>
              <span className="font-medium">{formatPrice(coin.high_24h)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">24h Low</span>
              <span className="font-medium">{formatPrice(coin.low_24h)}</span>
            </div>
          </div>
        </div>

        {/* Supply Stats */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Supply</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Circulating</span>
              <span className="font-medium">
                {formatSupply(coin.circulating_supply, coin.symbol)}
              </span>
            </div>
            {coin.total_supply && (
              <div className="flex justify-between">
                <span className="text-gray-400">Total</span>
                <span className="font-medium">{formatSupply(coin.total_supply, coin.symbol)}</span>
              </div>
            )}
            {coin.max_supply && (
              <div className="flex justify-between">
                <span className="text-gray-400">Max</span>
                <span className="font-medium">{formatSupply(coin.max_supply, coin.symbol)}</span>
              </div>
            )}
          </div>
        </div>

        {/* All Time Stats */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">All Time</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">ATH</span>
              <span className="font-medium">{formatPrice(coin.ath)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">ATH Change</span>
              <span className={`font-medium ${getChangeColor(coin.ath_change_percentage)}`}>
                {formatPercent(coin.ath_change_percentage)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">ATH Date</span>
              <span className="font-medium">{formatRelativeTime(coin.ath_date)}</span>
            </div>
            {coin.atl && (
              <>
                <div className="flex justify-between">
                  <span className="text-gray-400">ATL</span>
                  <span className="font-medium">{formatPrice(coin.atl)}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Description */}
      {coin.description && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-4">About {coin.name}</h3>
          <p className="text-gray-300 leading-relaxed line-clamp-4">{coin.description}</p>
          
          {/* Links Section */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {coin.homepage && (
              <a
                href={coin.homepage}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
              >
                <Globe className="w-4 h-4 text-blue-400" />
                <span className="text-sm">Official Website</span>
                <ExternalLink className="w-3 h-3 ml-auto text-gray-400" />
              </a>
            )}
            
            {coin.whitepaper && (
              <a
                href={coin.whitepaper}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-sm">Whitepaper</span>
                <ExternalLink className="w-3 h-3 ml-auto text-gray-400" />
              </a>
            )}
            
            {coin.blockchain_site && coin.blockchain_site.length > 0 && (
              <>
                {coin.blockchain_site.slice(0, 2).map((site, idx) => (
                  <a
                    key={idx}
                    href={site}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <span className="text-sm">Explorer {idx + 1}</span>
                    <ExternalLink className="w-3 h-3 ml-auto text-gray-400" />
                  </a>
                ))}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
