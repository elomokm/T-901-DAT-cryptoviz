"use client";

import { useEffect, useMemo, useState } from 'react';
import Sparkline from '@/components/Sparkline';
import { getCoinHistory, CoinHistoryResponse } from '@/lib/api';

type RangeKey = 'D' | 'W' | 'M' | 'Y';

function presetToParams(k: RangeKey): { days: number; interval: string } {
  switch (k) {
    case 'D': return { days: 1, interval: '5m' };
    case 'W': return { days: 7, interval: '1h' };
    case 'M': return { days: 30, interval: '4h' };
    case 'Y': return { days: 365, interval: '1d' };
  }
}

export default function CoinHistoryClient({ id }: { id: string }) {
  const [range, setRange] = useState<RangeKey>('W');
  const [data, setData] = useState<CoinHistoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const params = useMemo(() => presetToParams(range), [range]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getCoinHistory(id, params.days, params.interval)
      .then((res) => { if (alive) setData(res); })
      .catch((e) => console.error('history fetch error', e))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [id, params.days, params.interval]);

  const buttons: RangeKey[] = ['D','W','M','Y'];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {buttons.map((b) => (
          <button
            key={b}
            onClick={() => setRange(b)}
            className={`px-3 py-1.5 rounded-md text-sm border transition ${
              range === b
                ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                : 'bg-gray-800/50 text-gray-300 border-gray-700 hover:bg-gray-800'
            }`}
          >{b}</button>
        ))}
      </div>

      <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-4">
        {loading ? (
          <div className="h-40 animate-pulse bg-gray-800/50 rounded" />
        ) : (
          <Sparkline points={(data?.series || []).map(p => ({ time: p.time, value: p.value }))} width={800} height={180} />
        )}
      </div>
    </div>
  );
}
