'use client'

export default function CoreDashboard() {
  // Grafana Core dashboard URL - removed kiosk mode for better iframe compatibility
  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3000'
  const dashboardUrl = `${grafanaUrl}/d/crypto-core/crypto-core?orgId=1&refresh=30s&theme=dark`

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
              <a href="/" className="text-slate-400 hover:text-slate-300 transition">Overview</a>
              <a href="/dashboards/core" className="text-blue-400 hover:text-blue-300 transition">Core Dashboard</a>
              <a href="/dashboards/comparisons" className="text-slate-400 hover:text-slate-300 transition">Comparisons</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Crypto Core - Real-time Analytics</h2>
            <a
              href={`${grafanaUrl}/d/crypto-core/crypto-core?orgId=1`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 hover:text-blue-300 transition"
            >
              Open in Grafana ↗
            </a>
          </div>
          <div className="relative w-full" style={{ height: 'calc(100vh - 200px)' }}>
            <iframe
              src={dashboardUrl}
              className="w-full h-full rounded-lg border-0"
              title="Crypto Core Dashboard"
              allow="fullscreen"
            />
          </div>
        </div>
      </main>
    </div>
  )
}
