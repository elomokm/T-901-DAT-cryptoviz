'use client';

import { useMemo } from 'react';
import { PricePoint } from '@/types';
import { formatPrice } from '@/lib/utils';

interface CoinHistoryClientProps {
  prices: PricePoint[];
}

export default function CoinHistoryClient({ prices }: CoinHistoryClientProps) {
  const chartData = useMemo(() => {
    if (!prices || prices.length === 0) {
      return null;
    }

    const priceValues = prices.map((p) => p.price);
    const minPrice = Math.min(...priceValues);
    const maxPrice = Math.max(...priceValues);
    const priceRange = maxPrice - minPrice || 1;

    const width = 800;
    const height = 300;
    const padding = { top: 20, right: 20, bottom: 30, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Create path for the line
    const points = prices.map((point, i) => {
      const x = padding.left + (i / (prices.length - 1)) * chartWidth;
      const y =
        padding.top +
        chartHeight -
        ((point.price - minPrice) / priceRange) * chartHeight;
      return { x, y, price: point.price, timestamp: point.timestamp };
    });

    const linePath = `M ${points.map((p) => `${p.x},${p.y}`).join(' L ')}`;

    // Create area fill path
    const areaPath = `${linePath} L ${points[points.length - 1].x},${
      padding.top + chartHeight
    } L ${padding.left},${padding.top + chartHeight} Z`;

    // Generate Y-axis labels
    const yLabels = [];
    const steps = 5;
    for (let i = 0; i <= steps; i++) {
      const value = minPrice + (priceRange / steps) * i;
      const y = padding.top + chartHeight - (chartHeight / steps) * i;
      yLabels.push({ value, y });
    }

    // Determine if price went up or down
    const isPositive = prices[prices.length - 1].price >= prices[0].price;

    return {
      width,
      height,
      padding,
      linePath,
      areaPath,
      points,
      yLabels,
      isPositive,
      minPrice,
      maxPrice,
    };
  }, [prices]);

  if (!chartData) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        No price data available
      </div>
    );
  }

  const strokeColor = chartData.isPositive ? '#22c55e' : '#ef4444';
  const fillColor = chartData.isPositive
    ? 'rgba(34, 197, 94, 0.1)'
    : 'rgba(239, 68, 68, 0.1)';

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${chartData.width} ${chartData.height}`}
        className="w-full h-64"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Grid lines */}
        {chartData.yLabels.map((label, i) => (
          <line
            key={i}
            x1={chartData.padding.left}
            y1={label.y}
            x2={chartData.width - chartData.padding.right}
            y2={label.y}
            stroke="rgba(75, 85, 99, 0.3)"
            strokeDasharray="4"
          />
        ))}

        {/* Area fill */}
        <path d={chartData.areaPath} fill={fillColor} />

        {/* Line */}
        <path
          d={chartData.linePath}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Y-axis labels */}
        {chartData.yLabels.map((label, i) => (
          <text
            key={i}
            x={chartData.padding.left - 8}
            y={label.y + 4}
            textAnchor="end"
            fontSize="10"
            fill="#9ca3af"
          >
            {formatPrice(label.value)}
          </text>
        ))}

        {/* X-axis labels */}
        {prices.length > 0 && (
          <>
            <text
              x={chartData.padding.left}
              y={chartData.height - 8}
              textAnchor="start"
              fontSize="10"
              fill="#9ca3af"
            >
              {new Date(prices[0].timestamp).toLocaleDateString()}
            </text>
            <text
              x={chartData.width - chartData.padding.right}
              y={chartData.height - 8}
              textAnchor="end"
              fontSize="10"
              fill="#9ca3af"
            >
              {new Date(prices[prices.length - 1].timestamp).toLocaleDateString()}
            </text>
          </>
        )}
      </svg>

      {/* Price range info */}
      <div className="flex justify-between text-xs text-gray-400 mt-2">
        <span>Low: {formatPrice(chartData.minPrice)}</span>
        <span>High: {formatPrice(chartData.maxPrice)}</span>
      </div>
    </div>
  );
}
