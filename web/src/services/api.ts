const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export type TopItem = { symbol:string; price:number; change24h:number|null }

async function get<T>(path: string, params?: Record<string, string>) {
  const url = new URL(path, API_URL)
  if (params) Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, v))
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

export const api = {
  marketTop: (limit='20') => get<TopItem[]>('/market/top', { limit }),
  candles: (symbol:string, tf='1m') =>
    get<{ts:string;open:number;high:number;low:number;close:number;volume:number}[]>('/timeseries/candles', { symbol, tf }),
  news: (limit='50') => get<any[]>('/news', { limit }),
}
