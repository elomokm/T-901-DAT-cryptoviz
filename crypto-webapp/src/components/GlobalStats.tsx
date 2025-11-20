import { TrendingUp, DollarSign, Activity } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { GlobalStats } from '@/lib/api';
import { formatLargeNumber, formatPercentage, getChangeColor } from '@/utils/formatters';
import { Skeleton } from './ui/skeleton';

interface GlobalStatsCardsProps {
  stats: GlobalStats | null;
  loading: boolean;
}

export default function GlobalStatsCards({ stats, loading }: GlobalStatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="glass-card">
            <CardContent className="p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32 mb-1" />
              <Skeleton className="h-3 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      title: 'Total Market Cap',
      value: formatLargeNumber(stats.total_market_cap),
      change: stats.market_cap_change_24h,
      icon: DollarSign,
      color: 'text-primary',
    },
    {
      title: 'Total Volume 24h',
      value: formatLargeNumber(stats.total_volume_24h),
      icon: Activity,
      color: 'text-accent',
    },
    {
      title: 'Active Cryptos',
      value: stats.count.toString(),
      icon: TrendingUp,
      color: 'text-success',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {cards.map((card, index) => (
        <Card key={index} className="glass-card hover:border-primary/30 transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-2">{card.title}</p>
                <h3 className="text-2xl font-bold">{card.value}</h3>
                {card.change !== undefined && (
                  <p className={`text-sm mt-1 ${getChangeColor(card.change)}`}>
                    {formatPercentage(card.change)} 24h
                  </p>
                )}
              </div>
              <div className={`p-3 rounded-lg bg-secondary/50 ${card.color}`}>
                <card.icon className="w-5 h-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
