'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import type { CryptoTableData, SortField, SortDirection } from '@/types';
import { formatPrice, formatLargeNumber, formatPercent, getChangeColor, cn } from '@/lib/utils';

interface Props {
  data: CryptoTableData[];
  loading: boolean;
}

const ITEMS_PER_PAGE_OPTIONS = [10, 25, 50, 100];

export default function CryptoTable({ data, loading }: Props) {
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);

  // Sort data
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      let aVal: string | number = a[sortField];
      let bVal: string | number = b[sortField];

      // Handle string comparison for name
      if (sortField === 'name') {
        aVal = (aVal as string).toLowerCase();
        bVal = (bVal as string).toLowerCase();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortField, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedData.slice(start, start + itemsPerPage);
  }, [sortedData, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(data.length / itemsPerPage);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection(field === 'rank' ? 'asc' : 'desc');
    }
    setCurrentPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-3 h-3" />
    ) : (
      <ChevronDown className="w-3 h-3" />
    );
  };

  const HeaderCell = ({
    field,
    children,
    className = '',
    align = 'left',
  }: {
    field: SortField;
    children: React.ReactNode;
    className?: string;
    align?: 'left' | 'right';
  }) => (
    <th
      onClick={() => handleSort(field)}
      className={cn(
        'px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors',
        align === 'right' ? 'text-right' : 'text-left',
        className
      )}
    >
      <div className={cn('flex items-center gap-1', align === 'right' && 'justify-end')}>
        {children}
        <SortIcon field={field} />
      </div>
    </th>
  );

  if (loading) {
    return (
      <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl overflow-hidden backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">#</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400">Name</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">Price</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400">24h %</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 hidden md:table-cell">7d %</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 hidden lg:table-cell">Volume</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 hidden xl:table-cell">Market Cap</th>
              </tr>
            </thead>
            <tbody>
              {[...Array(10)].map((_, i) => (
                <tr key={i} className="border-t border-gray-800/60">
                  <td className="px-4 py-4"><div className="h-4 w-6 bg-gray-800/50 rounded animate-pulse" /></td>
                  <td className="px-4 py-4"><div className="h-4 w-24 bg-gray-800/50 rounded animate-pulse" /></td>
                  <td className="px-4 py-4"><div className="h-4 w-20 bg-gray-800/50 rounded animate-pulse ml-auto" /></td>
                  <td className="px-4 py-4"><div className="h-4 w-16 bg-gray-800/50 rounded animate-pulse ml-auto" /></td>
                  <td className="px-4 py-4 hidden md:table-cell"><div className="h-4 w-16 bg-gray-800/50 rounded animate-pulse ml-auto" /></td>
                  <td className="px-4 py-4 hidden lg:table-cell"><div className="h-4 w-20 bg-gray-800/50 rounded animate-pulse ml-auto" /></td>
                  <td className="px-4 py-4 hidden xl:table-cell"><div className="h-4 w-24 bg-gray-800/50 rounded animate-pulse ml-auto" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl overflow-hidden backdrop-blur-xl">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <HeaderCell field="rank">#</HeaderCell>
              <HeaderCell field="name">Name</HeaderCell>
              <HeaderCell field="price" align="right">Price</HeaderCell>
              <HeaderCell field="change_24h" align="right">24h %</HeaderCell>
              <HeaderCell field="change_7d" align="right" className="hidden md:table-cell">7d %</HeaderCell>
              <HeaderCell field="volume_24h" align="right" className="hidden lg:table-cell">Volume (24h)</HeaderCell>
              <HeaderCell field="market_cap" align="right" className="hidden xl:table-cell">Market Cap</HeaderCell>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((coin) => (
              <tr
                key={coin.id}
                className="border-t border-gray-800/60 hover:bg-gray-800/30 transition-colors"
              >
                <td className="px-4 py-4 text-sm text-gray-400">{coin.rank}</td>
                <td className="px-4 py-4">
                  <Link
                    href={`/coin/${coin.id}`}
                    className="flex items-center gap-3 hover:text-blue-400 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center text-white font-semibold text-xs">
                      {coin.symbol.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium text-white text-sm">{coin.name}</div>
                      <div className="text-gray-500 text-xs uppercase">{coin.symbol}</div>
                    </div>
                  </Link>
                </td>
                <td className="px-4 py-4 text-sm text-white font-medium text-right">
                  {formatPrice(coin.price)}
                </td>
                <td className={cn('px-4 py-4 text-sm font-medium text-right', getChangeColor(coin.change_24h))}>
                  {formatPercent(coin.change_24h)}
                </td>
                <td className={cn('px-4 py-4 text-sm font-medium text-right hidden md:table-cell', getChangeColor(coin.change_7d))}>
                  {formatPercent(coin.change_7d)}
                </td>
                <td className="px-4 py-4 text-sm text-gray-300 text-right hidden lg:table-cell">
                  {formatLargeNumber(coin.volume_24h)}
                </td>
                <td className="px-4 py-4 text-sm text-gray-300 text-right hidden xl:table-cell">
                  {formatLargeNumber(coin.market_cap)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data.length > 10 && (
        <div className="px-4 py-3 border-t border-gray-800/60 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>Show</span>
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-gray-800/70 border border-gray-700/60 rounded px-2 py-1 text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {ITEMS_PER_PAGE_OPTIONS.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            <span>of {data.length}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
              className="p-2 rounded bg-gray-800/70 border border-gray-700/60 hover:bg-gray-700/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-400">
              Page {currentPage} of {totalPages || 1}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || totalPages === 0}
              aria-label="Next page"
              className="p-2 rounded bg-gray-800/70 border border-gray-700/60 hover:bg-gray-700/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
