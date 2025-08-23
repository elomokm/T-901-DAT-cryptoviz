import { useEffect, useMemo, useState } from 'react'
import { TrendingUp, TrendingDown, Search, Star, BarChart3, DollarSign, Activity } from 'lucide-react'
import { api, TopItem } from '../services/api'

const formatNumber = (num:number) => {
  if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`
  if (num >= 1e9)  return `$${(num / 1e9).toFixed(2)}B`
  if (num >= 1e6)  return `$${(num / 1e6).toFixed(2)}M`
  if (num >= 1e3)  return `$${(num / 1e3).toFixed(2)}K`
  return `$${num.toFixed(2)}`
}
const formatPrice = (price:number) =>
  price >= 1
    ? `$${price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}`
    : `$${price.toFixed(6)}`

function MarketStats() {
  const totalMarketCap = 0 // placeholder
  const totalVolume    = 0 // placeholder
  const btcDominance   = 0 // placeholder
  const marketCapChange = 0
  const volumeChange    = 0
  const btcDominanceChange = 0

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Prix des Cryptos d'Aujourd'hui par Capitalisation Boursière</h2>
      <p className="text-gray-600 mb-6">Données récupérées sur ta base (Binance 1m via scraper).</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Capitalisation boursière</p>
            <p className="text-2xl font-bold text-gray-900">{formatNumber(totalMarketCap)}</p>
            <div className={`flex items-center text-sm ${marketCapChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {marketCapChange >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
              {Math.abs(marketCapChange)}%
            </div>
          </div>
          <DollarSign className="w-8 h-8 text-indigo-500" />
        </div>
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Volume 24h</p>
            <p className="text-2xl font-bold text-gray-900">{formatNumber(totalVolume)}</p>
            <div className={`flex items-center text-sm ${volumeChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {volumeChange >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
              {Math.abs(volumeChange)}%
            </div>
          </div>
          <BarChart3 className="w-8 h-8 text-emerald-500" />
        </div>
        <div className="bg-gradient-to-r from-orange-50 to-yellow-50 p-4 rounded-lg flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Domination du BTC</p>
            <p className="text-2xl font-bold text-gray-900">{btcDominance}%</p>
            <div className={`flex items-center text-sm ${btcDominanceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {btcDominanceChange >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
              {Math.abs(btcDominanceChange)}%
            </div>
          </div>
          <Activity className="w-8 h-8 text-orange-500" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [searchTerm, setSearchTerm] = useState('')
  const [rows, setRows] = useState<TopItem[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string>('')

  useEffect(() => {
    let mounted = true
    api.marketTop('20')
      .then((data) => { if (mounted) { setRows(data); setLoading(false) } })
      .catch((e) => { if (mounted) { setErr(String(e)); setLoading(false) } })
    return () => { mounted = false }
  }, [])

  const filtered = useMemo(() => {
    if (!searchTerm) return rows
    const q = searchTerm.toLowerCase()
    return rows.filter(r => r.symbol.toLowerCase().includes(q))
  }, [rows, searchTerm])

  return (
    <>
      <MarketStats />
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Top Cryptomonnaies</h2>
          <p className="text-gray-600">Données issues de ta DB (candles 1m).</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Rechercher une crypto..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
          />
        </div>
      </div>

      {err && <div className="text-red-600 mb-4">{err}</div>}
      {loading ? (
        <div className="text-gray-600">Chargement…</div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase">Symbole</th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">Prix</th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">24h %</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filtered.map((c) => (
                  <tr key={c.symbol} className="hover:bg-gray-50 transition-colors duration-150">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{c.symbol}</td>
                    <td className="px-6 py-4 text-right text-sm font-medium text-gray-900">{formatPrice(c.price)}</td>
                    <td className="px-6 py-4 text-right text-sm">
                      <div className={`flex items-center justify-end ${!c.change24h || c.change24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {(!c.change24h || c.change24h >= 0) ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                        {c.change24h === null ? '—' : Math.abs(c.change24h).toFixed(2) + '%'}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
