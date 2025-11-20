'use client';

import { useEffect, useState } from 'react';
import GlobalStatsCards from '@/components/GlobalStatsCards';
import FearGreedGauge from '@/components/FearGreedGauge';
import CryptoTable from '@/components/CryptoTable';
import NewsSection from '@/components/NewsSection';
import { GlobalStats, CoinSummary, NewsResponse, FearGreedResponse } from '@/types';
import { getGlobal, getCoins, getNews, getFearGreed } from '@/lib/api';

export default function Dashboard() {
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [coins, setCoins] = useState<CoinSummary[]>([]);
  const [news, setNews] = useState<NewsResponse | null>(null);
  const [fearGreed, setFearGreed] = useState<FearGreedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [globalData, coinsData, newsData, fearGreedData] = await Promise.allSettled([
          getGlobal(),
          getCoins({ per_page: 50, sparkline: true }),
          getNews({ page_size: 6 }),
          getFearGreed(),
        ]);

        if (globalData.status === 'fulfilled') {
          setGlobalStats(globalData.value);
        }

        if (coinsData.status === 'fulfilled') {
          setCoins(coinsData.value);
        } else {
          console.error('Failed to fetch coins:', coinsData.reason);
        }

        if (newsData.status === 'fulfilled') {
          setNews(newsData.value);
        }

        if (fearGreedData.status === 'fulfilled') {
          setFearGreed(fearGreedData.value);
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Refresh data every 60 seconds
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="glass-card p-8 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold gradient-text mb-2">Market Overview</h1>
        <p className="text-gray-400">Real-time cryptocurrency market data and analytics</p>
      </div>

      {/* Global Stats and Fear & Greed */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <GlobalStatsCards stats={globalStats} loading={loading} />
        </div>
        <div className="lg:col-span-1">
          <FearGreedGauge data={fearGreed} loading={loading} />
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Crypto Table - Takes 2/3 on large screens */}
        <div className="xl:col-span-2">
          <CryptoTable coins={coins} loading={loading} />
        </div>

        {/* News Section - Takes 1/3 on large screens */}
        <div className="xl:col-span-1">
          <NewsSection news={news} loading={loading} />
        </div>
      </div>
    </div>
  );
}
