/**
 * CryptoTable Component
 * 
 * Table complète des cryptos avec ranking, volumes, market cap
 * Design moderne avec hover effects
 */

'use client';

import PriceDisplay from './PriceDisplay';

interface CryptoData {
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

interface CryptoTableProps {
  data: CryptoData[];
  loading?: boolean;
}

export default function CryptoTable({ data, loading = false }: CryptoTableProps) {
  const formatVolume = (value: number): string => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  };

  if (loading) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-xl rounded-xl border border-gray-800/50 p-8">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-800/50 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 backdrop-blur-xl rounded-xl border border-gray-800/50 overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800/50">
              <th className="px-4 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                #
              </th>
              <th className="px-4 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Name
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Price
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                24h %
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                7d %
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">
                Volume (24h)
              </th>
              <th className="px-4 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider hidden lg:table-cell">
                Market Cap
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((crypto, idx) => (
              <tr 
                key={crypto.id}
                className="border-b border-gray-800/30 hover:bg-gray-800/30 transition-colors cursor-pointer group"
              >
                {/* Rank */}
                <td className="px-4 py-4 text-sm text-gray-400 font-mono">
                  {crypto.rank}
                </td>
                
                {/* Name + Symbol */}
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    {/* Icon placeholder */}
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center text-white font-semibold text-xs">
                      {crypto.symbol.charAt(0)}
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">{crypto.name}</div>
                      <div className="text-gray-500 text-xs uppercase">{crypto.symbol}</div>
                    </div>
                  </div>
                </td>
                
                {/* Price */}
                <td className="px-4 py-4 text-right">
                  <div className="text-white text-sm font-mono">
                    {crypto.price < 1 
                      ? `$${crypto.price.toFixed(6)}` 
                      : `$${crypto.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                    }
                  </div>
                </td>
                
                {/* 24h Change */}
                <td className="px-4 py-4 text-right">
                  <span className={`text-sm font-medium ${
                    crypto.change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {crypto.change_24h >= 0 ? '+' : ''}{crypto.change_24h.toFixed(2)}%
                  </span>
                </td>
                
                {/* 7d Change */}
                <td className="px-4 py-4 text-right">
                  <span className={`text-sm font-medium ${
                    crypto.change_7d >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {crypto.change_7d >= 0 ? '+' : ''}{crypto.change_7d.toFixed(2)}%
                  </span>
                </td>
                
                {/* Volume 24h */}
                <td className="px-4 py-4 text-right text-sm text-gray-400 font-mono hidden md:table-cell">
                  {formatVolume(crypto.volume_24h)}
                </td>
                
                {/* Market Cap */}
                <td className="px-4 py-4 text-right text-sm text-gray-300 font-mono hidden lg:table-cell">
                  {formatVolume(crypto.market_cap)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
