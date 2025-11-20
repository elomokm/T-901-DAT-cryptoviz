'use client';

import { TrendingUp, TrendingDown, DollarSign, BarChart3, Activity, Coins } from 'lucide-react';
import { GlobalStats } from '@/types';
import { formatLargeNumber, formatPercent, getChangeColor } from '@/lib/utils';

interface GlobalStatsCardsProps {
  stats: GlobalStats | null;
  loading?: boolean;
}

export default function GlobalStatsCards({ stats, loading }: GlobalStatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card p-4">
            <div className="skeleton h-4 w-24 mb-2 rounded" />
            <div className="skeleton h-6 w-32 mb-1 rounded" />
            <div className="skeleton h-3 w-20 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Market Cap',
      value: formatLargeNumber(stats?.total_market_cap),
      change: stats?.market_cap_change_percentage_24h,
      icon: DollarSign,
      iconColor: 'text-blue-400',
    },
    {
      title: '24h Volume',
      value: formatLargeNumber(stats?.total_volume),
      icon: BarChart3,
      iconColor: 'text-purple-400',
    },
    {
      title: 'BTC Dominance',
      value: `${stats?.market_cap_percentage?.btc?.toFixed(1) || 0}%`,
      icon: Activity,
      iconColor: 'text-orange-400',
    },
    {
      title: 'Active Cryptos',
      value: stats?.active_cryptocurrencies?.toLocaleString() || '0',
      subtitle: `${stats?.markets?.toLocaleString() || 0} markets`,
      icon: Coins,
      iconColor: 'text-green-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        const changeValue = card.change;
        const isPositive = changeValue && changeValue >= 0;

        return (
          <div
            key={card.title}
            className="glass-card p-4 hover:border-gray-700/80 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400 font-medium">{card.title}</span>
              <Icon className={`w-4 h-4 ${card.iconColor}`} />
            </div>
            <p className="text-lg font-bold mb-1">{card.value}</p>
            {changeValue !== undefined && (
              <div className={`flex items-center gap-1 text-xs ${getChangeColor(changeValue)}`}>
                {isPositive ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span>{formatPercent(changeValue)}</span>
                <span className="text-gray-500">24h</span>
              </div>
            )}
            {card.subtitle && (
              <p className="text-xs text-gray-500 mt-1">{card.subtitle}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
