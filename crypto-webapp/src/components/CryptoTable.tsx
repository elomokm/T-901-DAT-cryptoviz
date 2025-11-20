import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from './ui/card';
import { CoinSummary } from '@/lib/api';
import { formatPrice, formatLargeNumber, formatPercentage, getChangeColor } from '@/utils/formatters';
import { Skeleton } from './ui/skeleton';
import { ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';

interface CryptoTableProps {
  coins: CoinSummary[];
  loading: boolean;
}

type SortField = 'market_cap_rank' | 'price_usd' | 'change_24h' | 'volume_24h' | 'market_cap';
type SortOrder = 'asc' | 'desc';

export default function CryptoTable({ coins, loading }: CryptoTableProps) {
  const [sortField, setSortField] = useState<SortField>('market_cap_rank');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder(field === 'market_cap_rank' ? 'asc' : 'desc');
    }
  };

  const sortedCoins = [...coins].sort((a, b) => {
    const aVal = a[sortField] ?? 0;
    const bVal = b[sortField] ?? 0;
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown className="w-4 h-4 opacity-30" />;
    return sortOrder === 'asc' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <Card className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-border/50">
              <tr className="text-left text-sm text-muted-foreground">
                <th className="p-4 font-medium">#</th>
                <th className="p-4 font-medium">Name</th>
                <th className="p-4 font-medium text-right">Price</th>
                <th className="p-4 font-medium text-right hidden md:table-cell">24h %</th>
                <th className="p-4 font-medium text-right hidden lg:table-cell">7d %</th>
                <th className="p-4 font-medium text-right hidden xl:table-cell">Volume 24h</th>
                <th className="p-4 font-medium text-right hidden xl:table-cell">Market Cap</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((i) => (
                <tr key={i} className="border-b border-border/50">
                  <td className="p-4"><Skeleton className="h-4 w-8" /></td>
                  <td className="p-4"><Skeleton className="h-4 w-32" /></td>
                  <td className="p-4"><Skeleton className="h-4 w-24 ml-auto" /></td>
                  <td className="p-4 hidden md:table-cell"><Skeleton className="h-4 w-16 ml-auto" /></td>
                  <td className="p-4 hidden lg:table-cell"><Skeleton className="h-4 w-16 ml-auto" /></td>
                  <td className="p-4 hidden xl:table-cell"><Skeleton className="h-4 w-24 ml-auto" /></td>
                  <td className="p-4 hidden xl:table-cell"><Skeleton className="h-4 w-24 ml-auto" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    );
  }

  return (
    <Card className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b border-border/50 bg-secondary/30">
            <tr className="text-left text-sm text-muted-foreground">
              <th className="p-4 font-medium cursor-pointer hover:text-foreground transition-colors" onClick={() => handleSort('market_cap_rank')}>
                <div className="flex items-center gap-2">
                  # <SortIcon field="market_cap_rank" />
                </div>
              </th>
              <th className="p-4 font-medium">Name</th>
              <th className="p-4 font-medium text-right cursor-pointer hover:text-foreground transition-colors" onClick={() => handleSort('price_usd')}>
                <div className="flex items-center justify-end gap-2">
                  Price <SortIcon field="price_usd" />
                </div>
              </th>
              <th className="p-4 font-medium text-right cursor-pointer hover:text-foreground transition-colors hidden md:table-cell" onClick={() => handleSort('change_24h')}>
                <div className="flex items-center justify-end gap-2">
                  24h % <SortIcon field="change_24h" />
                </div>
              </th>
              <th className="p-4 font-medium text-right hidden lg:table-cell">7d %</th>
              <th className="p-4 font-medium text-right cursor-pointer hover:text-foreground transition-colors hidden xl:table-cell" onClick={() => handleSort('volume_24h')}>
                <div className="flex items-center justify-end gap-2">
                  Volume 24h <SortIcon field="volume_24h" />
                </div>
              </th>
              <th className="p-4 font-medium text-right cursor-pointer hover:text-foreground transition-colors hidden xl:table-cell" onClick={() => handleSort('market_cap')}>
                <div className="flex items-center justify-end gap-2">
                  Market Cap <SortIcon field="market_cap" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedCoins.map((coin) => (
              <tr key={coin.id} className="border-b border-border/50 hover:bg-secondary/20 transition-colors">
                <td className="p-4 text-muted-foreground">{coin.market_cap_rank || '-'}</td>
                <td className="p-4">
                  <Link to={`/coin/${coin.id}`} className="flex items-center gap-3 hover:text-primary transition-colors">
                    <div>
                      <div className="font-semibold">{coin.name}</div>
                      <div className="text-xs text-muted-foreground uppercase">{coin.symbol}</div>
                    </div>
                  </Link>
                </td>
                <td className="p-4 text-right font-mono">{formatPrice(coin.price_usd)}</td>
                <td className={`p-4 text-right font-medium hidden md:table-cell ${getChangeColor(coin.change_24h)}`}>
                  {formatPercentage(coin.change_24h)}
                </td>
                <td className={`p-4 text-right font-medium hidden lg:table-cell ${getChangeColor(coin.change_7d)}`}>
                  {formatPercentage(coin.change_7d)}
                </td>
                <td className="p-4 text-right hidden xl:table-cell">{formatLargeNumber(coin.volume_24h || 0)}</td>
                <td className="p-4 text-right hidden xl:table-cell">{formatLargeNumber(coin.market_cap || 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
