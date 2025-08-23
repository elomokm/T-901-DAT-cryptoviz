type Props = {
  totalArticles: number
  avgSentiment: number
  sourcesCount: number
  topSymbol: string
}

function formatNumber(n: number) {
  if (Number.isNaN(n)) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k'
  return String(Math.round(n))
}

export default function StatsStrip({ totalArticles, avgSentiment, sourcesCount, topSymbol }: Props) {
  return (
    <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/70 dark:border-gray-800 p-4">
        <div className="text-xs text-gray-500">Articles</div>
        <div className="text-2xl font-semibold">{formatNumber(totalArticles)}</div>
      </div>
      <div className="rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/70 dark:border-gray-800 p-4">
        <div className="text-xs text-gray-500">Sentiment moyen</div>
        <div className="text-2xl font-semibold">{avgSentiment.toFixed(2)}</div>
      </div>
      <div className="rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/70 dark:border-gray-800 p-4">
        <div className="text-xs text-gray-500">Sources actives</div>
        <div className="text-2xl font-semibold">{formatNumber(sourcesCount)}</div>
      </div>
      <div className="rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/70 dark:border-gray-800 p-4">
        <div className="text-xs text-gray-500">Top symbole</div>
        <div className="text-2xl font-semibold">{topSymbol}</div>
      </div>
    </section>
  )
}
