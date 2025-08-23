type Item = { key: string; count: number }

export default function TopSymbols({ items }: { items: Item[] }) {
  return (
    <div className="bg-white rounded-2xl shadow p-4">
      <h2 className="text-lg font-semibold mb-2">Top symboles (1h)</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b">
            <th className="py-2">Symbole</th>
            <th className="py-2">Mentions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.key} className="border-b last:border-0">
              <td className="py-2 font-medium">{it.key}</td>
              <td className="py-2">{it.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
