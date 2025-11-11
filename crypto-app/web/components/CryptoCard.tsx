/**
 * CryptoCard Component
 * 
 * Carte avec effet glassmorphism pour afficher crypto dans Top Gainers/Losers
 * Style inspiré de Cryptic.com
 */

'use client';

import PriceDisplay from './PriceDisplay';

interface CryptoCardProps {
  crypto: string;
  symbol?: string;
  name?: string;
  currentPrice: number;
  change24h: number;
  variant?: 'gainer' | 'loser' | 'neutral';
  rank?: number;
}

export default function CryptoCard({
  crypto,
  symbol,
  name,
  currentPrice,
  change24h,
  variant = 'neutral',
  rank
}: CryptoCardProps) {
  // Gradient border selon variant
  const borderGradient = {
    gainer: 'from-green-500/50 to-emerald-500/50',
    loser: 'from-red-500/50 to-rose-500/50',
    neutral: 'from-blue-500/30 to-purple-500/30'
  };

  // Symbol par défaut (première lettre uppercase)
  const displaySymbol = symbol || crypto.substring(0, 3).toUpperCase();
  const displayName = name || crypto.charAt(0).toUpperCase() + crypto.slice(1);

  return (
    <div className="group relative">
      {/* Gradient border */}
      <div className={`absolute -inset-0.5 bg-gradient-to-r ${borderGradient[variant]} rounded-xl blur opacity-50 group-hover:opacity-75 transition duration-300`}></div>
      
      {/* Card content - glassmorphism */}
      <div className="relative bg-gray-900/80 backdrop-blur-xl rounded-xl p-5 border border-gray-800/50 hover:border-gray-700/50 transition-all duration-300">
        
        {/* Rank badge (si fourni) */}
        {rank && (
          <div className="absolute top-3 right-3 bg-gray-800/60 backdrop-blur-sm px-2 py-1 rounded-md text-xs text-gray-400">
            #{rank}
          </div>
        )}
        
        {/* Header: Symbol + Name */}
        <div className="flex items-center gap-3 mb-4">
          {/* Icon placeholder - sera remplacé par vraie icon plus tard */}
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${borderGradient[variant]} flex items-center justify-center text-white font-bold text-sm`}>
            {displaySymbol.charAt(0)}
          </div>
          
          <div>
            <div className="text-white font-semibold text-sm">{displaySymbol}</div>
            <div className="text-gray-400 text-xs">{displayName}</div>
          </div>
        </div>
        
        {/* Price + Change */}
        <div className="space-y-1">
          <PriceDisplay 
            price={currentPrice} 
            change={change24h}
            size="md"
          />
          
          {/* 24h label */}
          <div className="text-xs text-gray-500">24h Change</div>
        </div>
        
        {/* Hover effect: subtle shine */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl pointer-events-none"></div>
      </div>
    </div>
  );
}
