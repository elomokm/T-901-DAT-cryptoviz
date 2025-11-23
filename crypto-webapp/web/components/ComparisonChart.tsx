'use client';

import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { CoinHistoryResponse } from '@/types';
import { formatRelativeTime } from '@/lib/utils';

interface ComparisonChartProps {
  coinsData: CoinHistoryResponse[];
  mainCoinId: string;
}

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ComparisonChart({ coinsData, mainCoinId }: ComparisonChartProps) {
  const chartData = useMemo(() => {
    if (coinsData.length === 0) return [];

    // Utiliser les timestamps de la crypto principale comme base
    const mainCoin = coinsData.find(c => c.id === mainCoinId);
    if (!mainCoin || mainCoin.prices.length === 0) return [];

    const baseTimestamps = mainCoin.prices.map(p => new Date(p.timestamp).getTime());

    // Fonction pour trouver le prix le plus proche
    const findClosestPrice = (prices: any[], targetTime: number) => {
      let closest = prices[0];
      let minDiff = Math.abs(new Date(prices[0].timestamp).getTime() - targetTime);
      
      for (const price of prices) {
        const diff = Math.abs(new Date(price.timestamp).getTime() - targetTime);
        if (diff < minDiff) {
          minDiff = diff;
          closest = price;
        }
      }
      return closest;
    };

    // Normaliser: % change depuis le début pour chaque coin
    return baseTimestamps.map(timestamp => {
      const point: any = {
        timestamp,
        formattedTime: formatRelativeTime(new Date(timestamp).toISOString()),
      };

      coinsData.forEach(coin => {
        if (coin.prices.length === 0) return;
        
        // Trouver le prix le plus proche de ce timestamp
        const pricePoint = findClosestPrice(coin.prices, timestamp);
        const initialPrice = coin.prices[0].price;
        
        const percentChange = ((pricePoint.price - initialPrice) / initialPrice) * 100;
        point[coin.id] = percentChange;
      });

      return point;
    });
  }, [coinsData, mainCoinId]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 border border-gray-700">
          <p className="text-gray-400 text-xs mb-2">{payload[0].payload.formattedTime}</p>
          <div className="space-y-1">
            {payload.map((entry: any, index: number) => {
              const coinData = coinsData.find(c => c.id === entry.dataKey);
              if (!coinData) return null;
              
              return (
                <div key={index} className="flex items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-gray-300">{coinData.symbol.toUpperCase()}</span>
                  </div>
                  <span
                    className="font-semibold"
                    style={{ color: entry.value >= 0 ? '#10b981' : '#ef4444' }}
                  >
                    {entry.value >= 0 ? '+' : ''}{entry.value.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    return null;
  };

  if (coinsData.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-gray-400">
        Sélectionnez des cryptos à comparer
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
        <XAxis
          dataKey="timestamp"
          tickFormatter={(timestamp) => {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          }}
          stroke="#9ca3af"
          style={{ fontSize: '12px' }}
          tick={{ fill: '#9ca3af' }}
        />
        <YAxis
          tickFormatter={(value) => `${value >= 0 ? '+' : ''}${value.toFixed(0)}%`}
          stroke="#9ca3af"
          style={{ fontSize: '12px' }}
          tick={{ fill: '#9ca3af' }}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: '12px' }}
          formatter={(value) => {
            const coin = coinsData.find(c => c.id === value);
            return coin ? `${coin.name} (${coin.symbol.toUpperCase()})` : value;
          }}
        />
        {coinsData.map((coin, index) => (
          <Line
            key={coin.id}
            type="monotone"
            dataKey={coin.id}
            stroke={CHART_COLORS[index % CHART_COLORS.length]}
            strokeWidth={coin.id === mainCoinId ? 3 : 2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
