'use client';

import { useEffect, useState, useCallback } from 'react';
import Header from '@/components/layout/Header';
import GlobalStatsCards from '@/components/GlobalStatsCards';
import FearGreedGauge from '@/components/FearGreedGauge';
import CryptoTable from '@/components/CryptoTable';
import NewsSection from '@/components/NewsSection';
import { getGlobal, getCoins, ApiError } from '@/lib/api';
import type { GlobalStats, CoinSummary, CryptoTableData } from '@/types';

export default function Home() {
  const [global, setGlobal] = useState<GlobalStats | null>(null);
  const [coins, setCoins] = useState<CoinSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchData = useCallback(async (showRefreshing = false) => {
    try {
      if (showRefreshing) setIsRefreshing(true);

      const [globalData, coinsData] = await Promise.all([
        getGlobal(),
        getCoins(100, 1, 'market_cap_desc'),
      ]);

      setGlobal(globalData);
      setCoins(coinsData);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load data');
      }
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => fetchData(false), 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleRefresh = () => {
    fetchData(true);
  };

  // Transform coins to table data
  const tableData: CryptoTableData[] = coins.map((c, idx) => ({
    rank: c.market_cap_rank ?? idx + 1,
    id: c.id,
    symbol: c.symbol,
    name: c.name,
    price: c.price_usd,
    change_24h: c.change_24h ?? 0,
    change_7d: c.change_7d ?? 0,
    volume_24h: c.volume_24h ?? 0,
    market_cap: c.market_cap ?? 0,
  }));

  return (
    <>
      <Header onRefresh={handleRefresh} isRefreshing={isRefreshing} />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error banner */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Global Stats */}
        <GlobalStatsCards stats={global} loading={loading} />

        {/* Fear & Greed + News row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <FearGreedGauge />
          </div>
          <div className="lg:col-span-2">
            <NewsSection limit={10} hours={24} />
          </div>
        </div>

        {/* Market Overview */}
        <section>
          <h2 className="text-xl font-bold text-white mb-4">Market Overview</h2>
          <CryptoTable data={tableData} loading={loading} />
        </section>
      </main>
    </>
  );
}
