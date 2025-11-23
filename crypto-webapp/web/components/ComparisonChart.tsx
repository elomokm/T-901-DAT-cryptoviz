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
import { formatPrice, formatRelativeTime } from '@/lib/utils';

interface ComparisonChartProps {
  coinsData: { [key: string]: CoinHistoryResponse };
  normalized?: boolean;
}

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ComparisonChart({ coinsData, normalized = false }: ComparisonChartProps) {
  const chartData = useMemo(() => {
    const coinIds = Object.keys(coinsData);
    if (coinIds.length === 0) return [];

    // Get all timestamps from all coins
    const allTimestamps = new Set<number>();
    coinIds.forEach((coinId) => {
      coinsData[coinId].prices.forEach((point) => {
        allTimestamps.add(new Date(point.timestamp).getTime());
      });
    });

    const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);

    // Normalize prices if requested (show as % change from start)
    const normalizedData = coinIds.reduce((acc, coinId) => {
      const prices = coinsData[coinId].prices;
      const firstPrice = prices[0]?.price || 1;
      acc[coinId] = prices.reduce((map, point) => {
        const timestamp = new Date(point.timestamp).getTime();
        const value = normalized
          ? ((point.price - firstPrice) / firstPrice) * 100
          : point.price;
        map[timestamp] = value;
        return map;
      }, {} as { [key: number]: number });
      return acc;
    }, {} as { [coinId: string]: { [timestamp: number]: number } });

    // Combine all data by timestamp
    return sortedTimestamps.map((timestamp) => {
      const dataPoint: any = {
        timestamp,
        formattedTime: formatRelativeTime(new Date(timestamp).toISOString()),
      };

      coinIds.forEach((coinId) => {
        dataPoint[coinId] = normalizedData[coinId][timestamp] || null;
      });

      return dataPoint;
    });
  }, [coinsData, normalized]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass-card p-4 border border-gray-700">
          <p className="text-gray-400 text-xs mb-2">{data.formattedTime}</p>
          <div className="space-y-1">
            {payload.map((entry: any, index: number) => {
              const coin = coinsData[entry.dataKey];
              return (
                <div key={index} className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm font-medium">{coin?.symbol.toUpperCase()}</span>
                  </div>
                  <span className="text-sm font-semibold">
                    {normalized
                      ? `${entry.value > 0 ? '+' : ''}${entry.value.toFixed(2)}%`
                      : formatPrice(entry.value)}
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

  if (Object.keys(coinsData).length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-400">Select coins to compare</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }}
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            tickFormatter={(value) =>
              normalized ? `${value > 0 ? '+' : ''}${value.toFixed(0)}%` : `$${value.toLocaleString()}`
            }
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => {
              const coin = coinsData[value];
              return coin ? `${coin.name} (${coin.symbol.toUpperCase()})` : value;
            }}
          />
          {Object.keys(coinsData).map((coinId, index) => (
            <Line
              key={coinId}
              type="monotone"
              dataKey={coinId}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
              animationDuration={300}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Toggle Normalized View */}
      <div className="flex justify-end">
        <button
          onClick={() => {}}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          {normalized ? '📊 Show Actual Prices' : '📈 Show Percentage Change'}
        </button>
      </div>
    </div>
  );
}
