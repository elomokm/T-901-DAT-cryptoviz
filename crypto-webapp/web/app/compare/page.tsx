'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, TrendingUp, TrendingDown, Activity, BarChart3, AlertTriangle } from 'lucide-react';
import { getCoins, compareCryptos } from '@/lib/api';
import { CoinSummary, ComparisonResult, ComparisonCriterion } from '@/types';

const CRITERIA_OPTIONS = [
  { value: 'volatility', label: 'Volatilité', description: 'Mesure la variation du prix', icon: Activity },
  { value: 'volume', label: 'Volume', description: 'Volume moyen de trading', icon: BarChart3 },
  { value: 'price', label: 'Prix', description: 'Prix moyen', icon: TrendingUp },
  { value: 'price_range', label: 'Amplitude', description: 'Écart min/max du prix', icon: TrendingDown },
  { value: 'anomalies', label: 'Anomalies', description: 'Nombre d\'anomalies détectées', icon: AlertTriangle },
] as const;

const PERIOD_OPTIONS = [
  { value: '1h', label: '1 Heure' },
  { value: '24h', label: '24 Heures' },
  { value: '7d', label: '7 Jours' },
  { value: '30d', label: '30 Jours' },
] as const;

export default function ComparePage() {
  const [availableCoins, setAvailableCoins] = useState<CoinSummary[]>([]);
  const [selectedCoins, setSelectedCoins] = useState<string[]>([]);
  const [period, setPeriod] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [criterion, setCriterion] = useState<ComparisonCriterion>('volatility');
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Charger la liste des cryptos disponibles
  useEffect(() => {
    const loadCoins = async () => {
      try {
        const coins = await getCoins({ per_page: 50 });
        setAvailableCoins(coins);
        // Sélectionner automatiquement Bitcoin et Ethereum
        if (coins.length >= 2) {
          setSelectedCoins([coins[0].id, coins[1].id]);
        }
      } catch (err) {
        console.error('Error loading coins:', err);
        setError('Impossible de charger la liste des cryptos');
      }
    };
    loadCoins();
  }, []);

  // Comparer les cryptos sélectionnées
  const handleCompare = async () => {
    if (selectedCoins.length < 2) {
      setError('Veuillez sélectionner au moins 2 cryptos');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await compareCryptos(selectedCoins, period);
      setComparisonData(result);
    } catch (err) {
      console.error('Error comparing cryptos:', err);
      setError('Erreur lors de la comparaison. Vérifiez que le consumer analytics est actif.');
    } finally {
      setLoading(false);
    }
  };

  // Toggle selection d'une crypto
  const toggleCoin = (coinId: string) => {
    setSelectedCoins(prev => {
      if (prev.includes(coinId)) {
        return prev.filter(id => id !== coinId);
      } else if (prev.length < 10) {
        return [...prev, coinId];
      }
      return prev;
    });
  };

  // Obtenir la valeur du critère pour une crypto
  const getCriterionValue = (crypto: any): number => {
    switch (criterion) {
      case 'volatility':
        return crypto.volatility_pct;
      case 'volume':
        return crypto.volume_mean;
      case 'price':
        return crypto.price_mean;
      case 'price_range':
        return crypto.price_range;
      case 'anomalies':
        return crypto.anomaly_count;
      default:
        return 0;
    }
  };

  // Formater la valeur selon le critère
  const formatValue = (value: number): string => {
    switch (criterion) {
      case 'volatility':
        return `${value.toFixed(2)}%`;
      case 'volume':
      case 'price':
      case 'price_range':
        return `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
      case 'anomalies':
        return value.toString();
      default:
        return value.toString();
    }
  };

  // Lancer automatiquement la comparaison quand les coins changent
  useEffect(() => {
    if (selectedCoins.length >= 2) {
      handleCompare();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCoins, period]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <Link
          href="/"
          className="inline-flex items-center text-purple-300 hover:text-purple-100 transition-colors mb-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Retour au tableau de bord
        </Link>
        
        <h1 className="text-4xl font-bold text-white mb-2">
          🔍 Comparaison de Cryptos
        </h1>
        <p className="text-gray-300">
          Comparez plusieurs cryptomonnaies selon différents critères analytiques
        </p>
      </div>

      {/* Controls */}
      <div className="max-w-7xl mx-auto mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Period Selection */}
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">📅 Période</h2>
          <div className="grid grid-cols-2 gap-3">
            {PERIOD_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setPeriod(opt.value)}
                className={`p-3 rounded-lg transition-all ${
                  period === opt.value
                    ? 'bg-purple-500 text-white shadow-lg'
                    : 'bg-white/5 text-gray-300 hover:bg-white/10'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Criterion Selection */}
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">📊 Critère</h2>
          <div className="space-y-2">
            {CRITERIA_OPTIONS.map(opt => {
              const Icon = opt.icon;
              return (
                <button
                  key={opt.value}
                  onClick={() => setCriterion(opt.value as ComparisonCriterion)}
                  className={`w-full p-3 rounded-lg flex items-center transition-all ${
                    criterion === opt.value
                      ? 'bg-purple-500 text-white shadow-lg'
                      : 'bg-white/5 text-gray-300 hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <div className="text-left">
                    <div className="font-semibold">{opt.label}</div>
                    <div className="text-xs opacity-75">{opt.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Crypto Selection */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">
            💰 Sélectionner les cryptos ({selectedCoins.length}/10)
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {availableCoins.slice(0, 20).map(coin => (
              <button
                key={coin.id}
                onClick={() => toggleCoin(coin.id)}
                disabled={!selectedCoins.includes(coin.id) && selectedCoins.length >= 10}
                className={`p-3 rounded-lg transition-all ${
                  selectedCoins.includes(coin.id)
                    ? 'bg-purple-500 text-white shadow-lg'
                    : 'bg-white/5 text-gray-300 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed'
                }`}
              >
                <div className="font-semibold">{coin.symbol.toUpperCase()}</div>
                <div className="text-xs opacity-75 truncate">{coin.name}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-8">
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200">
            ⚠️ {error}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="max-w-7xl mx-auto text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
          <p className="text-gray-300 mt-4">Analyse en cours...</p>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonData && !loading && (
        <div className="max-w-7xl mx-auto">
          <div className="glass-card p-6 mb-8">
            <h2 className="text-2xl font-bold text-white mb-6">
              📈 Résultats de la Comparaison
            </h2>

            {/* Comparison Chart */}
            <div className="space-y-4">
              {comparisonData.cryptos
                .sort((a, b) => getCriterionValue(b) - getCriterionValue(a))
                .map((crypto, index) => {
                  const value = getCriterionValue(crypto);
                  const maxValue = Math.max(...comparisonData.cryptos.map(getCriterionValue));
                  const percentage = (value / maxValue) * 100;

                  return (
                    <div key={crypto.crypto_id} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center space-x-3">
                          <span className="text-2xl font-bold text-purple-400">
                            #{index + 1}
                          </span>
                          <div>
                            <div className="font-semibold text-white">
                              {crypto.name} ({crypto.symbol.toUpperCase()})
                            </div>
                            <div className="text-sm text-gray-400">
                              {crypto.data_points} points de données
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-bold text-white">
                            {formatValue(value)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="relative h-8 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>

                      {/* Additional Stats */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                        <div className="bg-white/5 rounded p-2">
                          <div className="text-gray-400">Prix Moyen</div>
                          <div className="text-white font-semibold">
                            ${crypto.price_mean.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                          </div>
                        </div>
                        <div className="bg-white/5 rounded p-2">
                          <div className="text-gray-400">Volatilité</div>
                          <div className="text-white font-semibold">
                            {crypto.volatility_pct.toFixed(2)}%
                          </div>
                        </div>
                        <div className="bg-white/5 rounded p-2">
                          <div className="text-gray-400">Amplitude</div>
                          <div className="text-white font-semibold">
                            ${crypto.price_range.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                          </div>
                        </div>
                        <div className="bg-white/5 rounded p-2">
                          <div className="text-gray-400">Anomalies</div>
                          <div className="text-white font-semibold">
                            {crypto.anomaly_count}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Rankings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-red-400" />
                Plus Volatiles
              </h3>
              <ol className="space-y-2">
                {comparisonData.rankings.most_volatile.slice(0, 5).map((id, idx) => {
                  const crypto = comparisonData.cryptos.find(c => c.crypto_id === id);
                  return crypto ? (
                    <li key={id} className="text-gray-300">
                      {idx + 1}. {crypto.symbol.toUpperCase()} - {crypto.volatility_pct.toFixed(2)}%
                    </li>
                  ) : null;
                })}
              </ol>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
                Plus Gros Volumes
              </h3>
              <ol className="space-y-2">
                {comparisonData.rankings.highest_volume.slice(0, 5).map((id, idx) => {
                  const crypto = comparisonData.cryptos.find(c => c.crypto_id === id);
                  return crypto ? (
                    <li key={id} className="text-gray-300">
                      {idx + 1}. {crypto.symbol.toUpperCase()} - ${(crypto.volume_mean / 1e9).toFixed(2)}B
                    </li>
                  ) : null;
                })}
              </ol>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
                Prix les Plus Élevés
              </h3>
              <ol className="space-y-2">
                {comparisonData.rankings.highest_price.slice(0, 5).map((id, idx) => {
                  const crypto = comparisonData.cryptos.find(c => c.crypto_id === id);
                  return crypto ? (
                    <li key={id} className="text-gray-300">
                      {idx + 1}. {crypto.symbol.toUpperCase()} - ${crypto.price_mean.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                    </li>
                  ) : null;
                })}
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
