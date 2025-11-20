"use client";

import React from 'react';

export default function RightPanel() {
  return (
    <aside className="hidden lg:block border-l border-gray-800/60 bg-gray-950/60 backdrop-blur-xl">
      <div className="p-6 space-y-6">
        {/* Total balance mock card */}
        <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-5">
          <div className="text-gray-400 text-xs uppercase">Total balance</div>
          <div className="text-white text-3xl font-bold mt-1">$78,820.00</div>
          <div className="text-green-400 text-xs mt-1">▲ +$931.12</div>
        </div>

        {/* Exchange mock */}
        <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-5 space-y-3">
          <div className="text-gray-400 text-xs uppercase">Exchange</div>
          <button className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold rounded-lg py-2">Exchange</button>
        </div>

        {/* AI Tips mock */}
        <div className="bg-gray-900/60 border border-gray-800/60 rounded-xl p-5 space-y-2">
          <div className="text-white font-semibold">AI Tips</div>
          <ul className="text-sm text-gray-400 list-disc list-inside space-y-1">
            <li>Follow news and market analysis.</li>
            <li>Create a trading plan with goals.</li>
          </ul>
        </div>

        {/* Premium mock */}
        <div className="rounded-xl p-5 border border-blue-500/40 bg-gradient-to-br from-blue-500/10 to-purple-500/10">
          <div className="text-white font-semibold mb-2">Premium Plan</div>
          <div className="text-gray-300 text-sm mb-3">Upgrade for unlimited access.</div>
          <button className="w-full bg-white/90 hover:bg-white text-gray-900 font-semibold rounded-lg py-2">Upgrade Now</button>
        </div>
      </div>
    </aside>
  );
}
