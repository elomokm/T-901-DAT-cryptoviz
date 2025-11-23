'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { PricePoint } from '@/types';
import { formatPrice } from '@/lib/utils';

interface InteractiveChartProps {
  prices: PricePoint[];
}

// Custom Tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const date = new Date(data.timestamp);
    
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-1">
          {date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
        <p className="text-lg font-bold text-white">
          {formatPrice(data.price)}
        </p>
      </div>
    );
  }
  return null;
};

export default function InteractiveChart({ prices }: InteractiveChartProps) {
  const { chartData, minPrice, maxPrice, isPositive } = useMemo(() => {
    if (!prices || prices.length === 0) {
      return { chartData: [], minPrice: 0, maxPrice: 0, isPositive: true };
    }

    const priceValues = prices.map((p) => p.price);
    const min = Math.min(...priceValues);
    const max = Math.max(...priceValues);
    const isPositive = prices[prices.length - 1].price >= prices[0].price;

    return {
      chartData: prices,
      minPrice: min,
      maxPrice: max,
      isPositive,
    };
  }, [prices]);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        No price data available
      </div>
    );
  }

  const gradientId = isPositive ? 'colorPriceUp' : 'colorPriceDown';
  const strokeColor = isPositive ? '#22c55e' : '#ef4444';
  const fillColor = isPositive ? '#22c55e' : '#ef4444';

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={fillColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={fillColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#374151" 
            opacity={0.3}
          />
          
          <XAxis
            dataKey="timestamp"
            stroke="#9ca3af"
            fontSize={12}
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              });
            }}
            tick={{ fill: '#9ca3af' }}
          />
          
          <YAxis
            stroke="#9ca3af"
            fontSize={12}
            domain={[minPrice * 0.995, maxPrice * 1.005]}
            tickFormatter={(value) => `$${value.toLocaleString('en-US', {
              notation: 'compact',
              maximumFractionDigits: 0,
            })}`}
            tick={{ fill: '#9ca3af' }}
          />
          
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: strokeColor, strokeWidth: 1 }} />
          
          <Area
            type="monotone"
            dataKey="price"
            stroke={strokeColor}
            strokeWidth={2}
            fillOpacity={1}
            fill={`url(#${gradientId})`}
            animationDuration={1000}
          />
        </AreaChart>
      </ResponsiveContainer>
      
      {/* Price Range Display */}
      <div className="flex justify-between mt-2 text-sm text-gray-400">
        <div>
          <span className="text-xs">Low: </span>
          <span className="font-medium">{formatPrice(minPrice)}</span>
        </div>
        <div>
          <span className="text-xs">High: </span>
          <span className="font-medium">{formatPrice(maxPrice)}</span>
        </div>
      </div>
    </div>
  );
}
