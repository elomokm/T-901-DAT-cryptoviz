import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCoin, getCoinHistory, CoinSummary, CoinHistoryResponse } from '@/lib/api';
import Header from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import {
  formatPrice,
  formatLargeNumber,
  formatPercentage,
  getChangeColor,
  formatSupply,
} from '@/utils/formatters';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

type Period = '1d' | '7d' | '30d' | '365d';

const periodConfig = {
  '1d': { days: 1, interval: '15m', label: '1 Day' },
  '7d': { days: 7, interval: '1h', label: '7 Days' },
  '30d': { days: 30, interval: '4h', label: '30 Days' },
  '365d': { days: 365, interval: '1d', label: '1 Year' },
};

export default function CoinDetail() {
  const { id } = useParams<{ id: string }>();
  const [coin, setCoin] = useState<CoinSummary | null>(null);
  const [history, setHistory] = useState<CoinHistoryResponse | null>(null);
  const [period, setPeriod] = useState<Period>('7d');
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    const fetchCoin = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const data = await getCoin(id);
        setCoin(data);
      } catch (error) {
        console.error('Failed to fetch coin:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCoin();
  }, [id]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!id) return;
      try {
        setHistoryLoading(true);
        const config = periodConfig[period];
        const data = await getCoinHistory(id, config.days, config.interval);
        setHistory(data);
      } catch (error) {
        console.error('Failed to fetch history:', error);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [id, period]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Skeleton className="h-8 w-64 mb-8" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Skeleton className="h-96 w-full" />
            </div>
            <div>
              <Skeleton className="h-96 w-full" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!coin) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Card className="glass-card">
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-4">Cryptocurrency not found</p>
              <Link to="/">
                <Button variant="outline">Return to Dashboard</Button>
              </Link>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  const chartData = history?.series.map((point) => ({
    time: new Date(point.time).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: period === '1d' ? '2-digit' : undefined,
      minute: period === '1d' ? '2-digit' : undefined,
    }),
    price: point.value,
  })) || [];

  const priceChange = coin.change_24h || 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="min-h-screen">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Back button */}
        <Link to="/">
          <Button variant="ghost" size="sm" className="mb-6 gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </Link>

        {/* Coin header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <h1 className="text-4xl font-bold">{coin.name}</h1>
            <span className="text-2xl text-muted-foreground uppercase">{coin.symbol}</span>
            {coin.market_cap_rank && (
              <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                Rank #{coin.market_cap_rank}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-4">
            <span className="text-4xl font-bold">{formatPrice(coin.price_usd)}</span>
            <span className={`text-xl font-semibold flex items-center gap-1 ${getChangeColor(coin.change_24h)}`}>
              {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              {formatPercentage(coin.change_24h)} (24h)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart */}
          <div className="lg:col-span-2">
            <Card className="glass-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Price Chart</CardTitle>
                  <div className="flex gap-2">
                    {(Object.keys(periodConfig) as Period[]).map((p) => (
                      <Button
                        key={p}
                        variant={period === p ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPeriod(p)}
                      >
                        {periodConfig[p].label}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {historyLoading ? (
                  <div className="h-80 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                  </div>
                ) : chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis
                        dataKey="time"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value.toLocaleString()}`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                        }}
                        formatter={(value: number) => [formatPrice(value), 'Price']}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                        fill="url(#colorPrice)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-80 flex items-center justify-center text-muted-foreground">
                    No chart data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Stats sidebar */}
          <div className="space-y-6">
            {/* Market Stats */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-lg">Market Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Market Cap</div>
                  <div className="text-lg font-semibold">{formatLargeNumber(coin.market_cap || 0)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Volume 24h</div>
                  <div className="text-lg font-semibold">{formatLargeNumber(coin.volume_24h || 0)}</div>
                </div>
                <div className="border-t border-border/50 pt-4">
                  <div className="text-sm text-muted-foreground mb-1">Circulating Supply</div>
                  <div className="text-lg font-semibold">
                    {formatSupply(coin.circulating_supply)} {coin.symbol}
                  </div>
                </div>
                {coin.max_supply && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Max Supply</div>
                    <div className="text-lg font-semibold">
                      {formatSupply(coin.max_supply)} {coin.symbol}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Price Changes */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-lg">Price Changes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">1 Hour</span>
                  <span className={`font-semibold ${getChangeColor(coin.change_1h)}`}>
                    {formatPercentage(coin.change_1h)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">24 Hours</span>
                  <span className={`font-semibold ${getChangeColor(coin.change_24h)}`}>
                    {formatPercentage(coin.change_24h)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">7 Days</span>
                  <span className={`font-semibold ${getChangeColor(coin.change_7d)}`}>
                    {formatPercentage(coin.change_7d)}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* ATH/ATL */}
            {(coin.ath || coin.atl) && (
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-lg">All-Time</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {coin.ath && (
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">All-Time High</div>
                      <div className="text-lg font-semibold">{formatPrice(coin.ath)}</div>
                      {coin.ath_change_pct !== undefined && (
                        <div className="text-sm text-danger mt-1">
                          {formatPercentage(coin.ath_change_pct)} from ATH
                        </div>
                      )}
                    </div>
                  )}
                  {coin.atl && (
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">All-Time Low</div>
                      <div className="text-lg font-semibold">{formatPrice(coin.atl)}</div>
                      {coin.atl_change_pct !== undefined && (
                        <div className="text-sm text-success mt-1">
                          {formatPercentage(coin.atl_change_pct)} from ATL
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
