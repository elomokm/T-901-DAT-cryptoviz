'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, TrendingUp, TrendingDown, Activity, DollarSign, BarChart3, Coins } from 'lucide-react';
import { getCoin, ApiError } from '@/lib/api';
import type { CoinSummary } from '@/types';
import { formatPrice, formatLargeNumber, formatPercent, formatSupply, getChangeColor, cn } from '@/lib/utils';
import CoinHistoryClient from '@/components/CoinHistoryClient';

export default function CoinDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [coin, setCoin] = useState<CoinSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    let mounted = true;

    async function fetchCoin() {
      try {
        setLoading(true);
        const data = await getCoin(id);
        if (mounted) {
          setCoin(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError('Failed to load coin data');
          }
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchCoin();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchCoin, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [id]);

  if (loading) {
    return (
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="animate-pulse space-y-6">
          {/* Back button skeleton */}
          <div className="h-6 w-24 bg-gray-800/50 rounded" />

          {/* Header skeleton */}
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gray-800/50 rounded-full" />
            <div className="space-y-2">
              <div className="h-8 w-48 bg-gray-800/50 rounded" />
              <div className="h-4 w-24 bg-gray-800/50 rounded" />
            </div>
          </div>

          {/* Price skeleton */}
          <div className="h-12 w-64 bg-gray-800/50 rounded" />

          {/* Chart skeleton */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-6">
            <div className="h-48 bg-gray-800/50 rounded" />
          </div>

          {/* Stats skeleton */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
                <div className="h-4 w-20 bg-gray-800/50 rounded mb-2" />
                <div className="h-6 w-28 bg-gray-800/50 rounded" />
              </div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-6 py-8 text-center">
          <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Coin</h2>
          <p className="text-gray-400">{error}</p>
        </div>
      </main>
    );
  }

  if (!coin) {
    return (
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl px-6 py-8 text-center">
          <p className="text-gray-400">Coin not found</p>
        </div>
      </main>
    );
  }

  const change24h = coin.change_24h ?? 0;
  const isPositive = change24h >= 0;

  return (
    <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center text-white font-bold text-lg">
            {coin.symbol.charAt(0)}
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{coin.name}</h1>
            <p className="text-gray-400 uppercase">{coin.symbol}</p>
          </div>
          {coin.market_cap_rank && (
            <span className="px-2 py-1 rounded bg-gray-800/70 text-gray-400 text-sm">
              Rank #{coin.market_cap_rank}
            </span>
          )}
        </div>
      </div>

      {/* Current Price */}
      <div className="flex items-baseline gap-4">
        <span className="text-3xl sm:text-4xl font-bold text-white">
          {formatPrice(coin.price_usd)}
        </span>
        <span className={cn('flex items-center gap-1 text-lg font-medium', getChangeColor(change24h))}>
          {isPositive ? (
            <TrendingUp className="w-5 h-5" />
          ) : (
            <TrendingDown className="w-5 h-5" />
          )}
          {formatPercent(change24h)}
        </span>
      </div>

      {/* Price Chart */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-4">Price History</h2>
        <CoinHistoryClient id={id} />
      </section>

      {/* Changes */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-4">Price Changes</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <p className="text-sm text-gray-400 mb-1">1 Hour</p>
            <p className={cn('text-lg font-semibold', getChangeColor(coin.change_1h))}>
              {formatPercent(coin.change_1h)}
            </p>
          </div>
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <p className="text-sm text-gray-400 mb-1">24 Hours</p>
            <p className={cn('text-lg font-semibold', getChangeColor(coin.change_24h))}>
              {formatPercent(coin.change_24h)}
            </p>
          </div>
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <p className="text-sm text-gray-400 mb-1">7 Days</p>
            <p className={cn('text-lg font-semibold', getChangeColor(coin.change_7d))}>
              {formatPercent(coin.change_7d)}
            </p>
          </div>
        </div>
      </section>

      {/* Market Stats */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-4">Market Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Market Cap */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-400">Market Cap</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatLargeNumber(coin.market_cap)}
            </p>
          </div>

          {/* Volume 24h */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-400">Volume (24h)</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatLargeNumber(coin.volume_24h)}
            </p>
          </div>

          {/* ATH */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <p className="text-sm text-gray-400">All-Time High</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatPrice(coin.ath)}
            </p>
            {coin.ath_change_pct !== undefined && (
              <p className={cn('text-xs mt-1', getChangeColor(coin.ath_change_pct))}>
                {formatPercent(coin.ath_change_pct)} from ATH
              </p>
            )}
          </div>

          {/* ATL */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-4 h-4 text-red-500" />
              <p className="text-sm text-gray-400">All-Time Low</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatPrice(coin.atl)}
            </p>
            {coin.atl_change_pct !== undefined && (
              <p className={cn('text-xs mt-1', getChangeColor(coin.atl_change_pct))}>
                {formatPercent(coin.atl_change_pct)} from ATL
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Supply Info */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-4">Supply Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Circulating Supply */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Coins className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-400">Circulating Supply</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatSupply(coin.circulating_supply, coin.symbol)}
            </p>
            {coin.max_supply && coin.circulating_supply && (
              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progress</span>
                  <span>{((coin.circulating_supply / coin.max_supply) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(coin.circulating_supply / coin.max_supply) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Total Supply */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-400">Total Supply</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {formatSupply(coin.total_supply, coin.symbol)}
            </p>
          </div>

          {/* Max Supply */}
          <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Coins className="w-4 h-4 text-gray-400" />
              <p className="text-sm text-gray-400">Max Supply</p>
            </div>
            <p className="text-lg font-semibold text-white">
              {coin.max_supply ? formatSupply(coin.max_supply, coin.symbol) : '∞'}
            </p>
          </div>
        </div>
      </section>

      {/* Last Updated */}
      <p className="text-xs text-gray-500 text-center">
        Last updated: {new Date(coin.last_updated).toLocaleString()}
      </p>
    </main>
  );
}
