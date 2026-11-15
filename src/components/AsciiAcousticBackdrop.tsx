"use client";

import { useEffect, useRef } from "react";

interface AsciiAcousticBackdropProps {
  active?: boolean;
  theme?: "dark" | "light";
}

const ACOUSTIC_RAMP = " ·:-=+*#%@";

const DARK_PALETTE = Array.from({ length: ACOUSTIC_RAMP.length }, (_, idx) => {
  const alpha = (0.05 + (idx / ACOUSTIC_RAMP.length) * 0.15).toFixed(3);
  return `rgba(161, 161, 170, ${alpha})`;
});

const LIGHT_PALETTE = Array.from({ length: ACOUSTIC_RAMP.length }, (_, idx) => {
  const alpha = (0.05 + (idx / ACOUSTIC_RAMP.length) * 0.14).toFixed(3);
  return `rgba(24, 24, 27, ${alpha})`;
});

export function AsciiAcousticBackdrop({
  active = true,
  theme = "dark",
}: AsciiAcousticBackdropProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const palette = theme === "dark" ? DARK_PALETTE : LIGHT_PALETTE;
    const resonantColor =
      theme === "dark" ? "rgba(56, 189, 248, 0.36)" : "rgba(2, 132, 199, 0.36)";
    const harmonicPeakColor =
      theme === "dark" ? "rgba(244, 63, 94, 0.24)" : "rgba(225, 29, 72, 0.24)";

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    let animId = 0;
    let width = 0;
    let height = 0;
    let cols = 0;
    let rows = 0;
    let cell = 22;

    const pointer = {
      x: 0.5,
      y: 0.35,
      targetX: 0.5,
      targetY: 0.35,
      energy: 0,
    };

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      const isMobile = width < 768;
      const dpr = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 1.5);
      cell = isMobile ? 30 : 22;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.font = '600 12px "Geist Mono", ui-monospace, monospace';
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      cols = Math.ceil(width / cell) + 1;
      rows = Math.ceil(height / cell) + 1;
    };

    const drawFrame = (timeSec: number) => {
      ctx.clearRect(0, 0, width, height);

      pointer.x += (pointer.targetX - pointer.x) * 0.08;
      pointer.y += (pointer.targetY - pointer.y) * 0.08;
      pointer.energy *= 0.96;

      const px = pointer.x * width;
      const py = pointer.y * height;

      for (let r = 0; r < rows; r++) {
        const y = r * cell + cell * 0.5;
        const dy = y - py;
        const dySq = dy * dy;
        // Longitudinal acoustic carrier envelope
        const acousticP = Math.cos(r * 0.21 - timeSec * 0.95);

        for (let c = 0; c < cols; c++) {
          const x = c * cell + cell * 0.5;
          const dx = x - px;
          const distSq = dx * dx + dySq;

          // Soundwave modulation: Fundamental frequency + 2nd Harmonic
          const fundamental = Math.sin(c * 0.24 + timeSec * 1.25) * acousticP;
          const harmonic2 = Math.sin((c * 2 + r) * 0.14 - timeSec * 0.8) * 0.42;

          let acousticShockwave = 0;
          let dist = 999;
          if (distSq < 115600) {
            dist = Math.sqrt(distSq);
            // Doppler acoustic ripple expanding outward
            acousticShockwave =
              Math.sin(dist * 0.048 - timeSec * 4.8) *
              (1 - dist / 340) *
              (0.8 + pointer.energy * 0.7);
          }

          const pressureAmplitude = (fundamental + harmonic2 + acousticShockwave + 1.45) / 2.9;
          const clamped =
            pressureAmplitude < 0 ? 0 : pressureAmplitude > 0.999 ? 0.999 : pressureAmplitude;
          const charIdx = (clamped * ACOUSTIC_RAMP.length) | 0;

          if (charIdx <= 1) continue;

          const ch = ACOUSTIC_RAMP[charIdx];
          ctx.fillStyle =
            dist < 260 && charIdx >= 6
              ? resonantColor
              : charIdx >= 7
                ? harmonicPeakColor
                : palette[charIdx];
          ctx.fillText(ch, x, y);
        }
      }
    };

    const onPointerMove = (e: PointerEvent) => {
      if (width <= 0 || height <= 0) return;
      pointer.targetX = e.clientX / width;
      pointer.targetY = e.clientY / height;
      pointer.energy = 1;
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    if (!active || mediaQuery.matches) {
      drawFrame(0.8);
      return () => {
        window.removeEventListener("resize", resize);
        window.removeEventListener("pointermove", onPointerMove);
      };
    }

    let lastRender = 0;
    const loop = (now: number) => {
      if (!document.hidden && now - lastRender >= 33) {
        drawFrame(now * 0.001);
        lastRender = now;
      }
      animId = window.requestAnimationFrame(loop);
    };

    const onVisibilityChange = () => {
      if (!document.hidden) lastRender = 0;
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    animId = window.requestAnimationFrame(loop);

    return () => {
      window.cancelAnimationFrame(animId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
    };
  }, [active, theme]);

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-(--canvas) transition-colors duration-300 [contain:strict]"
    >
      {/* Acoustic Frequency Mesh Grid */}
      <div
        className={`absolute inset-0 [background-size:24px_24px] [mask-image:radial-gradient(ellipse_75%_65%_at_50%_20%,#000_55%,transparent_100%)] ${
          theme === "dark"
            ? "bg-[radial-gradient(#ffffff12_1px,transparent_1px)]"
            : "bg-[radial-gradient(#11111314_1px,transparent_1px)]"
        }`}
      />

      {/* Real-time Oscillating Acoustic ASCII Soundwave Canvas */}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 transition-opacity duration-500 [mask-image:radial-gradient(ellipse_85%_80%_at_50%_35%,#000_50%,transparent_100%)] ${
          active ? "opacity-100" : "opacity-25"
        }`}
      />

      {/* Soundwave Atmospheric Ambient Glow Orbs */}
      <div
        className={`absolute -left-32 -top-40 h-[520px] w-[520px] rounded-full blur-[130px] ${
          theme === "dark" ? "bg-sky-500/12" : "bg-sky-500/10"
        }`}
      />
      <div
        className={`absolute -right-24 top-16 h-[460px] w-[460px] rounded-full blur-[140px] ${
          theme === "dark" ? "bg-amber-500/10" : "bg-amber-500/8"
        }`}
      />
      <div
        className={`absolute bottom-0 left-1/3 h-[380px] w-[560px] rounded-full blur-[140px] ${
          theme === "dark" ? "bg-emerald-500/8" : "bg-emerald-500/8"
        }`}
      />

      {/* Monochromatic Acoustic Grain Texture */}
      <svg
        className={`absolute inset-0 h-full w-full mix-blend-overlay ${
          theme === "dark" ? "opacity-[0.03]" : "opacity-[0.025]"
        }`}
      >
        <filter id="audio-dsp-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.82"
            numOctaves="3"
            stitchTiles="stitch"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#audio-dsp-grain)" />
      </svg>
    </div>
  );
}
