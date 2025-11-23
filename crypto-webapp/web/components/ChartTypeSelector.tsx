'use client';

import { LineChart, BarChart3, AreaChart, CandlestickChart } from 'lucide-react';

export type ChartType = 'line' | 'area' | 'bar' | 'candlestick';

interface ChartTypeSelectorProps {
  selected: ChartType;
  onChange: (type: ChartType) => void;
}

const chartTypes = [
  { type: 'line' as ChartType, icon: LineChart, label: 'Line' },
  { type: 'area' as ChartType, icon: AreaChart, label: 'Area' },
  { type: 'bar' as ChartType, icon: BarChart3, label: 'Bar' },
  { type: 'candlestick' as ChartType, icon: CandlestickChart, label: 'Candles' },
];

export default function ChartTypeSelector({ selected, onChange }: ChartTypeSelectorProps) {
  return (
    <div className="flex gap-2 p-1 bg-gray-800/50 rounded-lg">
      {chartTypes.map(({ type, icon: Icon, label }) => (
        <button
          key={type}
          onClick={() => onChange(type)}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-md transition-all
            ${
              selected === type
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
            }
          `}
          title={label}
        >
          <Icon className="w-4 h-4" />
          <span className="text-sm font-medium hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}
