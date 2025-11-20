"use client";

import React from 'react';

interface Point { time: string | Date; value: number }

interface SparklineProps {
  points: Point[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
}

export default function Sparkline({ points, width = 280, height = 80, stroke = '#60a5fa', fill = 'rgba(96,165,250,0.15)' }: SparklineProps) {
  if (!points || points.length === 0) {
    return <div className="text-xs text-gray-500">No data</div>;
  }

  const xs = points.map((_, i) => i);
  const ys = points.map(p => p.value);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanY = maxY - minY || 1;

  const pad = 4;
  const w = width - pad * 2;
  const h = height - pad * 2;

  const coords = points.map((p, i) => {
    const x = pad + (i / (points.length - 1)) * w;
    const yNorm = (p.value - minY) / spanY; // 0..1
    const y = pad + (1 - yNorm) * h;
    return [x, y] as [number, number];
  });

  const path = coords.map(([x, y], idx) => `${idx === 0 ? 'M' : 'L'}${x},${y}`).join(' ');
  const area = `${path} L${pad + w},${pad + h} L${pad},${pad + h} Z`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path d={area} fill={fill} stroke="none" />
      <path d={path} fill="none" stroke={stroke} strokeWidth={2} />
    </svg>
  );
}
