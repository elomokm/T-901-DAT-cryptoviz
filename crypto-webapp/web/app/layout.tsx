import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from '@/components/Providers';
import Header from '@/components/layout/Header';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CryptoViz - Cryptocurrency Dashboard',
  description: 'Real-time cryptocurrency market data, analytics, and insights',
  keywords: ['cryptocurrency', 'bitcoin', 'ethereum', 'crypto', 'market', 'dashboard'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <Providers>
          <div className="flex flex-col min-h-screen">
            <Header />
            <main className="flex-1 container mx-auto px-4 py-6">
              {children}
            </main>
            <footer className="border-t border-gray-800/60 py-4 mt-8">
              <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
                <p>CryptoViz Dashboard - Real-time cryptocurrency data</p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
