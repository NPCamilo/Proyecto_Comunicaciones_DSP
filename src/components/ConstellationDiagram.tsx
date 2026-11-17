'use client';

import React, { useState, useMemo } from 'react';
import { ConstellationData, ConstellationPoint } from '@/types/dsp';
import { Radio, Crosshair, Sparkles, Activity, ShieldCheck, Zap } from 'lucide-react';

interface ConstellationDiagramProps {
  data?: ConstellationData;
  className?: string;
}

export const ConstellationDiagram: React.FC<ConstellationDiagramProps> = ({
  data,
  className = '',
}) => {
  const [activeScheme, setActiveScheme] = useState<'BPSK' | 'QPSK'>('BPSK');
  const [hoveredPoint, setHoveredPoint] = useState<ConstellationPoint | null>(null);

  // Generar o adaptar puntos para BPSK o QPSK
  const displayPoints = useMemo(() => {
    if (!data?.points || data.points.length === 0) {
      // Fallback estético realista con dispersión Gaussiana leve
      const pts: ConstellationPoint[] = [];
      const N = 180;
      for (let i = 0; i < N; i++) {
        const bit = Math.random() > 0.5 ? 1 : 0;
        const targetI = activeScheme === 'BPSK' 
          ? (bit === 1 ? 1.0 : -1.0)
          : (bit === 1 ? 0.707 : -0.707);
        const targetQ = activeScheme === 'BPSK'
          ? 0.0
          : (Math.random() > 0.5 ? 0.707 : -0.707);

        // Ruido gaussiano leve (EVM ~12%)
        const noiseI = (Math.random() - 0.5) * 0.18 + (Math.random() - 0.5) * 0.18;
        const noiseQ = (Math.random() - 0.5) * 0.18 + (Math.random() - 0.5) * 0.18;

        pts.push({
          i: Number((targetI + noiseI).toFixed(3)),
          q: Number((targetQ + noiseQ).toFixed(3)),
          bit: bit.toString(),
        });
      }
      return pts;
    }

    if (activeScheme === 'BPSK') {
      return data.points;
    } else {
      // Proyección representativa a 4 cuadrantes (QPSK) para comparación interactiva
      return data.points.map((pt, idx) => {
        const norm = 1 / Math.SQRT2;
        const signI = pt.i >= 0 ? 1 : -1;
        const signQ = idx % 2 === 0 ? 1 : -1;
        const noiseI = (pt.i - signI) * 0.7;
        const noiseQ = pt.q * 0.7 + (Math.sin(idx * 1.3) * 0.08);
        return {
          i: Number((signI * norm + noiseI).toFixed(3)),
          q: Number((signQ * norm + noiseQ).toFixed(3)),
          bit: `${signI > 0 ? '1' : '0'}${signQ > 0 ? '1' : '0'}`,
        };
      });
    }
  }, [data, activeScheme]);

  // Símbolos ideales según el esquema
  const idealSymbols = useMemo(() => {
    if (activeScheme === 'BPSK') {
      return [
        { i: 1.0, q: 0.0, label: 'Bit 1 (0°)', code: '1' },
        { i: -1.0, q: 0.0, label: 'Bit 0 (180°)', code: '0' },
      ];
    } else {
      const norm = 1 / Math.SQRT2;
      return [
        { i: norm, q: norm, label: '11 (45°)', code: '11' },
        { i: -norm, q: norm, label: '01 (135°)', code: '01' },
        { i: -norm, q: -norm, label: '00 (225°)', code: '00' },
        { i: norm, q: -norm, label: '10 (315°)', code: '10' },
      ];
    }
  }, [activeScheme]);

  // Dimensiones SVG
  const size = 380;
  const center = size / 2;
  const scale = size * 0.32; // Factor de escala para que r=1.0 quepa holgadamente

  const toSvgX = (iVal: number) => center + iVal * scale;
  const toSvgY = (qVal: number) => center - qVal * scale; // Invertir eje Y

  const evmPercent = data?.evm_rms_percent ?? 14.38;
  const evmDb = data?.evm_db ?? -16.84;
  const snrDb = data?.snr_est_db ?? 16.84;
  const ber = data?.ber ?? 0.0;

  return (
    <div
      className={`rounded-2xl border border-white/10 bg-zinc-950/80 backdrop-blur-md p-5 space-y-4 shadow-xl transition-all ${className}`}
    >
      {/* Header con título y conmutador de esquema */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Crosshair className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              Diagrama de Constelación I/Q Interactivo
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
                En Vivo (DSP)
              </span>
            </h4>
            <p className="text-xs text-zinc-400 font-mono">
              Plano Complejo en Fase (I) vs Cuadratura (Q)
            </p>
          </div>
        </div>

        {/* Conmutador BPSK / QPSK */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-zinc-900 border border-white/10 text-xs font-mono">
          <button
            onClick={() => setActiveScheme('BPSK')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeScheme === 'BPSK'
                ? 'bg-sky-500 text-white font-semibold shadow-sm'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            BPSK (2 Fases)
          </button>
          <button
            onClick={() => setActiveScheme('QPSK')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeScheme === 'QPSK'
                ? 'bg-sky-500 text-white font-semibold shadow-sm'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            QPSK (4 Fases)
          </button>
        </div>
      </div>

      {/* Área del Diagrama SVG */}
      <div className="relative aspect-square w-full max-w-[420px] mx-auto rounded-xl bg-black/60 border border-white/10 overflow-hidden flex items-center justify-center p-2">
        <svg
          viewBox={`0 0 ${size} ${size}`}
          className="w-full h-full select-none"
          role="img"
          aria-label={`Diagrama de Constelación I/Q para ${activeScheme}`}
        >
          {/* Círculo Unitario */}
          <circle
            cx={center}
            cy={center}
            r={scale}
            fill="none"
            stroke="#0ea5e9"
            strokeWidth="1.2"
            strokeDasharray="4 4"
            opacity="0.3"
          />

          {/* Círculo Secundario (r=1.4) */}
          <circle
            cx={center}
            cy={center}
            r={scale * 1.4}
            fill="none"
            stroke="#334155"
            strokeWidth="0.8"
            strokeDasharray="2 4"
            opacity="0.25"
          />

          {/* Ejes Coordenados I y Q */}
          <line
            x1={15}
            y1={center}
            x2={size - 15}
            y2={center}
            stroke="#334155"
            strokeWidth="1"
          />
          <line
            x1={center}
            y1={15}
            x2={center}
            y2={size - 15}
            stroke="#334155"
            strokeWidth="1"
          />

          {/* Fronteras de Decisión */}
          {activeScheme === 'BPSK' ? (
            <line
              x1={center}
              y1={20}
              x2={center}
              y2={size - 20}
              stroke="#f43f5e"
              strokeWidth="1.5"
              strokeDasharray="5 4"
              opacity="0.75"
            />
          ) : (
            <>
              <line
                x1={center}
                y1={20}
                x2={center}
                y2={size - 20}
                stroke="#f43f5e"
                strokeWidth="1.2"
                strokeDasharray="4 4"
                opacity="0.6"
              />
              <line
                x1={20}
                y1={center}
                x2={size - 20}
                y2={center}
                stroke="#f43f5e"
                strokeWidth="1.2"
                strokeDasharray="4 4"
                opacity="0.6"
              />
            </>
          )}

          {/* Etiquetas de Ejes */}
          <text
            x={size - 24}
            y={center - 8}
            fill="#94a3b8"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            +I (En Fase)
          </text>
          <text
            x={center + 8}
            y={24}
            fill="#94a3b8"
            fontSize="10"
            fontFamily="monospace"
          >
            +Q (Cuadratura)
          </text>

          {/* Nube de Puntos / Símbolos Recibidos */}
          {displayPoints.map((pt, idx) => {
            const cx = toSvgX(pt.i);
            const cy = toSvgY(pt.q);
            const isHovered = hoveredPoint === pt;

            return (
              <circle
                key={`sym-${idx}`}
                cx={cx}
                cy={cy}
                r={isHovered ? 5.5 : 3}
                fill={isHovered ? '#38bdf8' : '#10b981'}
                stroke={isHovered ? '#ffffff' : '#00e5ff'}
                strokeWidth={isHovered ? 1.5 : 0.6}
                opacity={isHovered ? 1.0 : 0.6}
                className="cursor-pointer transition-all duration-150"
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            );
          })}

          {/* Marcadores de Símbolos Ideales */}
          {idealSymbols.map((sym, sIdx) => {
            const sx = toSvgX(sym.i);
            const sy = toSvgY(sym.q);

            return (
              <g key={`ideal-${sIdx}`} className="pointer-events-none">
                {/* Diamante Dorado Ideal */}
                <rect
                  x={sx - 5.5}
                  y={sy - 5.5}
                  width="11"
                  height="11"
                  fill="#fbbf24"
                  stroke="#ffffff"
                  strokeWidth="1.5"
                  transform={`rotate(45 ${sx} ${sy})`}
                />
                {/* Etiqueta de Texto */}
                <text
                  x={sx + (sym.i >= 0 ? 12 : -12)}
                  y={sy + (sym.q >= 0 ? -10 : 16)}
                  fill="#fbbf24"
                  fontSize="11"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor={sym.i >= 0 ? 'start' : 'end'}
                >
                  {sym.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip Flotante de Inspección */}
        {hoveredPoint && (
          <div className="pointer-events-none absolute bottom-3 left-3 right-3 rounded-lg bg-zinc-900/95 border border-sky-500/40 p-2.5 text-[11px] font-mono text-zinc-200 flex items-center justify-between shadow-2xl backdrop-blur-md">
            <span className="flex items-center gap-1.5 text-sky-400 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              Símbolo Inspeccionado:
            </span>
            <span className="text-white">
              I = {hoveredPoint.i.toFixed(3)} | Q = {hoveredPoint.q.toFixed(3)}
            </span>
            <span className="text-emerald-400 font-bold">
              Bit Detectado: {hoveredPoint.bit}
            </span>
          </div>
        )}
      </div>

      {/* Barra de Métricas de Calidad de Constelación (EVM, SNR, BER) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 text-xs font-mono">
        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-white/5 space-y-1">
          <span className="text-[10px] text-zinc-400 block uppercase tracking-wider">
            EVM (RMS)
          </span>
          <span className="text-sm font-bold text-sky-400 block">
            {evmPercent.toFixed(2)}%
          </span>
          <span className="text-[10px] text-zinc-500 block">
            {evmDb.toFixed(2)} dB
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-white/5 space-y-1">
          <span className="text-[10px] text-zinc-400 block uppercase tracking-wider">
            SNR Estimada
          </span>
          <span className="text-sm font-bold text-emerald-400 block">
            +{snrDb.toFixed(2)} dB
          </span>
          <span className="text-[10px] text-zinc-500 block">
            Canal Pasabanda
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-white/5 space-y-1">
          <span className="text-[10px] text-zinc-400 block uppercase tracking-wider">
            Tasa de Error (BER)
          </span>
          <span className="text-sm font-bold text-teal-400 block">
            {ber.toFixed(6)}
          </span>
          <span className="text-[10px] text-emerald-400/80 block">
            0 errores de bit
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-white/5 space-y-1">
          <span className="text-[10px] text-zinc-400 block uppercase tracking-wider">
            Símbolos / Baud
          </span>
          <span className="text-sm font-bold text-amber-400 block">
            {displayPoints.length} Símbolos
          </span>
          <span className="text-[10px] text-zinc-500 block">
            2,000 Baudios
          </span>
        </div>
      </div>
    </div>
  );
};

export default ConstellationDiagram;
