import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { getFearGreed, FearGreedResponse } from '@/lib/api';
import { Skeleton } from './ui/skeleton';
import { AlertCircle } from 'lucide-react';

export default function FearGreedGauge() {
  const [data, setData] = useState<FearGreedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(false);
        const result = await getFearGreed();
        setData(result);
      } catch (err) {
        console.error('Failed to fetch Fear & Greed:', err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const getSentiment = (value: number) => {
    if (value <= 25) return { label: 'Extreme Fear', color: 'text-red-500' };
    if (value <= 45) return { label: 'Fear', color: 'text-orange-500' };
    if (value <= 55) return { label: 'Neutral', color: 'text-yellow-500' };
    if (value <= 75) return { label: 'Greed', color: 'text-lime-500' };
    return { label: 'Extreme Greed', color: 'text-green-500' };
  };

  const getGaugeColor = (value: number) => {
    if (value <= 25) return '#ef4444';
    if (value <= 45) return '#f97316';
    if (value <= 55) return '#eab308';
    if (value <= 75) return '#84cc16';
    return '#22c55e';
  };

  if (loading) {
    return (
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Fear & Greed Index</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-8">
          <Skeleton className="w-40 h-40 rounded-full mb-4" />
          <Skeleton className="h-6 w-32" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Fear & Greed Index</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-8 text-muted-foreground">
          <AlertCircle className="w-12 h-12 mb-2" />
          <p className="text-sm">Data unavailable</p>
        </CardContent>
      </Card>
    );
  }

  const sentiment = getSentiment(data.value);
  const rotation = (data.value / 100) * 180 - 90;

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-lg">Fear & Greed Index</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center py-6">
        <div className="relative w-48 h-24 mb-6">
          {/* Gauge background */}
          <svg className="w-full h-full" viewBox="0 0 200 100">
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
              d="M 20 90 A 80 80 0 0 1 180 90"
              fill="none"
              stroke="url(#gaugeGradient)"
              strokeWidth="16"
              strokeLinecap="round"
              opacity="0.3"
            />
            <path
              d="M 20 90 A 80 80 0 0 1 180 90"
              fill="none"
              stroke="url(#gaugeGradient)"
              strokeWidth="16"
              strokeLinecap="round"
              strokeDasharray={`${(data.value / 100) * 251.2} 251.2`}
            />
          </svg>
          {/* Needle */}
          <div
            className="absolute top-[70%] left-1/2 w-1 h-16 bg-foreground origin-bottom transition-transform duration-1000"
            style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
          >
            <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-foreground" />
          </div>
          {/* Center value */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
            <div className="text-4xl font-bold" style={{ color: getGaugeColor(data.value) }}>
              {Math.round(data.value)}
            </div>
          </div>
        </div>

        <div className="text-center">
          <p className={`text-xl font-semibold ${sentiment.color} mb-1`}>
            {sentiment.label}
          </p>
          <p className="text-xs text-muted-foreground">
            Market Sentiment
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
