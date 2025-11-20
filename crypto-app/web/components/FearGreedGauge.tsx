'use client';

import React, { useEffect, useState } from 'react';
import { getFearGreed, ApiError } from '@/lib/api';
import { getFearGreedClass } from '@/lib/utils';

export default function FearGreedGauge() {
  const [value, setValue] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      try {
        const data = await getFearGreed();
        if (mounted) {
          setValue(data.value);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError('Failed to load Fear & Greed index');
          }
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-6 backdrop-blur-xl">
        <div className="text-gray-400 text-xs uppercase mb-4">Fear & Greed Index</div>
        <div className="flex items-center justify-center h-32">
          <div className="w-32 h-16 bg-gray-800/50 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || value === null) {
    return (
      <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-6 backdrop-blur-xl">
        <div className="text-gray-400 text-xs uppercase mb-4">Fear & Greed Index</div>
        <div className="text-center text-gray-500 py-8">
          {error || 'Not available'}
        </div>
      </div>
    );
  }

  const { label, color, bgColor } = getFearGreedClass(value);

  // Calculate needle rotation (0 = left, 100 = right)
  const rotation = -90 + (value / 100) * 180;

  return (
    <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-6 backdrop-blur-xl">
      <div className="text-gray-400 text-xs uppercase mb-4">Fear & Greed Index</div>

      <div className="relative flex flex-col items-center">
        {/* SVG Gauge */}
        <svg viewBox="0 0 200 120" className="w-full max-w-[200px]">
          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#374151"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Gradient arc - Extreme Fear to Extreme Greed */}
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="25%" stopColor="#f97316" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="75%" stopColor="#84cc16" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>

          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Needle */}
          <g transform={`rotate(${rotation}, 100, 100)`}>
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="35"
              stroke="white"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle cx="100" cy="100" r="6" fill="white" />
          </g>
        </svg>

        {/* Value display */}
        <div className="mt-4 text-center">
          <div className="text-3xl font-bold text-white">{value}</div>
          <div className={`mt-1 px-3 py-1 rounded-full text-sm font-medium ${color} ${bgColor}`}>
            {label}
          </div>
        </div>
      </div>
    </div>
  );
}
