import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { FearGreedClassification } from '@/types';

/**
 * Merge Tailwind CSS classes with clsx
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a price in USD with appropriate decimal places
 */
export function formatPrice(price: number | undefined | null): string {
  if (price === undefined || price === null) return '$0.00';

  if (price >= 1000) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  } else if (price >= 1) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(price);
  } else if (price >= 0.01) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 6,
    }).format(price);
  } else {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 6,
      maximumFractionDigits: 8,
    }).format(price);
  }
}

/**
 * Format large numbers with T/B/M/K suffixes
 */
export function formatLargeNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return '$0';

  const absNum = Math.abs(num);
  const sign = num < 0 ? '-' : '';

  if (absNum >= 1e12) {
    return `${sign}$${(absNum / 1e12).toFixed(2)}T`;
  } else if (absNum >= 1e9) {
    return `${sign}$${(absNum / 1e9).toFixed(2)}B`;
  } else if (absNum >= 1e6) {
    return `${sign}$${(absNum / 1e6).toFixed(2)}M`;
  } else if (absNum >= 1e3) {
    return `${sign}$${(absNum / 1e3).toFixed(2)}K`;
  } else {
    return `${sign}$${absNum.toFixed(2)}`;
  }
}

/**
 * Format a percentage with sign
 */
export function formatPercent(percent: number | undefined | null): string {
  if (percent === undefined || percent === null) return '0.00%';

  const formatted = Math.abs(percent).toFixed(2);
  const sign = percent >= 0 ? '+' : '-';

  return `${sign}${formatted}%`;
}

/**
 * Get Tailwind color class for positive/negative changes
 */
export function getChangeColor(value: number | undefined | null): string {
  if (value === undefined || value === null || value === 0) {
    return 'text-gray-400';
  }
  return value > 0 ? 'text-green-400' : 'text-red-400';
}

/**
 * Get background color class for positive/negative changes
 */
export function getChangeBgColor(value: number | undefined | null): string {
  if (value === undefined || value === null || value === 0) {
    return 'bg-gray-400/10';
  }
  return value > 0 ? 'bg-green-400/10' : 'bg-red-400/10';
}

/**
 * Format relative time (e.g., "5 minutes ago")
 */
export function formatRelativeTime(dateString: string): string {
  if (!dateString || dateString === '') {
    return 'N/A';
  }
  
  const date = new Date(dateString);
  
  // Vérifier si la date est valide
  if (isNaN(date.getTime())) {
    return 'N/A';
  }
  
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} ${days === 1 ? 'day' : 'days'} ago`;
  } else if (diffInSeconds < 2592000) {
    const weeks = Math.floor(diffInSeconds / 604800);
    return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`;
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  }
}

/**
 * Format supply with symbol
 */
export function formatSupply(supply: number | undefined | null, symbol: string): string {
  if (supply === undefined || supply === null) return 'N/A';

  const absNum = Math.abs(supply);

  if (absNum >= 1e12) {
    return `${(absNum / 1e12).toFixed(2)}T ${symbol.toUpperCase()}`;
  } else if (absNum >= 1e9) {
    return `${(absNum / 1e9).toFixed(2)}B ${symbol.toUpperCase()}`;
  } else if (absNum >= 1e6) {
    return `${(absNum / 1e6).toFixed(2)}M ${symbol.toUpperCase()}`;
  } else if (absNum >= 1e3) {
    return `${(absNum / 1e3).toFixed(2)}K ${symbol.toUpperCase()}`;
  } else {
    return `${absNum.toFixed(2)} ${symbol.toUpperCase()}`;
  }
}

/**
 * Get Fear & Greed classification with colors
 */
export function getFearGreedClass(value: number): FearGreedClassification {
  if (value <= 20) {
    return {
      label: 'Extreme Fear',
      color: '#ef4444',
      bgColor: 'bg-red-500/20',
      textColor: 'text-red-400',
    };
  } else if (value <= 40) {
    return {
      label: 'Fear',
      color: '#f97316',
      bgColor: 'bg-orange-500/20',
      textColor: 'text-orange-400',
    };
  } else if (value <= 60) {
    return {
      label: 'Neutral',
      color: '#eab308',
      bgColor: 'bg-yellow-500/20',
      textColor: 'text-yellow-400',
    };
  } else if (value <= 80) {
    return {
      label: 'Greed',
      color: '#84cc16',
      bgColor: 'bg-lime-500/20',
      textColor: 'text-lime-400',
    };
  } else {
    return {
      label: 'Extreme Greed',
      color: '#22c55e',
      bgColor: 'bg-green-500/20',
      textColor: 'text-green-400',
    };
  }
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
