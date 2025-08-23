type Props = {
  items: any[]
  selectedSymbol?: string
  onSelectSymbol: (symbol: string) => void
}

function getSymbolLabel(raw: any): string {
  if (typeof raw === 'string') return raw
  return raw?.symbol || raw?.ticker || raw?.name || '—'
}
function getCount(raw: any): number {
  return Number(raw?.count ?? raw?.mentions ?? raw?.volume ?? 0)
}

export default function MarketsTable({ items, selectedSymbol, onSelectSymbol }: Props) {
  const rows = (items || []).map((it, idx) => ({
    rank: idx + 1,
    symbol: getSymbolLabel(it),
    count: getCount(it),
  }))

  // Tri façon “market cap” -> ici par count décroissant si dispo
  rows.sort((a, b) => b.count - a.count)

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur border-b border-gray-200/70 dark:border-gray-800">
          <tr className="text-left">
            <th className="px-4 py-3 w-14">#</th>
            <th className="px-4 py-3">Symbole</th>
            <th className="px-4 py-3">Mentions (proxy)</th>
            <th className="px-4 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-6 text-center text-gray-500">Aucune donnée</td>
            </tr>
          ) : rows.map((r) => {
            const active = selectedSymbol && r.symbol.toLowerCase() === selectedSymbol.toLowerCase()
            return (
              <tr key={r.symbol} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50/60 dark:hover:bg-gray-800/40">
                <td className="px-4 py-3 text-gray-500">{r.rank}</td>
                <td className="px-4 py-3 font-medium">
                  {r.symbol.toUpperCase()}
                </td>
                <td className="px-4 py-3">{r.count ? r.count.toLocaleString() : '—'}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onSelectSymbol(r.symbol)}
                    className={
                      'px-3 py-1.5 rounded-lg border text-xs ' +
                      (active
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800')
                    }
                  >
                    Voir mentions
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
