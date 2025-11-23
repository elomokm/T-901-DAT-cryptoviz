'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react';
import { CoinSummary, SortField, SortDirection } from '@/types';
import {
  formatPrice,
  formatLargeNumber,
  formatPercent,
  getChangeColor,
} from '@/lib/utils';
import Sparkline from './Sparkline';

interface CryptoTableProps {
  coins: CoinSummary[];
  loading?: boolean;
}

export default function CryptoTable({ coins, loading }: CryptoTableProps) {
  const [sortField, setSortField] = useState<SortField>('market_cap_rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection(field === 'market_cap_rank' ? 'asc' : 'desc');
    }
  };

  const sortedCoins = useMemo(() => {
    return [...coins].sort((a, b) => {
      const aValue = a[sortField] ?? 0;
      const bValue = b[sortField] ?? 0;

      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      }
      return aValue < bValue ? 1 : -1;
    });
  }, [coins, sortField, sortDirection]);

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-gray-500" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-3 h-3 text-blue-400" />
    ) : (
      <ChevronDown className="w-3 h-3 text-blue-400" />
    );
  };

  if (loading) {
    return (
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-gray-800/60">
          <div className="skeleton h-6 w-48 rounded" />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800/60">
                {[...Array(7)].map((_, i) => (
                  <th key={i} className="p-4">
                    <div className="skeleton h-4 w-16 rounded" />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...Array(10)].map((_, i) => (
                <tr key={i} className="border-b border-gray-800/40">
                  {[...Array(7)].map((_, j) => (
                    <td key={j} className="p-4">
                      <div className="skeleton h-4 w-20 rounded" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4 border-b border-gray-800/60">
        <h2 className="text-lg font-semibold">Top Cryptocurrencies</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800/60 text-gray-400 text-xs uppercase">
              <th
                className="p-4 text-left cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('market_cap_rank')}
              >
                <div className="flex items-center gap-1">
                  #
                  <SortIcon field="market_cap_rank" />
                </div>
              </th>
              <th className="p-4 text-left">Name</th>
              <th
                className="p-4 text-right cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('current_price')}
              >
                <div className="flex items-center justify-end gap-1">
                  Price
                  <SortIcon field="current_price" />
                </div>
              </th>
              <th
                className="p-4 text-right cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('price_change_percentage_24h')}
              >
                <div className="flex items-center justify-end gap-1">
                  24h %
                  <SortIcon field="price_change_percentage_24h" />
                </div>
              </th>
              <th
                className="p-4 text-right cursor-pointer hover:text-white transition-colors hidden md:table-cell"
                onClick={() => handleSort('market_cap')}
              >
                <div className="flex items-center justify-end gap-1">
                  Market Cap
                  <SortIcon field="market_cap" />
                </div>
              </th>
              <th
                className="p-4 text-right cursor-pointer hover:text-white transition-colors hidden lg:table-cell"
                onClick={() => handleSort('total_volume')}
              >
                <div className="flex items-center justify-end gap-1">
                  Volume (24h)
                  <SortIcon field="total_volume" />
                </div>
              </th>
              <th className="p-4 text-right hidden xl:table-cell">7d Chart</th>
            </tr>
          </thead>
          <tbody>
            {sortedCoins.map((coin) => {
              const change24h = coin.price_change_percentage_24h;

              return (
                <tr
                  key={coin.id}
                  className="border-b border-gray-800/40 table-row-hover"
                >
                  <td className="p-4 text-gray-400">{coin.market_cap_rank}</td>
                  <td className="p-4">
                    <Link
                      href={`/coin/${coin.id}`}
                      className="flex items-center gap-3 hover:text-blue-400 transition-colors"
                    >
                      {coin.image && (
                        <img
                          src={coin.image}
                          alt={coin.name}
                          className="w-6 h-6 rounded-full"
                        />
                      )}
                      <div>
                        <p className="font-medium">{coin.name}</p>
                        <p className="text-xs text-gray-400 uppercase">
                          {coin.symbol}
                        </p>
                      </div>
                    </Link>
                  </td>
                  <td className="p-4 text-right font-medium">
                    {formatPrice(coin.current_price)}
                  </td>
                  <td className={`p-4 text-right ${getChangeColor(change24h)}`}>
                    {formatPercent(change24h)}
                  </td>
                  <td className="p-4 text-right text-gray-300 hidden md:table-cell">
                    {formatLargeNumber(coin.market_cap)}
                  </td>
                  <td className="p-4 text-right text-gray-300 hidden lg:table-cell">
                    {formatLargeNumber(coin.total_volume)}
                  </td>
                  <td className="p-4 text-right hidden xl:table-cell">
                    {coin.sparkline_in_7d && coin.sparkline_in_7d.length > 0 ? (
                      <Sparkline
                        data={coin.sparkline_in_7d}
                        change={coin.price_change_percentage_7d || change24h}
                      />
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {sortedCoins.length === 0 && (
        <div className="p-8 text-center text-gray-400">
          No cryptocurrencies found
        </div>
      )}
    </div>
  );
}
