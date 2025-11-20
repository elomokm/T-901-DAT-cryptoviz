'use client';

import { formatPrice } from '@/lib/utils';

interface PriceRangeBarProps {
  low: number;
  high: number;
  current: number;
  className?: string;
}

export default function PriceRangeBar({ low, high, current, className = '' }: PriceRangeBarProps) {
  // Calculate percentage position of current price
  const range = high - low;
  const position = range > 0 ? ((current - low) / range) * 100 : 50;
  
  // Ensure position is between 0 and 100
  const clampedPosition = Math.max(0, Math.min(100, position));
  
  // Determine color based on position
  const getColor = () => {
    if (clampedPosition < 33) return 'from-red-500 to-yellow-500';
    if (clampedPosition < 66) return 'from-yellow-500 to-green-500';
    return 'from-green-400 to-green-600';
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>24h Range</span>
        <span className="text-white font-medium">{formatPrice(current)}</span>
      </div>
      
      <div className="relative">
        {/* Background bar */}
        <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
          {/* Gradient fill */}
          <div
            className={`h-full bg-gradient-to-r ${getColor()} transition-all duration-500`}
            style={{ width: `${clampedPosition}%` }}
          />
        </div>
        
        {/* Current price indicator */}
        <div
          className="absolute top-1/2 -translate-y-1/2 transition-all duration-500"
          style={{ left: `${clampedPosition}%` }}
        >
          <div className="relative -translate-x-1/2">
            {/* Triangle pointer */}
            <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-white" />
          </div>
        </div>
      </div>
      
      {/* Low and High labels */}
      <div className="flex justify-between text-xs">
        <span className="text-red-400">{formatPrice(low)}</span>
        <span className="text-green-400">{formatPrice(high)}</span>
      </div>
    </div>
  );
}
