'use client';

import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  AreaChart,
  BarChart,
  ComposedChart,
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
  // Préparer données pour tous types de charts
  const chartData = useMemo(() => {
    if (type === 'candlestick') {
      // Générer OHLC simulé à partir des prix (grouper par périodes)
      const groupedData: any[] = [];
      const groupSize = Math.max(1, Math.floor(data.length / 50)); // Max 50 bougies
      
      for (let i = 0; i < data.length; i += groupSize) {
        const group = data.slice(i, i + groupSize);
        if (group.length === 0) continue;
        
        const prices = group.map(p => p.price);
        const open = group[0].price;
        const close = group[group.length - 1].price;
        const high = Math.max(...prices);
        const low = Math.min(...prices);
        
        groupedData.push({
          timestamp: new Date(group[0].timestamp).getTime(),
          open,
          high,
          low,
          close,
          formattedTime: formatRelativeTime(group[0].timestamp),
          isPositive: close >= open,
        });
      }
      return groupedData;
    }
    
    // Pour les autres types de charts
    return data.map((point) => ({
      timestamp: new Date(point.timestamp).getTime(),
      price: point.price,
      formattedTime: formatRelativeTime(point.timestamp),
    }));
  }, [data, type]);

  const minPrice = useMemo(() => {
    if (type === 'candlestick') {
      return Math.min(...chartData.map((d: any) => d.low));
    }
    return Math.min(...chartData.map((d: any) => d.price));
  }, [chartData, type]);

  const maxPrice = useMemo(() => {
    if (type === 'candlestick') {
      return Math.max(...chartData.map((d: any) => d.high));
    }
    return Math.max(...chartData.map((d: any) => d.price));
  }, [chartData, type]);
  
  const padding = (maxPrice - minPrice) * 0.1;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      if (type === 'candlestick') {
        const isPositive = data.close >= data.open;
        return (
          <div className="glass-card p-3 border border-gray-700">
            <p className="text-gray-400 text-xs mb-2">{data.formattedTime}</p>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between gap-3">
                <span className="text-gray-400">Open:</span>
                <span className="text-white font-semibold">{formatPrice(data.open)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-gray-400">High:</span>
                <span className="text-green-400 font-semibold">{formatPrice(data.high)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-gray-400">Low:</span>
                <span className="text-red-400 font-semibold">{formatPrice(data.low)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-gray-400">Close:</span>
                <span className={`font-semibold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {formatPrice(data.close)}
                </span>
              </div>
            </div>
          </div>
        );
      }
      
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
      ) : type === 'candlestick' ? (
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
            dataKey="close"
            stroke="none"
            dot={(props: any) => {
              const { cx, cy, payload, index } = props;
              if (!payload || !chartData[index]) return <g />;
              
              const candle = chartData[index];
              const chartHeight = 400;
              const yMin = minPrice - padding;
              const yMax = maxPrice + padding;
              const priceToY = (price: number) => {
                const ratio = (yMax - price) / (yMax - yMin);
                return ratio * chartHeight;
              };
              
              const yHigh = priceToY(candle.high);
              const yLow = priceToY(candle.low);
              const yOpen = priceToY(candle.open);
              const yClose = priceToY(candle.close);
              const bodyTop = Math.min(yOpen, yClose);
              const bodyHeight = Math.abs(yOpen - yClose);
              const wickColor = candle.isPositive ? '#10b981' : '#ef4444';
              const bodyWidth = 8;
              
              return (
                <g key={`candle-${index}`}>
                  {/* Wick */}
                  <line
                    x1={cx}
                    y1={yHigh}
                    x2={cx}
                    y2={yLow}
                    stroke={wickColor}
                    strokeWidth={1}
                  />
                  {/* Body */}
                  <rect
                    x={cx - bodyWidth / 2}
                    y={bodyTop}
                    width={bodyWidth}
                    height={Math.max(bodyHeight, 2)}
                    fill={wickColor}
                    stroke={candle.isPositive ? '#059669' : '#dc2626'}
                    strokeWidth={1}
                  />
                </g>
              );
            }}
            isAnimationActive={false}
          />
        </LineChart>
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-400">Unknown chart type</p>
        </div>
      )}
    </ResponsiveContainer>
  );
}
