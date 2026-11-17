"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, Play, Sparkles, Volume2, Pause } from "lucide-react";

interface AcousticWaveformComparatorProps {
  originalAudioUrl: string;
  reconstructedAudioUrl: string;
  comparisonPlotUrl?: string;
  snrDb: number;
  pearsonCorr: number;
  sqnrDb: number;
  sampleRate: number;
  durationSec: number;
  onInspectImage?: (src: string, title: string, caption?: string) => void;
  realWaveforms?: {
    macro_orig: number[];
    macro_rec: number[];
    transient_orig: number[];
    transient_rec: number[];
  };
}

type ViewMode = "waveform" | "transient";

// Generador determinista de perfil macro de onda (envolvente silábica completa)
function generateMacroProfile(points: number, phaseShift: number = 0, roughness: number = 0.05): number[] {
  const profile: number[] = [];
  for (let i = 0; i < points; i++) {
    const t = i / points;
    // Envolvente de sílabas y formantes vocálicos F1/F2
    const syllableEnv = Math.sin(t * Math.PI * 4.5) ** 2;
    const formants =
      Math.sin(t * 75.0 + phaseShift) * 0.55 +
      Math.sin(t * 165.0 - phaseShift * 1.5) * 0.32 +
      Math.sin(t * 310.0) * 0.13;
    const quantizationJitter = Math.sin(i * 12.3) * roughness;
    const value = Math.max(-0.95, Math.min(0.95, (formants + quantizationJitter) * syllableEnv));
    profile.push(value);
  }
  return profile;
}

// Generador de perfil micro transitorio (zoom microscópico de 20 ms sobre pulso glótico y lóbulos sinc)
function generateTransientProfile(points: number, isReconstructed: boolean): number[] {
  const profile: number[] = [];
  for (let i = 0; i < points; i++) {
    const t = (i / points) * 4.0 - 2.0; // de -2.0 a +2.0
    // Función sinc central del pulso acústico Whittaker-Shannon
    const piT = Math.PI * t * 3.4;
    const sincCenter = Math.abs(piT) < 0.001 ? 1.0 : Math.sin(piT) / piT;
    const formantRinging = Math.cos(t * 16.0) * 0.38 * Math.exp(-t * t * 1.6);
    const glottalPulse = (sincCenter * 0.72 + formantRinging) * Math.exp(-Math.abs(t) * 0.85);

    if (isReconstructed) {
      // Reconstrucción Sinc DAC: lóbulos de Whittaker-Shannon y discretización
      const sincLobes = Math.sin(t * 22.0) * 0.08 * Math.exp(-Math.abs(t) * 1.1);
      const stepped = Math.round((glottalPulse + sincLobes) * 18.0) / 18.0;
      profile.push(Math.max(-0.95, Math.min(0.95, stepped * 0.88 + (glottalPulse + sincLobes) * 0.12)));
    } else {
      // Onda continua pura analógica
      profile.push(Math.max(-0.95, Math.min(0.95, glottalPulse)));
    }
  }
  return profile;
}

