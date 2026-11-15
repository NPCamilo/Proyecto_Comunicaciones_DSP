'use client';

import React, { useEffect, useState, useTransition } from 'react';
import dynamic from 'next/dynamic';
import { DemoData } from '@/types/dsp';
import { AsciiAcousticBackdrop } from '@/components/AsciiAcousticBackdrop';
import { AcousticWaveformComparator } from '@/components/AcousticWaveformComparator';
import EditorialShowcase from '@/components/EditorialShowcase';
import {
  Activity,
  Sliders,
  Sun,
  Moon,
  Terminal,
  Radio,
  FileCode,
  Sparkles,
  Layers,
  ChevronRight,
  GitBranch,
} from 'lucide-react';

// Dynamic lazy imports for heavy interactive components
const TelemetryDrawer = dynamic(() => import('@/components/TelemetryDrawer'), {
  ssr: false,
});

const LiveAudioTransceiver = dynamic(() => import('@/components/LiveAudioTransceiver'), {
  ssr: false,
});

export default function HomePage() {
  const [demoData, setDemoData] = useState<DemoData | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [asciiActive, setAsciiActive] = useState<boolean>(true);
  const [telemetryOpen, setTelemetryOpen] = useState<boolean>(false);
  const [, startTransition] = useTransition();

  // Load theme preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('dsp_theme') as 'dark' | 'light' | null;
    const initialTheme = savedTheme || 'dark';
    setTheme(initialTheme);
    document.documentElement.classList.toggle('dark', initialTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('dsp_theme', nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  };

  // Fetch demo data
  useEffect(() => {
    fetch('/demo/datos_demo.json')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: DemoData) => {
        startTransition(() => {
          setDemoData(data);
        });
      })
      .catch((err) => {
        console.warn('Fallback: Error al cargar datos_demo.json local:', err);
        // Fallback to API if available
        fetch('/api/audio/demo')
          .then((r) => r.json())
          .then((d) => setDemoData(d))
          .catch((apiErr) => {
            setDataError('No se pudieron cargar los datos de demostración de audio.');
          });
      });
  }, []);

  return (
    <div className="relative min-h-screen text-(--ink) bg-(--canvas) selection:bg-emerald-500/20 selection:text-emerald-400 overflow-x-hidden">
      {/* Dynamic ASCII Acoustic Background Matrix */}
      <AsciiAcousticBackdrop active={asciiActive} theme={theme} />

      {/* Atmospheric Ambient Radial Glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-40 dark:opacity-25">
        <div className="absolute -top-[20%] left-[10%] h-[600px] w-[600px] rounded-full bg-sky-500/10 blur-[130px]" />
        <div className="absolute top-[40%] -right-[15%] h-[700px] w-[700px] rounded-full bg-emerald-500/10 blur-[150px]" />
        <div className="absolute bottom-[10%] left-[20%] h-[500px] w-[500px] rounded-full bg-purple-500/10 blur-[120px]" />
      </div>

      {/* Telemetry Drawer Modal */}
      <TelemetryDrawer
        demoData={demoData}
        isOpen={telemetryOpen}
        onClose={() => setTelemetryOpen(false)}
      />

      {/* Sticky Top Header Rail */}
      <header className="sticky top-0 z-40 w-full border-b border-(--hairline) bg-(--canvas)/80 backdrop-blur-md transition-colors">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo & Project Identity */}
          <div className="flex items-center gap-3">
            <a href="#hero" className="flex items-center gap-2.5 group">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 group-hover:scale-105 transition-transform">
                <Radio className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-display text-sm font-bold tracking-tight text-(--ink)">
                  AUDIO DSP // UTP
                </span>
                <span className="font-mono text-[10px] text-(--ink-muted) uppercase tracking-wider">
                  Comunicaciones I · Semestre 6
                </span>
              </div>
            </a>
          </div>

          {/* Desktop Anchor Stations */}
          <nav className="hidden md:flex items-center gap-1 font-mono text-xs">
            <a
              href="#hero"
              className="px-2.5 py-1.5 rounded-lg text-(--ink-muted) hover:text-(--ink) hover:bg-(--surface) transition-colors"
            >
              00 // Hero
            </a>
            <a
              href="#exhibit-01"
              className="px-2.5 py-1.5 rounded-lg text-(--ink-muted) hover:text-(--ink) hover:bg-(--surface) transition-colors"
            >
              01 // FFT
            </a>
            <a
              href="#exhibit-02"
              className="px-2.5 py-1.5 rounded-lg text-(--ink-muted) hover:text-(--ink) hover:bg-(--surface) transition-colors"
            >
              02 // PCM
            </a>
            <a
              href="#exhibit-03"
              className="px-2.5 py-1.5 rounded-lg text-(--ink-muted) hover:text-(--ink) hover:bg-(--surface) transition-colors"
            >
              03 // RF
            </a>
            <a
              href="#exhibit-04"
              className="px-2.5 py-1.5 rounded-lg text-(--ink-muted) hover:text-(--ink) hover:bg-(--surface) transition-colors"
            >
              04 // DAC
            </a>
            <a
              href="#workbench"
              className="px-2.5 py-1.5 rounded-lg text-emerald-400 font-medium bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 transition-colors"
            >
              05 // Laboratorio
            </a>
          </nav>

          {/* Utility Actions */}
          <div className="flex items-center gap-2">
            {/* ASCII Toggle */}
            <button
              onClick={() => setAsciiActive(!asciiActive)}
              className={`p-2 rounded-xl border text-xs font-mono transition-all ${
                asciiActive
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                  : 'bg-(--surface) border-(--hairline) text-(--ink-muted) hover:text-(--ink)'
              }`}
              title="Alternar fondo acústico de caracteres ASCII"
              aria-label="Alternar fondo ASCII"
            >
              <Terminal className="w-4 h-4" />
            </button>

            {/* Telemetry Trigger */}
            <button
              onClick={() => setTelemetryOpen(true)}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-(--hairline) bg-(--surface) hover:bg-(--surface-elevated) text-xs font-mono text-(--ink) transition-colors"
              title="Abrir cónsola de telemetría"
            >
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              <span>Telemetría</span>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl border border-(--hairline) bg-(--surface) hover:bg-(--surface-elevated) text-(--ink-muted) hover:text-(--ink) transition-colors"
              aria-label="Cambiar tema claro/oscuro"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-28">
        {/* HERO SECTION */}
        <section id="hero" className="scroll-mt-24 space-y-12">
          {/* Hero Headlines */}
          <div className="space-y-4 max-w-4xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>COMUNICACIONES & PROCESAMIENTO DIGITAL DE SEÑALES</span>
            </div>

            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-(--ink) leading-[1.1]">
              Cadena Integral de Audio DSP & Radiotransmisión
            </h1>

            <p className="text-base sm:text-lg text-(--ink-muted) leading-relaxed max-w-3xl">
              Plataforma interactiva para la adquisición temporal, análisis espectral de Fourier, digitalización PCM bajo el criterio Nyquist-Shannon, modulación en radiofrecuencia (AM, FM, FSK) y síntesis analógica por interpolación Sinc de Whittaker.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-mono text-(--ink-muted)">
              <span className="px-2.5 py-1 rounded-lg bg-(--surface) border border-(--hairline)">
                UTP · Ingeniería de Sistemas y Computación
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-(--surface) border border-(--hairline)">
                SNR Sinc: +26.97 dB
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-(--surface) border border-(--hairline)">
                BER Digital: 0.000000
              </span>
            </div>
          </div>

          {/* 120fps Waveform Split Comparator (Hero Exhibit) */}
          {demoData && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  Comparador A/B de Forma de Onda en Tiempo Real (120 FPS)
                </span>
                <span className="text-[11px] font-mono text-(--ink-muted)">
                  Arrastra el cursor para comparar Voz Original vs Reconstrucción Sinc
                </span>
              </div>

              <AcousticWaveformComparator
                originalAudioUrl={demoData.assets.wav_original}
                reconstructedAudioUrl={demoData.assets.wav_reconstructed_sinc}
                comparisonPlotUrl={demoData.assets.fig_fidelity_comparison}
                snrDb={demoData.fase4_5.dac_sinc.snr_db}
                pearsonCorr={demoData.fase4_5.dac_sinc.pearson_corr}
                sqnrDb={demoData.fase1.sampling_pcm.sqnr_empirical_db}
                sampleRate={demoData.fase1.audio.sample_rate_hz}
                durationSec={demoData.fase1.audio.duration_s}
              />
            </div>
          )}

          {dataError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              {dataError}
            </div>
          )}
        </section>

        {/* EDITORIAL SHOWCASE (Exhibits 01 to 04) */}
        {demoData && <EditorialShowcase demoData={demoData} />}

        {/* LIVE AUDIO TRANSCEIVER WORKBENCH (Exhibit 05) */}
        <LiveAudioTransceiver />
      </main>

      {/* Floating Action Dock (Mobile & Quick Actions) */}
      <aside aria-label="Navegación rápida de estaciones" className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-1.5 p-1.5 rounded-2xl bg-zinc-950/80 dark:bg-zinc-900/80 border border-zinc-800 shadow-2xl backdrop-blur-lg">
        <a
          href="#hero"
          className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
          title="Ir al inicio / Hero"
        >
          <Radio className="w-4 h-4" />
        </a>
        <a
          href="#exhibit-01"
          className="px-2 py-1 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
          title="01. Adquisición & FFT"
        >
          01
        </a>
        <a
          href="#exhibit-02"
          className="px-2 py-1 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
          title="02. Nyquist & PCM"
        >
          02
        </a>
        <a
          href="#exhibit-03"
          className="px-2 py-1 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
          title="03. Consola 8 Pistas RF"
        >
          03
        </a>
        <a
          href="#exhibit-04"
          className="px-2 py-1 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
          title="04. DAC Sinc"
        >
          04
        </a>
        <a
          href="#workbench"
          className="px-2 py-1 rounded-lg text-xs font-mono text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/20 transition-colors font-medium"
          title="05. Laboratorio en Vivo"
        >
          05
        </a>
        <div className="h-4 w-px bg-zinc-800 mx-1" />
        <button
          onClick={() => setTelemetryOpen(true)}
          className="p-2 rounded-xl text-blue-400 hover:bg-zinc-800/80 transition-colors"
          title="Abrir Telemetría"
        >
          <Activity className="w-4 h-4" />
        </button>
      </aside>

      {/* Colophon & Footer */}
      <footer className="relative z-10 border-t border-(--hairline) bg-(--surface) py-12 px-4 sm:px-6 lg:px-8 mt-24">
        <div className="mx-auto max-w-7xl flex flex-col md:flex-row items-center justify-between gap-6 font-mono text-xs text-(--ink-muted)">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <span className="font-semibold text-(--ink)">
              UTP · COMUNICACIONES I · 2026
            </span>
            <span className="hidden sm:inline">·</span>
            <span>Ingeniería de Sistemas y Computación</span>
          </div>

          <div className="flex items-center gap-6">
            <a
              href="https://github.com/NPCamilo/Proyecto_Comunicaciones_DSP"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-(--ink) transition-colors"
            >
              <GitBranch className="w-4 h-4" />
              <span>Repositorio GitHub</span>
            </a>
            <span>v1.0.0-fase6</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
