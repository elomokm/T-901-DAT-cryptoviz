/**
 * Home Page - Crypto Dashboard
 * 
 * Features:
 * - Top Gainers & Losers (Priority 1)
 * - Full Crypto Table with ranking (Priority 1)
 * - Dark mode with glassmorphism design
 * 
 * Style: Cryptic.com inspired
 */

'use client';

import { useEffect, useState } from 'react';
import CryptoCard from '@/components/CryptoCard';
import CryptoTable from '@/components/CryptoTable';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface Mover {
  crypto: string;
  current_price: number;
  price_24h_ago: number;
  change_24h_pct: number;
}

interface TopMoversResponse {
  gainers: Mover[];
  losers: Mover[];
  timestamp: string;
  is_mock?: boolean;
}

interface CryptoListResponse {
  data: Array<{
    rank: number;
    id: string;
    symbol: string;
    name: string;
    price: number;
    change_24h: number;
    change_7d: number;
    volume_24h: number;
    market_cap: number;
  }>;
  timestamp: string;
  is_mock?: boolean;
}

export default function Home() {
  const [topMovers, setTopMovers] = useState<TopMoversResponse | null>(null);
  const [cryptoList, setCryptoList] = useState<CryptoListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch top movers (mock pour l'instant)
    fetch(`${API_BASE}/top-movers/mock?limit=3`)
      .then(res => res.json())
      .then(data => setTopMovers(data))
      .catch(err => console.error('Error fetching top movers:', err));

    // Fetch crypto list
    fetch(`${API_BASE}/crypto-list`)
      .then(res => res.json())
      .then(data => {
        setCryptoList(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching crypto list:', err);
        setLoading(false);
      });
  }, []);

  // Crypto name mapping
  const cryptoNames: Record<string, { symbol: string; name: string }> = {
    bitcoin: { symbol: 'BTC', name: 'Bitcoin' },
    ethereum: { symbol: 'ETH', name: 'Ethereum' },
    binancecoin: { symbol: 'BNB', name: 'BNB' },
    ripple: { symbol: 'XRP', name: 'XRP' },
    dogecoin: { symbol: 'DOGE', name: 'Dogecoin' },
    solana: { symbol: 'SOL', name: 'Solana' },
    polygon: { symbol: 'MATIC', name: 'Polygon' },
    chainlink: { symbol: 'LINK', name: 'Chainlink' },
    avalanche: { symbol: 'AVAX', name: 'Avalanche' },
    cardano: { symbol: 'ADA', name: 'Cardano' },
    polkadot: { symbol: 'DOT', name: 'Polkadot' },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800/50 backdrop-blur-xl bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                CryptoViz
              </h1>
              <p className="text-gray-400 text-sm mt-1">Real-time cryptocurrency dashboard</p>
            </div>
            
            {/* Mock indicator (à retirer plus tard) */}
            {(topMovers?.is_mock || cryptoList?.is_mock) && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 px-3 py-1 rounded-full text-xs text-yellow-400">
                📊 Mock Data
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        
        {/* Section: Top Gainers & Losers */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="text-green-400">📈</span>
            Top Gainers & Losers
            <span className="text-gray-500 text-sm font-normal">(24h)</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Gainers */}
            <div>
              <h3 className="text-green-400 font-semibold mb-4 flex items-center gap-2">
                <span>🚀</span> Top Gainers
              </h3>
              <div className="space-y-4">
                {topMovers?.gainers.map((mover, idx) => (
                  <CryptoCard
                    key={mover.crypto}
                    crypto={mover.crypto}
                    symbol={cryptoNames[mover.crypto]?.symbol}
                    name={cryptoNames[mover.crypto]?.name}
                    currentPrice={mover.current_price}
                    change24h={mover.change_24h_pct}
                    variant="gainer"
                    rank={idx + 1}
                  />
                ))}
              </div>
            </div>

            {/* Losers */}
            <div>
              <h3 className="text-red-400 font-semibold mb-4 flex items-center gap-2">
                <span>📉</span> Top Losers
              </h3>
              <div className="space-y-4">
                {topMovers?.losers.map((mover, idx) => (
                  <CryptoCard
                    key={mover.crypto}
                    crypto={mover.crypto}
                    symbol={cryptoNames[mover.crypto]?.symbol}
                    name={cryptoNames[mover.crypto]?.name}
                    currentPrice={mover.current_price}
                    change24h={mover.change_24h_pct}
                    variant="loser"
                    rank={idx + 1}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Section: Full Crypto Table */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span>💎</span>
            Market Overview
            <span className="text-gray-500 text-sm font-normal">(11 cryptos)</span>
          </h2>

          <CryptoTable 
            data={cryptoList?.data || []} 
            loading={loading}
          />
        </section>

        {/* Footer timestamp */}
        {(topMovers || cryptoList) && (
          <div className="text-center text-gray-500 text-xs">
            Last updated: {new Date(topMovers?.timestamp || cryptoList?.timestamp || '').toLocaleString()}
          </div>
        )}
      </main>
    </div>
  );
}
