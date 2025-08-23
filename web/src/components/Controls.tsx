type Props = {
  hours: number; onHoursChange: (h: number) => void;
  symbol: string; onSymbolChange: (s: string) => void;
  topSymbols: { key: string; count: number }[];
}

export default function Controls({ hours, onHoursChange, symbol, onSymbolChange, topSymbols }: Props) {
  const presets = [1, 6, 24, 72]
  return (
    <div className="bg-white rounded-2xl shadow p-4 flex flex-wrap gap-4 items-center">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Fenêtre</span>
        <select className="border rounded px-2 py-1"
          value={hours} onChange={e => onHoursChange(Number(e.target.value))}>
          {presets.map(h => <option key={h} value={h}>{h} h</option>)}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Symbole</span>
        <select className="border rounded px-2 py-1"
          value={symbol} onChange={e => onSymbolChange(e.target.value)}>
          <option value="">(aucun)</option>
          {topSymbols.map(t => <option key={t.key} value={t.key}>{t.key}</option>)}
        </select>
      </div>
    </div>
  )
}
