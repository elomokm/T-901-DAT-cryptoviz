'use client';

import { useMemo } from 'react';
import { PricePoint } from '@/types';

interface SparklineProps {
  data: PricePoint[];
  change?: number;
  width?: number;
  height?: number;
}

export default function Sparkline({
  data,
  change = 0,
  width = 120,
  height = 40,
}: SparklineProps) {
  const { path, color } = useMemo(() => {
    if (!data || data.length === 0) {
      return { path: '', color: '#6b7280' };
    }

    const prices = data.map((d) => d.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1;

    const padding = 2;
    const availableWidth = width - padding * 2;
    const availableHeight = height - padding * 2;

    const points = prices.map((price, i) => {
      const x = padding + (i / (prices.length - 1)) * availableWidth;
      const y = padding + availableHeight - ((price - minPrice) / priceRange) * availableHeight;
      return `${x},${y}`;
    });

    const pathString = `M ${points.join(' L ')}`;
    const lineColor = change >= 0 ? '#22c55e' : '#ef4444';

    return { path: pathString, color: lineColor };
  }, [data, change, width, height]);

  if (!data || data.length === 0) {
    return null;
  }

  return (
    <svg width={width} height={height} className="inline-block">
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
