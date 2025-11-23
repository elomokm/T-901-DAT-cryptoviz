'use client';

import { Gauge } from 'lucide-react';
import { FearGreedResponse } from '@/types';
import { getFearGreedClass } from '@/lib/utils';

interface FearGreedGaugeProps {
  data: FearGreedResponse | null;
  loading?: boolean;
}

export default function FearGreedGauge({ data, loading }: FearGreedGaugeProps) {
  if (loading) {
    return (
      <div className="glass-card p-4 h-full">
        <div className="skeleton h-4 w-32 mb-4 rounded" />
        <div className="skeleton h-24 w-24 mx-auto rounded-full mb-4" />
        <div className="skeleton h-4 w-20 mx-auto rounded" />
      </div>
    );
  }

  const value = data?.value || 50;
  const classification = getFearGreedClass(value);

  // Calculate rotation for the gauge needle (-90 to 90 degrees)
  const rotation = (value / 100) * 180 - 90;

  return (
    <div className="glass-card p-4 h-full">
      <div className="flex items-center gap-2 mb-4">
        <Gauge className="w-4 h-4 text-blue-400" />
        <h3 className="text-sm font-medium text-gray-400">Fear & Greed Index</h3>
      </div>

      {/* Gauge Display */}
      <div className="relative flex flex-col items-center">
        {/* Semi-circle gauge */}
        <div className="relative w-32 h-16 overflow-hidden">
          {/* Background arc */}
          <div className="absolute inset-0">
            <div
              className="w-32 h-32 rounded-full"
              style={{
                background: `conic-gradient(
                  from 180deg,
                  #ef4444 0deg,
                  #f97316 45deg,
                  #eab308 90deg,
                  #84cc16 135deg,
                  #22c55e 180deg,
                  transparent 180deg
                )`,
              }}
            />
          </div>
          {/* Inner circle cutout */}
          <div className="absolute top-2 left-2 w-28 h-28 bg-gray-900 rounded-full" />

          {/* Needle */}
          <div
            className="absolute bottom-0 left-1/2 w-0.5 h-12 bg-white origin-bottom transition-transform duration-500"
            style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
          />

          {/* Center dot */}
          <div className="absolute bottom-0 left-1/2 w-2 h-2 -translate-x-1/2 translate-y-1/2 bg-white rounded-full" />
        </div>

        {/* Value and Label */}
        <div className="text-center mt-4">
          <p className="text-3xl font-bold">{value}</p>
          <p className={`text-sm font-medium ${classification.textColor}`}>
            {classification.label}
          </p>
        </div>

        {/* Legend */}
        <div className="flex justify-between w-full mt-4 text-xs text-gray-500">
          <span>Fear</span>
          <span>Greed</span>
        </div>
      </div>
    </div>
  );
}
