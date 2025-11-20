'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Search, TrendingUp, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export default function Header({ onRefresh, isRefreshing }: HeaderProps) {
  const [search, setSearch] = useState('');
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = search.trim().toLowerCase();
    if (trimmed) {
      router.push(`/coin/${encodeURIComponent(trimmed)}`);
      setSearch('');
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-gray-800/60 bg-gray-900/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                CryptoViz
              </h1>
              <span className="text-xs text-gray-500 hidden sm:block">
                Real-time market data
              </span>
            </div>
          </Link>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {/* Search */}
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search coin..."
                aria-label="Search cryptocurrencies"
                className="w-40 sm:w-56 bg-gray-800/70 border border-gray-700/60 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </form>

            {/* Refresh button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                aria-label="Refresh data"
                className="p-2 rounded-lg bg-gray-800/70 border border-gray-700/60 hover:bg-gray-700/70 transition-colors disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-4 h-4 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`}
                />
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
