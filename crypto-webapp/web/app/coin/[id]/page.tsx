'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ExternalLink, Globe, TrendingUp, TrendingDown } from 'lucide-react';
import InteractiveChart from '@/components/InteractiveChart';
import { CoinHistoryResponse, Period } from '@/types';
import { getCoinHistory } from '@/lib/api';
import {
  formatPrice,
  formatLargeNumber,
  formatPercent,
  formatSupply,
  getChangeColor,
  formatRelativeTime,
} from '@/lib/utils';

export default function CoinPage() {
  const params = useParams();
  const coinId = params.id as string;

  const [coin, setCoin] = useState<CoinHistoryResponse | null>(null);
  const [period, setPeriod] = useState<Period>('7d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCoin = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getCoinHistory(coinId, period);
        setCoin(data);
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
  }, [coinId, period]);

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
      </div>

      {/* Price Chart */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Price History</h2>
          <div className="flex gap-2">
            {(['24h', '7d', '30d', '90d', '1y'] as Period[]).map((p) => (
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
        <InteractiveChart prices={coin.prices} />
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
          <p className="text-gray-300 leading-relaxed">{coin.description}</p>
          {coin.homepage && (
            <a
              href={coin.homepage}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 mt-4 text-blue-400 hover:text-blue-300 transition-colors"
            >
              <Globe className="w-4 h-4" />
              Official Website
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}
