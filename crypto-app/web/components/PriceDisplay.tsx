/**
 * PriceDisplay Component
 * 
 * Affiche un prix avec variation colorée (vert/rouge)
 * Style: Cryptic.com dark mode
 */

import React from 'react';

interface PriceDisplayProps {
  price: number;
  change?: number;
  showSign?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showChangePercent?: boolean;
}

export default function PriceDisplay({
  price,
  change,
  showSign = true,
  size = 'md',
  showChangePercent = true
}: PriceDisplayProps) {
  const isPositive = change !== undefined && change >= 0;
  const isNegative = change !== undefined && change < 0;
  
  // Format price selon la valeur (crypto < $1 = 8 décimales, sinon 2)
  const formatPrice = (value: number): string => {
    if (value < 0.01) {
      return `$${value.toFixed(8)}`;
    } else if (value < 1) {
      return `$${value.toFixed(6)}`;
    } else {
      return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
  };

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-lg font-semibold',
    lg: 'text-2xl font-bold'
  };

  const changeColorClasses = isPositive 
    ? 'text-green-400' 
    : isNegative 
    ? 'text-red-400' 
    : 'text-gray-400';

  return (
    <div className="flex items-center gap-2">
      <span className={`${sizeClasses[size]} text-white`}>
        {formatPrice(price)}
      </span>
      
      {change !== undefined && showChangePercent && (
        <span className={`${sizeClasses[size === 'lg' ? 'md' : 'sm']} ${changeColorClasses} flex items-center gap-1`}>
          {showSign && (
            <span className="text-xs">
              {isPositive ? '▲' : isNegative ? '▼' : ''}
            </span>
          )}
          {showSign && isPositive && '+'}
          {change.toFixed(2)}%
        </span>
      )}
    </div>
  );
}
