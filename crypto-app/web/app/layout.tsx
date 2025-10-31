import './globals.css'

export const metadata = {
  title: 'CryptoViz',
  description: 'Real-time crypto analytics platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
