import { useMemo } from 'react'

type Props = {
  hours: 24 | 168 | 720
  onHoursChange: (v: 24 | 168 | 720) => void
  searchValue: string
  onSearchChange: (v: string) => void
  apiUrl?: string
}

const presets: Array<{ label: string; value: 24 | 168 | 720 }> = [
  { label: '24h', value: 24 },
  { label: '7j', value: 168 },
  { label: '30j', value: 720 },
]

export default function Header({ hours, onHoursChange, searchValue, onSearchChange, apiUrl }: Props) {
  const presetSet = useMemo(() => new Set(presets.map(p => p.value)), [])
  const normalized = presetSet.has(hours) ? hours : 24

  return (
    <header className="sticky top-0 z-30 backdrop-blur bg-white/80 dark:bg-gray-950/70 border-b border-gray-200/70 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center gap-4">
          {/* Logo / Brand */}
          <div className="shrink-0 font-bold text-lg">
            Crypto Viz
          </div>

          {/* Onglets (placeholder façon CoinStats) */}
          <nav className="hidden md:flex items-center gap-2 text-sm">
            <a className="px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 font-medium" href="#">Marchés</a>
            <a className="px-3 py-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800" href="#">Watchlist</a>
            <a className="px-3 py-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800" href="#">Sources</a>
          </nav>

          {/* Recherche symbole */}
          <div className="flex-1">
            <input
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value.trim())}
              placeholder="Rechercher un symbole (ex: BTC, ETH)…"
              className="w-full md:max-w-md rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Sélecteur de période */}
          <div className="flex items-center gap-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-1">
            {presets.map(p => (
              <button
                key={p.value}
                onClick={() => onHoursChange(p.value)}
                className={
                  'px-3 py-1.5 rounded-lg text-sm ' +
                  (normalized === p.value
                    ? 'bg-white dark:bg-gray-900 shadow border border-gray-200 dark:border-gray-700 font-medium'
                    : 'text-gray-600 dark:text-gray-300 hover:opacity-90')
                }
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Info API (compact) */}
          {apiUrl ? (
            <div className="hidden lg:block text-[11px] text-gray-500">
              API: {apiUrl}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  )
}
