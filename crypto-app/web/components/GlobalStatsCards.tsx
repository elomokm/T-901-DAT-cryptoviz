'use client';

import React from 'react';
import { DollarSign, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import type { GlobalStats } from '@/types';
import { formatLargeNumber, formatPercent, cn } from '@/lib/utils';

interface Props {
  stats: GlobalStats | null;
  loading?: boolean;
}

function StatCard({
  label,
  value,
  subtext,
  loading,
  icon: Icon,
  gradient,
  isChange = false,
}: {
  label: string;
  value: string;
  subtext: string;
  loading: boolean;
  icon: React.ElementType;
  gradient: string;
  isChange?: boolean;
}) {
  const isPositive = isChange && value.startsWith('+');
  const isNegative = isChange && value.startsWith('-');

  return (
    <div className="relative bg-gray-900/60 border border-gray-800/60 rounded-xl p-6 backdrop-blur-xl overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-gray-400 text-xs uppercase tracking-wider">{label}</div>
          {loading ? (
            <div className="h-8 w-32 bg-gray-800/50 rounded animate-pulse mt-2" />
          ) : (
            <div
              className={cn(
                'text-2xl font-bold mt-2',
                isChange && isPositive && 'text-green-400',
                isChange && isNegative && 'text-red-400',
                !isChange && 'text-white'
              )}
            >
              {value}
            </div>
          )}
          {!loading && (
            <div className="text-gray-500 text-xs mt-2">{subtext}</div>
          )}
        </div>
        <div className="p-2 rounded-lg bg-gray-800/50">
          <Icon className="w-5 h-5 text-gray-400" />
        </div>
      </div>
      <div className={cn('absolute inset-0 rounded-xl pointer-events-none', gradient)} />
    </div>
  );
}

export default function GlobalStatsCards({ stats, loading = false }: Props) {
  const changeValue = stats?.market_cap_change_24h;
  const changeFormatted = changeValue !== undefined && changeValue !== null
    ? formatPercent(changeValue)
    : '—';

  return (
    <section aria-label="Global Market Statistics">
      <h2 className="sr-only">Global Market Stats</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        <StatCard
          label="Total Market Cap"
          value={loading ? '—' : formatLargeNumber(stats?.total_market_cap)}
          subtext="All assets combined"
          loading={loading}
          icon={DollarSign}
          gradient="bg-gradient-to-br from-blue-500/5 to-purple-500/5"
        />

        <StatCard
          label="Total Volume (24h)"
          value={loading ? '—' : formatLargeNumber(stats?.total_volume_24h)}
          subtext="Last 24 hours"
          loading={loading}
          icon={Activity}
          gradient="bg-gradient-to-br from-green-500/5 to-emerald-500/5"
        />

        <StatCard
          label="Market Cap Change"
          value={loading ? '—' : changeFormatted}
          subtext="Last 24 hours"
          loading={loading}
          icon={changeValue && changeValue >= 0 ? TrendingUp : TrendingDown}
          gradient="bg-gradient-to-br from-pink-500/5 to-purple-500/5"
          isChange={true}
        />
      </div>
    </section>
  );
}
