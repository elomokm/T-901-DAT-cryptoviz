import './globals.css';
import { Inter } from 'next/font/google';
import type { Metadata } from 'next';
import Providers from '@/components/Providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CryptoViz - Real-time Crypto Dashboard',
  description: 'Real-time cryptocurrency analytics platform with market data, news, and insights',
  keywords: ['crypto', 'bitcoin', 'ethereum', 'cryptocurrency', 'market', 'analytics'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 antialiased`}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
