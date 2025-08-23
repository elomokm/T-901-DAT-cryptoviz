import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'
type Point = { bucket: string; value: number }

export default function ChartMentions({ data, symbol }: { data: Point[]; symbol?: string }) {
  return (
    <div className="h-80 bg-white rounded-2xl shadow p-4">
      <h2 className="text-lg font-semibold mb-2">Mentions {symbol ? `(${symbol})` : ''}</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line type="monotone" dataKey="value" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
