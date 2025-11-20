"use client";

import Link from 'next/link';

const items = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/coin/bitcoin', label: 'BTC', icon: '₿' },
  { href: '/coin/ethereum', label: 'ETH', icon: '◇' },
  { href: '/fear-greed', label: 'Sentiment', icon: '🧠' },
];

export default function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col items-center gap-4 py-6 border-r border-gray-800/60 bg-gray-950/80 backdrop-blur-xl">
      <div className="text-xl font-bold text-white">💠</div>
      <nav className="flex flex-col gap-3">
        {items.map((it) => (
          <Link key={it.href} href={it.href} className="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-800/50 text-gray-300 hover:text-white transition">
            <span title={it.label}>{it.icon}</span>
          </Link>
        ))}
      </nav>
      <div className="mt-auto text-gray-600 text-xs">v0.1</div>
    </aside>
  );
}
