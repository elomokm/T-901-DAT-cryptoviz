'use client';

import GlobalStatsCards from '@/components/GlobalStatsCards';
import FearGreedGauge from '@/components/FearGreedGauge';
import CryptoTable from '@/components/CryptoTable';
import NewsSection from '@/components/NewsSection';
import { useBootstrap, useNews } from '@/lib/hooks';

export default function Dashboard() {
  // 🚀 SWR Hooks - Appels dédupliqués + cache intelligent
  const { coins, global: globalStats, fearGreed, isLoading: bootstrapLoading, stale, rateLimited } = useBootstrap(50, true);
  const { articles: news, isLoading: newsLoading } = useNews(6);

  const loading = bootstrapLoading || newsLoading;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold gradient-text mb-2">Market Overview</h1>
        <p className="text-gray-400">Real-time cryptocurrency market data and analytics</p>
        {stale && (
          <div className="mt-3 text-sm px-3 py-2 rounded bg-yellow-500/10 border border-yellow-600 text-yellow-300 inline-flex items-center gap-2">
            <span>⚠️ Données en cache (stale) – rate limit externe, affichage temporaire.</span>
          </div>
        )}
        {rateLimited && !stale && (
          <div className="mt-3 text-sm px-3 py-2 rounded bg-orange-500/10 border border-orange-600 text-orange-300 inline-flex items-center gap-2">
            <span>⏳ Rate limit API externe – rechargement auto dans quelques secondes.</span>
          </div>
        )}
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
