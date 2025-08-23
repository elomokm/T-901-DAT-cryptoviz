import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/live'

type Snapshot = {
  t: string
  volume_1m: { bucket: string; source: string; value: number }[]
  sentiment_1m: { bucket: string; value: number }[]
}

export function useLiveSnapshot() {
  const [data, setData] = useState<Snapshot | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data) as Snapshot
        setData(parsed)
      } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {}
    return () => {
      ws.close()
    }
  }, [])

  return data
}
