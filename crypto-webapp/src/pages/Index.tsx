import { useEffect, useState } from 'react';
import { getCoins, getGlobal, CoinSummary, GlobalStats } from '@/lib/api';
import Header from '@/components/Header';
import GlobalStatsCards from '@/components/GlobalStats';
import FearGreedGauge from '@/components/FearGreedGauge';
import CryptoTable from '@/components/CryptoTable';
import NewsSection from '@/components/NewsSection';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Index() {
  const [coins, setCoins] = useState<CoinSummary[]>([]);
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const [coinsData, statsData] = await Promise.all([
        getCoins(50, 1, 'market_cap_desc'),
        getGlobal(),
      ]);

      setCoins(coinsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchData(true);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header with refresh */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              Live Crypto Market
            </h2>
            <p className="text-muted-foreground">
              Real-time cryptocurrency prices and market data
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Global Stats */}
        <div className="mb-8">
          <GlobalStatsCards stats={stats} loading={loading} />
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Fear & Greed */}
          <div className="lg:col-span-1">
            <FearGreedGauge />
          </div>

          {/* News */}
          <div className="lg:col-span-2">
            <NewsSection />
          </div>
        </div>

        {/* Crypto Table */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Top Cryptocurrencies</h3>
          <CryptoTable coins={coins} loading={loading} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 mt-16">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>CryptoViz - Live cryptocurrency market streaming platform</p>
          <p className="mt-1">Data updated in real-time from multiple sources</p>
        </div>
      </footer>
    </div>
  );
}
