import { NavLink, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import News from './pages/News'
import Portfolio from './pages/Portfolio'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Topbar simple */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            CryptoViz
          </h1>
          <nav className="flex gap-6 text-gray-700">
            <NavLink to="/" end className={({isActive}) => isActive ? 'font-semibold text-blue-600' : 'hover:text-blue-600'}>
              Dashboard
            </NavLink>
            <NavLink to="/news" className={({isActive}) => isActive ? 'font-semibold text-blue-600' : 'hover:text-blue-600'}>
              Actualités
            </NavLink>
            <NavLink to="/portfolio" className={({isActive}) => isActive ? 'font-semibold text-blue-600' : 'hover:text-blue-600'}>
              Portefeuille
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard/>} />
          <Route path="/news" element={<News/>} />
          <Route path="/portfolio" element={<Portfolio/>} />
        </Routes>
      </main>
    </div>
  )
}
