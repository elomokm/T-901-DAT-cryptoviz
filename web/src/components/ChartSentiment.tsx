import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

type Point = { bucket: string; value: number }

export default function ChartSentiment({ data }: { data: Point[] }) {
  return (
    <div className="h-80 bg-white rounded-2xl shadow p-4">
      <h2 className="text-lg font-semibold mb-2">Sentiment moyen</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
          <YAxis domain={[-1, 1]} />
          <Tooltip />
          <Line type="monotone" dataKey="value" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
