'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const DEFAULT_CRYPTOS = ['bitcoin', 'cardano', 'ethereum', 'polkadot', 'solana']

const COLORS: Record<string, string> = {
  bitcoin: '#F7931A',
  ethereum: '#627EEA',
  cardano: '#0033AD',
  polkadot: '#E6007A',
  solana: '#14F195',
}

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [marketCap, setMarketCap] = useState<any>(null)
  const [prices, setPrices] = useState<any>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const cryptos = DEFAULT_CRYPTOS.join(',')
        const [mcRes, prRes] = await Promise.all([
          fetch(`${API_BASE}/overview/market-cap?cryptos=${cryptos}`),
          fetch(`${API_BASE}/overview/prices?cryptos=${cryptos}&range=24h&interval=30m`)
        ])
        if (!mcRes.ok) throw new Error('Failed to load market cap')
        if (!prRes.ok) throw new Error('Failed to load prices')
        const mcJson = await mcRes.json()
        const prJson = await prRes.json()
        setMarketCap(mcJson)
        setPrices(prJson)
      } catch (e: any) {
        setError(e.message || 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Transform price series for recharts
  const chartData = prices ? (() => {
    const allTimes = new Set<string>()
    DEFAULT_CRYPTOS.forEach(c => {
      (prices.series?.[c] || []).forEach((pt: any) => allTimes.add(pt.time))
    })
    const sorted = Array.from(allTimes).sort()
    return sorted.map(time => {
      const point: any = { time: new Date(time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) }
      DEFAULT_CRYPTOS.forEach(c => {
        const found = (prices.series?.[c] || []).find((pt: any) => pt.time === time)
        point[c] = found ? found.value : null
      })
      return point
    })
  })() : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              CryptoViz
            </h1>
            <nav className="flex gap-6">
              <a href="/" className="text-blue-400 hover:text-blue-300 transition">Overview</a>
              <a href="/dashboards/core" className="text-slate-400 hover:text-slate-300 transition">Core Dashboard</a>
              <a href="/dashboards/comparisons" className="text-slate-400 hover:text-slate-300 transition">Comparisons</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-400 text-lg">Loading market data...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-400">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6">
                <div className="text-slate-400 text-sm mb-2">Total Market Cap</div>
                <div className="text-3xl font-bold text-white">
                  ${(marketCap?.total_market_cap || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
                <div className="text-xs text-slate-500 mt-1">Selected assets</div>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6">
                <div className="text-slate-400 text-sm mb-2">Bitcoin Price</div>
                <div className="text-3xl font-bold text-orange-400">
                  ${(() => {
                    const pts = prices?.series?.bitcoin || []
                    const last = pts[pts.length - 1]
                    return last ? Number(last.value).toLocaleString() : 'n/a'
                  })()}
                </div>
                <div className="text-xs text-slate-500 mt-1">Latest</div>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6">
                <div className="text-slate-400 text-sm mb-2">Ethereum Price</div>
                <div className="text-3xl font-bold text-blue-400">
                  ${(() => {
                    const pts = prices?.series?.ethereum || []
                    const last = pts[pts.length - 1]
                    return last ? Number(last.value).toLocaleString() : 'n/a'
                  })()}
                </div>
                <div className="text-xs text-slate-500 mt-1">Latest</div>
              </div>
            </div>

            {/* Price Chart */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6 mb-8">
              <h2 className="text-xl font-semibold text-white mb-4">Price Trends (24h)</h2>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94a3b8" style={{ fontSize: 12 }} />
                  <YAxis stroke="#94a3b8" style={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#cbd5e1' }}
                  />
                  <Legend wrapperStyle={{ color: '#cbd5e1' }} />
                  {DEFAULT_CRYPTOS.map(c => (
                    <Line
                      key={c}
                      type="monotone"
                      dataKey={c}
                      stroke={COLORS[c] || '#94a3b8'}
                      strokeWidth={2}
                      dot={false}
                      name={c.charAt(0).toUpperCase() + c.slice(1)}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Market Cap Breakdown */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Market Cap by Asset</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {DEFAULT_CRYPTOS.map(c => {
                  const val = marketCap?.per_crypto?.[c] || 0
                  return (
                    <div key={c} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[c] || '#94a3b8' }}
                        />
                        <div className="text-sm font-medium text-slate-300 capitalize">{c}</div>
                      </div>
                      <div className="text-lg font-bold text-white">
                        ${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {((val / (marketCap?.total_market_cap || 1)) * 100).toFixed(1)}%
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

