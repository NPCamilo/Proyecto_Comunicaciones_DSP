"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Download, Pause, Play, Volume2 } from "lucide-react";

export interface AudioTrackItem {
  id: string;
  code: string;
  title: string;
  subtitle: string;
  src: string;
  accentClass: string;
}

interface AudibleSignalDeckProps {
  tracks: AudioTrackItem[];
}

function formatSec(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) return "00:00.0";
  const mins = Math.floor(sec / 60);
  const rem = sec % 60;
  return `${String(mins).padStart(2, "0")}:${rem.toFixed(1).padStart(4, "0")}`;
}

export function AudibleSignalDeck({ tracks }: AudibleSignalDeckProps) {
  const [activeId, setActiveId] = useState<string>(tracks[0]?.id ?? "");
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playError, setPlayError] = useState<string | null>(null);
  const [phaseTick, setPhaseTick] = useState(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const activeTrack = tracks.find((t) => t.id === activeId) ?? tracks[0];

  // Visualizador armónico determinista con pulso reactivo durante la reproducción
  const bars = useMemo(() => {
    const seed = tracks.findIndex((t) => t.id === activeTrack?.id) + 1;
    return Array.from({ length: 56 }, (_, i) => {
      const base =
        26 +
        Math.abs(Math.sin(i * 0.28 + seed * 1.35) * Math.cos(i * 0.12 - seed)) * 64;
      const mod = playing ? Math.sin(i * 0.45 + phaseTick * 0.35) * 16 : 0;
      return Math.max(14, Math.min(96, Math.round(base + mod)));
    });
  }, [tracks, activeTrack?.id, playing, phaseTick]);

  useEffect(() => {
    if (!playing) return;
    let rafId = 0;
    let last = 0;
    const step = (now: number) => {
      if (now - last >= 70) {
        setPhaseTick((p) => (p + 1) % 1000);
        last = now;
      }
      rafId = window.requestAnimationFrame(step);
    };
    rafId = window.requestAnimationFrame(step);
    return () => window.cancelAnimationFrame(rafId);
  }, [playing]);

  const handleSelectTrack = (id: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setPlayError(null);
    setActiveId(id);
  };

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    setPlayError(null);
    if (audio.paused) {
      try {
        await audio.play();
        setPlaying(true);
      } catch (err) {
        setPlaying(false);
        setPlayError(
          err instanceof Error
            ? `No se pudo iniciar reproducción automática (${err.message}). Usa el reproductor nativo debajo.`
            : "Usa el reproductor nativo debajo para reproducir el audio."
        );
      }
    } else {
      audio.pause();
      setPlaying(false);
    }
  };

  const handleScrub = (ratio: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    const total = audio.duration || duration;
    if (!Number.isFinite(total) || total <= 0) return;
    const next = Math.max(0, Math.min(total, ratio * total));
    audio.currentTime = next;
    setCurrentTime(next);
  };

  const scrubFromPointer = (e: React.PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width > 0) {
      handleScrub((e.clientX - rect.left) / rect.width);
    }
  };

  if (!activeTrack) return null;

  const progress = duration > 0 ? Math.min(1, currentTime / duration) : 0;

  return (
    <div className="overflow-hidden rounded-2xl border border-(--hairline) bg-(--surface)">
      {/* 8-Track Modular Selector Strip */}
      <div className="grid grid-cols-2 border-b border-(--hairline) sm:grid-cols-4 lg:grid-cols-8">
        {tracks.map((track) => {
          const isSelected = track.id === activeTrack.id;
          return (
            <button
              key={track.id}
              type="button"
              onClick={() => handleSelectTrack(track.id)}
              className={`group flex min-w-0 flex-col items-start border-b border-r border-(--hairline) px-3 py-2.5 text-left transition last:border-r-0 lg:border-b-0 ${
                isSelected
                  ? "bg-(--surface-elevated)"
                  : "hover:bg-black/[0.03] dark:hover:bg-white/[0.03]"
              }`}
            >
              <span
                className={`truncate font-mono text-[10px] uppercase tracking-widest ${
                  isSelected ? track.accentClass : "text-(--ink-muted)"
                }`}
              >
                {track.code}
              </span>
              <span className="mt-0.5 line-clamp-1 text-xs font-semibold text-(--ink)">
                {track.title}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main OP-1 Hardware Deck Console */}
      <div className="space-y-4 p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <button
              type="button"
              onClick={togglePlay}
              aria-label={playing ? `Pausar ${activeTrack.title}` : `Reproducir ${activeTrack.title}`}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-(--ink) text-(--canvas) shadow-md transition hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Volume2 className={`h-3.5 w-3.5 shrink-0 ${activeTrack.accentClass}`} />
                <p className="truncate font-display text-sm font-semibold text-(--ink)">
                  {activeTrack.title}
                </p>
              </div>
              <p className="mt-0.5 truncate text-xs text-(--ink-muted)">
                {activeTrack.subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-xs tabular-nums text-(--ink-muted)">
              <strong className="font-semibold text-(--ink)">{formatSec(currentTime)}</strong> /{" "}
              {formatSec(duration)}
            </span>
            <a
              href={activeTrack.src}
              download
              title="Descargar archivo WAV"
              className="inline-flex items-center gap-1 rounded-lg border border-(--hairline) bg-(--surface-elevated) px-2.5 py-1.5 font-mono text-[11px] text-(--ink) transition hover:border-sky-500/50"
            >
              <Download className="h-3.5 w-3.5" /> WAV
            </a>
          </div>
        </div>

        {/* Minimalist Waveform Scrub Bar (Click or Drag with Pointer Capture) */}
        <div
          role="slider"
          tabIndex={0}
          aria-label="Barra de progreso de audio"
          aria-valuemin={0}
          aria-valuemax={Math.round(duration || 100)}
          aria-valuenow={Math.round(currentTime)}
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            scrubFromPointer(e);
          }}
          onPointerMove={(e) => {
            if (e.buttons > 0) scrubFromPointer(e);
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowRight") handleScrub(Math.min(1, progress + 0.05));
            if (e.key === "ArrowLeft") handleScrub(Math.max(0, progress - 0.05));
          }}
          style={{ touchAction: "none" }}
          className="flex h-12 cursor-pointer select-none items-center gap-[3px] rounded-xl border border-(--hairline) bg-(--surface-elevated) px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
        >
          {bars.map((h, idx) => {
            const played = idx / bars.length <= progress;
            return (
              <span
                key={idx}
                style={{ height: `${h}%` }}
                className={`flex-1 rounded-full transition-[height,background-color] duration-100 ${
                  played ? "bg-sky-500" : "bg-zinc-400/35 dark:bg-zinc-600/45"
                }`}
              />
            );
          })}
        </div>

        {/* Synchronized HTML5 native player */}
        <audio
          key={activeTrack.src}
          ref={audioRef}
          controls
          preload="auto"
          src={activeTrack.src}
          onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || 0)}
          onDurationChange={(e) => setDuration(e.currentTarget.duration || 0)}
          onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime || 0)}
          onEnded={() => setPlaying(false)}
          onPause={() => setPlaying(false)}
          onPlay={() => {
            setPlayError(null);
            setPlaying(true);
          }}
          onError={() =>
            setPlayError("El navegador no pudo cargar el archivo WAV desde el servidor actual.")
          }
          className="h-10 w-full rounded-xl"
        />

        {playError && (
          <p className="font-mono text-[11px] text-amber-600 dark:text-amber-300">
            {playError}
          </p>
        )}
      </div>
    </div>
  );
}