export function AcousticWaveformComparator({
  originalAudioUrl,
  reconstructedAudioUrl,
  snrDb,
  pearsonCorr,
  sqnrDb,
  sampleRate,
  durationSec,
  realWaveforms,
}: AcousticWaveformComparatorProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("waveform");
  const [sweeping, setSweeping] = useState(false);
  const [playingChannel, setPlayingChannel] = useState<"none" | "orig" | "rec">("none");
  const [playProgress, setPlayProgress] = useState(0);
  const [playTime, setPlayTime] = useState(0);

  const playingChannelRef = useRef<"none" | "orig" | "rec">("none");
  const frameRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const readoutRef = useRef<HTMLSpanElement | null>(null);

  const audioOrigRef = useRef<HTMLAudioElement | null>(null);
  const audioRecRef = useRef<HTMLAudioElement | null>(null);

  // URLs con cache-busting estricto para evitar reproducción de audios sintéticos residuales
  const safeOrigUrl = useMemo(() => {
    return originalAudioUrl.includes("?")
      ? `${originalAudioUrl}&cb=v2`
      : `${originalAudioUrl}?v=2.0-billie`;
  }, [originalAudioUrl]);

  const safeRecUrl = useMemo(() => {
    return reconstructedAudioUrl.includes("?")
      ? `${reconstructedAudioUrl}&cb=v2`
      : `${reconstructedAudioUrl}?v=2.0-billie`;
  }, [reconstructedAudioUrl]);

  const stateRef = useRef({
    split: 52,
    targetSplit: 52,
    dragging: false,
    tiltX: 2.2,
    tiltY: -3.0,
    targetTiltX: 2.2,
    targetTiltY: -3.0,
    sweepStart: 0,
    sweeping: false,
  });

  const rafRef = useRef<number | null>(null);

  // Perfiles de onda macro (Onda Dual) y micro (Transiente sinc)
  const wavePoints = 140;
  const originalWaveMacro = useMemo(() => generateMacroProfile(wavePoints, 0.0, 0.0), []);
  const reconstructedWaveMacro = useMemo(() => generateMacroProfile(wavePoints, 0.08, 0.04), []);
  const originalWaveTransient = useMemo(() => generateTransientProfile(wavePoints, false), []);
  const reconstructedWaveTransient = useMemo(() => generateTransientProfile(wavePoints, true), []);

  const activeOrigWave = useMemo(() => {
    if (viewMode === "transient") {
      return realWaveforms?.transient_orig?.length ? realWaveforms.transient_orig : originalWaveTransient;
    }
    return realWaveforms?.macro_orig?.length ? realWaveforms.macro_orig : originalWaveMacro;
  }, [viewMode, realWaveforms, originalWaveTransient, originalWaveMacro]);

  const activeRecWave = useMemo(() => {
    if (viewMode === "transient") {
      return realWaveforms?.transient_rec?.length ? realWaveforms.transient_rec : reconstructedWaveTransient;
    }
    return realWaveforms?.macro_rec?.length ? realWaveforms.macro_rec : reconstructedWaveMacro;
  }, [viewMode, realWaveforms, reconstructedWaveTransient, reconstructedWaveMacro]);

  const applyVars = useCallback(() => {
    const s = stateRef.current;
    const viewport = viewportRef.current;
    const frame = frameRef.current;
    const readout = readoutRef.current;

    if (viewport) {
      viewport.style.setProperty("--split", `${s.split.toFixed(2)}%`);
      viewport.setAttribute("aria-valuenow", String(Math.round(s.split)));
    }
    if (frame) {
      frame.style.setProperty("--rx", `${s.tiltX.toFixed(2)}deg`);
      frame.style.setProperty("--ry", `${s.tiltY.toFixed(2)}deg`);
    }
    if (readout) {
      if (playingChannelRef.current === "rec") {
        readout.textContent = `▶ Reproduciendo DAC Sinc (Billie Bossa Nova)`;
      } else if (playingChannelRef.current === "orig") {
        readout.textContent = `▶ Reproduciendo Audio Original (Billie Bossa Nova)`;
      } else {
        const leftPct = Math.round(s.split);
        readout.textContent = `${leftPct}% Original / ${100 - leftPct}% Reconstruida Sinc`;
      }
    }
  }, []);

  const startLoop = useCallback(() => {
    if (rafRef.current !== null) return;

    const tick = (now: number) => {
      const s = stateRef.current;
      const isAudioActive = playingChannelRef.current !== "none";

      if (isAudioActive && !s.dragging) {
        const activeAudio =
          playingChannelRef.current === "rec" ? audioRecRef.current : audioOrigRef.current;
        if (activeAudio && activeAudio.duration > 0 && !activeAudio.paused) {
          const cur = activeAudio.currentTime;
          const dur = activeAudio.duration || durationSec || 8.0;
          const p = Math.max(0, Math.min(1, cur / dur));
          // Barrido progresivo continuo en paralelo a lo largo de la onda
          const pct = 4 + p * 92;
          s.targetSplit = pct;
          s.split = pct;
          setPlayProgress(p);
          setPlayTime(cur);

          if (readoutRef.current) {
            const chLabel =
              playingChannelRef.current === "rec" ? "DAC Sinc (Whittaker)" : "Billie Bossa Nova Original";
            readoutRef.current.textContent = `▶ ${chLabel}: ${cur.toFixed(1)}s / ${dur.toFixed(1)}s [${Math.round(p * 100)}%]`;
          }
        }
      } else if (s.sweeping) {
        if (s.sweepStart === 0) s.sweepStart = now;
        const elapsed = (now - s.sweepStart) / 1000;
        const duration = 2.4;
        if (elapsed >= duration) {
          s.sweeping = false;
          s.targetSplit = 52;
          setSweeping(false);
        } else {
          // Barrido sinusoidal elegante entre 16% <-> 86%
          const p = elapsed / duration;
          s.targetSplit = 52 - Math.sin(p * Math.PI * 2) * 35;
        }
      }

      const dSplit = s.targetSplit - s.split;
      const dTx = s.targetTiltX - s.tiltX;
      const dTy = s.targetTiltY - s.tiltY;

      if (!isAudioActive) {
        s.split += dSplit * 0.24;
      }
      s.tiltX += dTx * 0.14;
      s.tiltY += dTy * 0.14;

      applyVars();

      const settled =
        !isAudioActive &&
        !s.sweeping &&
        !s.dragging &&
        Math.abs(dSplit) < 0.04 &&
        Math.abs(dTx) < 0.03 &&
        Math.abs(dTy) < 0.03;

      if (settled) {
        s.split = s.targetSplit;
        s.tiltX = s.targetTiltX;
        s.tiltY = s.targetTiltY;
        applyVars();
        rafRef.current = null;
        return;
      }

      rafRef.current = window.requestAnimationFrame(tick);
    };

    rafRef.current = window.requestAnimationFrame(tick);
  }, [applyVars, durationSec]);

  useEffect(() => {
    applyVars();
    return () => {
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
      }
    };
  }, [applyVars]);

  const updateSplitFromClientX = (clientX: number) => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const rect = viewport.getBoundingClientRect();
    if (rect.width <= 0) return;
    const pct = ((clientX - rect.left) / rect.width) * 100;
    const clamped = Math.max(4, Math.min(96, pct));
    stateRef.current.targetSplit = clamped;
    stateRef.current.split = clamped;

    // Si hay audio reproduciéndose, permitir scrubbing táctil directo
    if (playingChannelRef.current !== "none") {
      const activeAudio =
        playingChannelRef.current === "rec" ? audioRecRef.current : audioOrigRef.current;
      if (activeAudio && activeAudio.duration > 0) {
        const norm = Math.max(0, Math.min(1, (clamped - 4) / 92));
        activeAudio.currentTime = norm * activeAudio.duration;
        setPlayProgress(norm);
        setPlayTime(activeAudio.currentTime);
      }
    }

    applyVars();
    startLoop();
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest("button")) {
      return;
    }
    stateRef.current.sweeping = false;
    setSweeping(false);
    stateRef.current.dragging = true;
    e.currentTarget.setPointerCapture(e.pointerId);
    updateSplitFromClientX(e.clientX);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0 && window.matchMedia("(hover: hover)").matches) {
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;
      stateRef.current.targetTiltX = -ny * 4.5;
      stateRef.current.targetTiltY = nx * 5.5;
      startLoop();
    }
    if (stateRef.current.dragging) {
      updateSplitFromClientX(e.clientX);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    stateRef.current.dragging = false;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // Ignorar si ya fue liberado
    }
  };

  const handlePointerLeave = () => {
    stateRef.current.dragging = false;
    stateRef.current.targetTiltX = 2.2;
    stateRef.current.targetTiltY = -3.0;
    startLoop();
  };

  const triggerSweep = () => {
    stateRef.current.sweeping = true;
    stateRef.current.sweepStart = 0;
    setSweeping(true);
    startLoop();
  };

  const handleAudioEnded = () => {
    setPlayingChannel("none");
    playingChannelRef.current = "none";
    setPlayProgress(0);
    setPlayTime(0);
    stateRef.current.targetSplit = 52;
    startLoop();
  };

  const toggleAudio = (channel: "orig" | "rec") => {
    if (channel === "orig") {
      if (audioRecRef.current) {
        audioRecRef.current.pause();
      }
      if (audioOrigRef.current) {
        if (playingChannel === "orig") {
          audioOrigRef.current.pause();
          setPlayingChannel("none");
          playingChannelRef.current = "none";
          stateRef.current.targetSplit = 52;
          startLoop();
        } else {
          audioOrigRef.current.currentTime = 0;
          audioOrigRef.current
            .play()
            .then(() => {
              setPlayingChannel("orig");
              playingChannelRef.current = "orig";
              stateRef.current.split = 4;
              stateRef.current.targetSplit = 4;
              applyVars();
              startLoop();
            })
            .catch((err) => {
              console.warn("Reproducción no iniciada:", err);
              setPlayingChannel("none");
              playingChannelRef.current = "none";
            });
        }
      }
    } else {
      if (audioOrigRef.current) {
        audioOrigRef.current.pause();
      }
      if (audioRecRef.current) {
        if (playingChannel === "rec") {
          audioRecRef.current.pause();
          setPlayingChannel("none");
          playingChannelRef.current = "none";
          stateRef.current.targetSplit = 52;
          startLoop();
        } else {
          audioRecRef.current.currentTime = 0;
          audioRecRef.current
            .play()
            .then(() => {
              setPlayingChannel("rec");
              playingChannelRef.current = "rec";
              stateRef.current.split = 4;
              stateRef.current.targetSplit = 4;
              applyVars();
              startLoop();
            })
            .catch((err) => {
              console.warn("Reproducción DAC no iniciada:", err);
              setPlayingChannel("none");
              playingChannelRef.current = "none";
            });
        }
      }
    }
  };

  // Convertir perfiles de onda a puntos de SVG Polyline
  const makePoints = (data: number[]) => {
    return data
      .map((val, idx) => {
        const x = (idx / (data.length - 1)) * 100;
        const y = 50 - val * 44;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  };

  return (
    <div className="group relative min-w-0 max-w-full [perspective:1200px]">
      {/* Decorative Technical Radial Array */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-0 top-0 h-36 w-36 rounded-3xl bg-[radial-gradient(#38bdf8_1px,transparent_1px)] opacity-25 [background-size:6px_6px] [mask-image:radial-gradient(circle_at_top_right,#000_25%,transparent_75%)] sm:-right-4 sm:-top-4"
      />

      {/* 3D Chassis Stage Frame driven by GPU CSS vars (--rx / --ry) */}
      <div
        ref={frameRef}
        onPointerLeave={handlePointerLeave}
        className="relative overflow-hidden rounded-2xl border border-(--hairline) bg-(--surface-elevated) shadow-[0_24px_70px_-20px_rgba(0,0,0,0.45)] dark:shadow-[0_28px_80px_-18px_rgba(0,0,0,0.85)] will-change-transform md:[transform-style:preserve-3d] md:[transform:rotateX(var(--rx,2.2deg))_rotateY(var(--ry,-3.0deg))]"
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 z-20 rounded-2xl bg-gradient-to-tr from-transparent via-white/[0.03] to-white/[0.09]"
        />

        {/* Chassis Toolbar */}
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-2 border-b border-(--hairline) bg-(--surface) px-3.5 py-2.5 sm:px-4">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/85 animate-pulse" />
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-(--ink)">
              Comparador Acústico 120 FPS
            </span>
            <span
              ref={readoutRef}
              className="hidden font-mono text-[11px] text-(--ink-muted) sm:inline"
            >
              52% Original / 48% Reconstruida
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Mode Selectors (Onda Dual vs Transiente) */}
            <div className="flex gap-1 rounded-lg border border-(--hairline) bg-(--surface-elevated) p-0.5">
              {(
                [
                  { id: "waveform", label: "Onda Dual" },
                  { id: "transient", label: "Transiente" },
                ] as const
              ).map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setViewMode(mode.id)}
                  className={`rounded-md px-2.5 py-1 font-mono text-[10px] transition ${
                    viewMode === mode.id
                      ? "bg-sky-500 font-semibold text-zinc-950 shadow-sm"
                      : "text-(--ink-muted) hover:text-(--ink)"
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={triggerSweep}
              disabled={sweeping}
              className="inline-flex items-center gap-1 rounded-lg border border-(--hairline) bg-(--surface) px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-(--ink) transition hover:border-sky-500/50 active:scale-[0.97] disabled:opacity-50"
            >
              {sweeping ? (
                <Sparkles className="h-3 w-3 text-sky-500" />
              ) : (
                <Play className="h-3 w-3 text-sky-500" />
              )}
              {sweeping ? "Barriendo..." : "Barrido"}
            </button>
          </div>
        </div>

        {/* Viewport A/B Split Stage */}
        <div
          ref={viewportRef}
          role="slider"
          tabIndex={0}
          aria-label="Separador comparativo audio original versus señal reconstruida DAC"
          aria-valuemin={4}
          aria-valuemax={96}
          aria-valuenow={52}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          style={{ touchAction: "none" }}
          className="relative h-[340px] w-full cursor-ew-resize select-none overflow-hidden bg-zinc-950 sm:h-[380px]"
        >
          {/* Canal B (Fondo base): Reconstrucción DAC Sinc */}
          <div className="absolute inset-0 flex flex-col justify-between p-5 text-emerald-400">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="font-mono text-xs font-semibold text-emerald-400">
                  CANAL B · Reconstrucción Sinc DAC
                </span>
                {viewMode === "transient" && (
                  <span className="hidden sm:inline-block rounded bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-mono text-emerald-300 border border-emerald-500/20">
                    Lóbulos Whittaker-Shannon
                  </span>
                )}
              </div>
              <button
                type="button"
                onPointerDown={(e) => e.stopPropagation()}
                onMouseDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleAudio("rec");
                }}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-[10px] transition ${
                  playingChannel === "rec"
                    ? "border-emerald-400 bg-emerald-500/20 text-emerald-300 shadow-sm"
                    : "border-white/10 bg-zinc-900/90 text-zinc-300 hover:border-emerald-500/50 hover:text-white"
                }`}
              >
                {playingChannel === "rec" ? (
                  <>
                    <Pause className="h-3 w-3 text-emerald-400" />
                    <span>Pausar DAC</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="h-3 w-3 text-emerald-400" />
                    <span>Escuchar DAC</span>
                  </>
                )}
              </button>
            </div>

            {/* SVG Waveform Channel B */}
            <div className="relative my-auto h-40 w-full">
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                className="h-full w-full overflow-visible"
              >
                <polyline
                  fill="none"
                  stroke="rgba(16, 185, 129, 0.9)"
                  strokeWidth={viewMode === "transient" ? "2.0" : "1.6"}
                  strokeLinecap="round"
                  points={makePoints(activeRecWave)}
                />
              </svg>
            </div>

            <div className="flex items-center justify-between font-mono text-[10px] text-zinc-400">
              <span>
                {viewMode === "transient" ? "Zoom Micro-Transiente (20 ms)" : "Interpolación Whittaker-Shannon"}
              </span>
              <span className="text-emerald-400">SNR: {snrDb} dB · r: {pearsonCorr}</span>
            </div>
          </div>

          {/* Canal A (Capa recortada): Voz Acústica Original */}
          <div
            style={{
              clipPath:
                "polygon(0 0, var(--split, 52%) 0, var(--split, 52%) 100%, 0 100%)",
            }}
            className="absolute inset-0 flex flex-col justify-between border-r border-sky-400 bg-zinc-950/95 p-5 text-sky-400 will-change-[clip-path]"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-sky-400" />
                <span className="font-mono text-xs font-semibold text-sky-400">
                  CANAL A · Audio Original (Billie Bossa Nova)
                </span>
                {viewMode === "transient" && (
                  <span className="hidden sm:inline-block rounded bg-sky-500/10 px-1.5 py-0.5 text-[9px] font-mono text-sky-300 border border-sky-500/20">
                    Respuesta Continua
                  </span>
                )}
              </div>
              <button
                type="button"
                onPointerDown={(e) => e.stopPropagation()}
                onMouseDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleAudio("orig");
                }}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-[10px] transition ${
                  playingChannel === "orig"
                    ? "border-sky-400 bg-sky-500/20 text-sky-300 shadow-sm"
                    : "border-white/10 bg-zinc-900/90 text-zinc-300 hover:border-sky-500/50 hover:text-white"
                }`}
              >
                {playingChannel === "orig" ? (
                  <>
                    <Pause className="h-3 w-3 text-sky-400" />
                    <span>Pausar Audio</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="h-3 w-3 text-sky-400" />
                    <span>Escuchar Audio</span>
                  </>
                )}
              </button>
            </div>

            {/* SVG Waveform Channel A */}
            <div className="relative my-auto h-40 w-full">
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                className="h-full w-full overflow-visible"
              >
                <polyline
                  fill="none"
                  stroke="rgba(56, 189, 248, 0.95)"
                  strokeWidth={viewMode === "transient" ? "2.0" : "1.6"}
                  strokeLinecap="round"
                  points={makePoints(activeOrigWave)}
                />
              </svg>
            </div>

            <div className="flex items-center justify-between font-mono text-[10px] text-zinc-400">
              <span>{sampleRate.toLocaleString()} Hz · {durationSec} s</span>
              <span className="text-sky-400">SQNR: {sqnrDb} dB (8 bits)</span>
            </div>
          </div>

          {/* Physical Scrubber Handle Indicator */}
          <div
            style={{ left: "var(--split, 52%)" }}
            className="pointer-events-none absolute inset-y-0 -ml-[1px] flex w-0 items-center justify-center will-change-[left]"
          >
            <div
              className={`absolute inset-y-0 w-[2px] transition-colors duration-150 ${
                playingChannel === "rec"
                  ? "bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,1)]"
                  : playingChannel === "orig"
                  ? "bg-sky-400 shadow-[0_0_14px_rgba(56,189,248,1)]"
                  : "bg-white/70 shadow-[0_0_12px_rgba(255,255,255,0.8)]"
              }`}
            />

            {/* Playhead time indicator tag while active */}
            {playingChannel !== "none" && (
              <div className="absolute -top-7 -translate-x-1/2 flex items-center gap-1.5 rounded-full bg-zinc-950/95 border border-white/20 px-2 py-0.5 text-[9px] font-mono shadow-xl backdrop-blur-md whitespace-nowrap">
                <span
                  className={`w-1.5 h-1.5 rounded-full animate-ping ${
                    playingChannel === "rec" ? "bg-emerald-400" : "bg-sky-400"
                  }`}
                />
                <span className={playingChannel === "rec" ? "text-emerald-300" : "text-sky-300"}>
                  {playTime.toFixed(1)}s / {durationSec.toFixed(1)}s
                </span>
              </div>
            )}

            <div
              className={`z-30 flex h-8 w-8 items-center justify-center rounded-full border bg-zinc-950/95 shadow-xl backdrop-blur-md transition-colors duration-150 ${
                playingChannel === "rec"
                  ? "border-emerald-400/80 text-emerald-400 shadow-emerald-500/20"
                  : playingChannel === "orig"
                  ? "border-sky-400/80 text-sky-400 shadow-sky-500/20"
                  : "border-white/60 text-sky-400"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Real-time playback progress track */}
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-1 bg-white/10 z-20 overflow-hidden">
            <div
              style={{ width: `${playProgress * 100}%` }}
              className={`h-full transition-all duration-75 ${
                playingChannel === "rec"
                  ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]"
                  : "bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.8)]"
              }`}
            />
          </div>
        </div>

        {/* Audio Elements Sync (Forced cache-busting v2.0) */}
        <audio
          ref={audioOrigRef}
          src={safeOrigUrl}
          preload="auto"
          onEnded={handleAudioEnded}
          onError={() => {
            setPlayingChannel("none");
            playingChannelRef.current = "none";
          }}
        />
        <audio
          ref={audioRecRef}
          src={safeRecUrl}
          preload="auto"
          onEnded={handleAudioEnded}
          onError={() => {
            setPlayingChannel("none");
            playingChannelRef.current = "none";
          }}
        />
      </div>
    </div>
  );
}
