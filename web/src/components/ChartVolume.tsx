import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts'

type Point = { bucket: string; value: number; source?: string }

export default function ChartVolume({ data }: { data: Point[] }) {
  // Transforme en séries par source
  const sources = Array.from(new Set(data.map(d => d.source || 'unknown')))
  const byBucket = new Map<string, any>()
  for (const d of data) {
    const k = d.bucket
    if (!byBucket.has(k)) byBucket.set(k, { bucket: k })
    byBucket.get(k)[d.source || 'unknown'] = d.value
  }
  const series = Array.from(byBucket.values())

  return (
    <div className="h-80 bg-white rounded-2xl shadow p-4">
      <h2 className="text-lg font-semibold mb-2">Volume d’articles par minute (par source)</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series}>
          <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Legend />
          {sources.map((s) => (
            <Line key={s} type="monotone" dataKey={s} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
