'use client';

import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  AreaChart,
  BarChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { PricePoint } from '@/types';
import { formatPrice, formatRelativeTime } from '@/lib/utils';

export type ChartType = 'line' | 'area' | 'bar' | 'candlestick';

interface MultiChartProps {
  data: PricePoint[];
  type: ChartType;
  color?: string;
  name?: string;
}

export default function MultiChart({ data, type, color = '#3b82f6', name = 'Price' }: MultiChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      timestamp: new Date(point.timestamp).getTime(),
      price: point.price,
      formattedTime: formatRelativeTime(point.timestamp),
    }));
  }, [data]);

  const minPrice = useMemo(() => Math.min(...chartData.map((d) => d.price)), [chartData]);
  const maxPrice = useMemo(() => Math.max(...chartData.map((d) => d.price)), [chartData]);
  const padding = (maxPrice - minPrice) * 0.1;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass-card p-3 border border-gray-700">
          <p className="text-gray-400 text-xs mb-1">{data.formattedTime}</p>
          <p className="text-white font-semibold">{formatPrice(data.price)}</p>
        </div>
      );
    }
    return null;
  };

  const commonProps = {
    data: chartData,
    margin: { top: 5, right: 5, left: 5, bottom: 5 },
  };

  const commonAxisProps = {
    stroke: '#6b7280',
    style: { fontSize: '12px' },
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      {type === 'line' ? (
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }}
            {...commonAxisProps}
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            {...commonAxisProps}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={2}
            dot={false}
            animationDuration={300}
          />
        </LineChart>
      ) : type === 'area' ? (
        <AreaChart {...commonProps}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.8} />
              <stop offset="95%" stopColor={color} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }}
            {...commonAxisProps}
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            {...commonAxisProps}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={2}
            fill="url(#colorPrice)"
            animationDuration={300}
          />
        </AreaChart>
      ) : type === 'bar' ? (
        <BarChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }}
            {...commonAxisProps}
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            {...commonAxisProps}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="price" fill={color} radius={[4, 4, 0, 0]} />
        </BarChart>
      ) : (
        // Candlestick placeholder - would need OHLC data
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-gray-400">Candlestick chart requires OHLC data</p>
            <p className="text-sm text-gray-500 mt-2">Coming soon...</p>
          </div>
        </div>
      )}
    </ResponsiveContainer>
  );
}
