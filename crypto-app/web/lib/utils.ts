/**
 * Utilitaires pour CryptoViz
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combine les classes Tailwind intelligemment
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formate un prix en USD
 * - < $0.01: 8 décimales
 * - < $1: 6 décimales
 * - >= $1: 2 décimales avec séparateur
 */
export function formatPrice(price: number | undefined | null): string {
  if (price === undefined || price === null) return '$0.00';

  if (price < 0.01) {
    return `$${price.toFixed(8)}`;
  }
  if (price < 1) {
    return `$${price.toFixed(6)}`;
  }
  return `$${price.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Formate un grand nombre (market cap, volume)
 * >= 1T: $X.XXT
 * >= 1B: $X.XXB
 * >= 1M: $X.XXM
 */
export function formatLargeNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return '$0';

  if (num >= 1e12) {
    return `$${(num / 1e12).toFixed(2)}T`;
  }
  if (num >= 1e9) {
    return `$${(num / 1e9).toFixed(2)}B`;
  }
  if (num >= 1e6) {
    return `$${(num / 1e6).toFixed(2)}M`;
  }
  return `$${num.toLocaleString('en-US')}`;
}

/**
 * Formate un pourcentage avec couleur
 */
export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Retourne la classe de couleur pour un changement
 */
export function getChangeColor(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'text-gray-400';
  if (value > 0) return 'text-green-500';
  if (value < 0) return 'text-red-500';
  return 'text-gray-400';
}

/**
 * Formate une date relative (5m ago, 2h ago, etc.)
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Formate un supply avec le symbole
 */
export function formatSupply(value: number | undefined | null, symbol?: string): string {
  if (value === undefined || value === null) return '-';

  const formatted = value.toLocaleString('en-US', {
    maximumFractionDigits: 0,
  });

  return symbol ? `${formatted} ${symbol}` : formatted;
}

/**
 * Tronque un texte avec ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Génère une couleur basée sur un string (pour badges)
 */
export function stringToColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 70%, 50%)`;
}

/**
 * Classe Fear & Greed selon la valeur
 */
export function getFearGreedClass(value: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (value <= 25) {
    return { label: 'Extreme Fear', color: 'text-red-500', bgColor: 'bg-red-500/20' };
  }
  if (value <= 45) {
    return { label: 'Fear', color: 'text-orange-500', bgColor: 'bg-orange-500/20' };
  }
  if (value <= 55) {
    return { label: 'Neutral', color: 'text-yellow-500', bgColor: 'bg-yellow-500/20' };
  }
  if (value <= 75) {
    return { label: 'Greed', color: 'text-lime-500', bgColor: 'bg-lime-500/20' };
  }
  return { label: 'Extreme Greed', color: 'text-green-500', bgColor: 'bg-green-500/20' };
}
