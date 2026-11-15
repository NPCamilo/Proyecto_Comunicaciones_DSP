'use client';

import React, { useMemo, useState } from 'react';
import { DemoData } from '@/types/dsp';
import { OptimizedPicture } from './OptimizedPicture';
import { ImageLightboxDialog, LightboxAsset } from './ImageLightboxDialog';
import { AudibleSignalDeck, AudioTrackItem } from './AudibleSignalDeck';
import {
  Maximize2,
  ShieldCheck,
  Binary,
  Radio,
  Download,
  FileCode,
  Music,
  CheckCircle2,
  Cpu,
} from 'lucide-react';

interface EditorialShowcaseProps {
  demoData: DemoData;
}

export default function EditorialShowcase({ demoData }: EditorialShowcaseProps) {
  const [lightboxAsset, setLightboxAsset] = useState<LightboxAsset | null>(null);
  const [exhibit2Plot, setExhibit2Plot] = useState<'nqs' | 'quant'>('nqs');
  const [rfPlot, setRfPlot] = useState<'am' | 'fm' | 'fsk' | 'translation' | 'modes'>('am');

  const { fase1, fase2, fase3, fase4_5, assets } = demoData;

  const tracks: AudioTrackItem[] = useMemo(
    () => [
      {
        id: 'track-1-orig',
        code: 'CH 01',
        title: 'Voz Original Acústica',
        subtitle: `Entrada PCM · fs = ${(fase1.audio.sample_rate_hz / 1000).toFixed(1)} kHz`,
        src: assets.wav_original,
        accentClass: 'text-sky-400',
      },
      {
        id: 'track-2-am-tx',
        code: 'CH 02',
        title: 'Modulación AM-FC (TX)',
        subtitle: `Portadora fc = ${(fase2.am.carrier_freq_hz / 1000).toFixed(1)} kHz · μ = ${fase2.am.modulation_index_mu.toFixed(2)}`,
        src: assets.wav_mod_am,
        accentClass: 'text-amber-400',
      },
      {
        id: 'track-3-fm-tx',
        code: 'CH 03',
        title: 'Modulación FM-WBFM (TX)',
        subtitle: `Portadora fc = ${(fase2.fm.carrier_freq_hz / 1000).toFixed(1)} kHz · β = ${fase2.fm.beta.toFixed(2)}`,
        src: assets.wav_mod_fm,
        accentClass: 'text-purple-400',
      },
      {
        id: 'track-4-fsk-tx',
        code: 'CH 04',
        title: 'Modulación Digital 2-FSK (TX)',
        subtitle: `f0 = ${(fase2.fsk.f0_hz / 1000).toFixed(1)} kHz, f1 = ${(fase2.fsk.f1_hz / 1000).toFixed(1)} kHz · ${fase2.fsk.bit_rate_bps.toFixed(0)} bps`,
        src: assets.wav_mod_fsk,
        accentClass: 'text-pink-400',
      },
      {
        id: 'track-5-am-coh',
        code: 'CH 05',
        title: 'Demodulación AM Coherente (RX)',
        subtitle: `Receptor sincrónico · SNR = ${fase3.am_coherent.snr_db.toFixed(2)} dB`,
        src: assets.wav_demod_am_coherent,
        accentClass: 'text-emerald-400',
      },
      {
        id: 'track-6-am-env',
        code: 'CH 06',
        title: 'Demodulación AM Envolvente (RX)',
        subtitle: `Detector pico no lineal · SNR = ${fase3.am_envelope.snr_db.toFixed(2)} dB`,
        src: assets.wav_demod_am_envelope,
        accentClass: 'text-yellow-400',
      },
      {
        id: 'track-7-fm-disc',
        code: 'CH 07',
        title: 'Demodulación FM Discriminador (RX)',
        subtitle: `Detector de cruces por cero · SNR = ${fase3.fm_discriminator.snr_db.toFixed(2)} dB`,
        src: assets.wav_demod_fm,
        accentClass: 'text-indigo-400',
      },
      {
        id: 'track-8-dac-sinc',
        code: 'CH 08',
        title: 'Reconstrucción DAC Sinc Whittaker',
        subtitle: `Salida analógica final · SNR = ${fase4_5.dac_sinc.snr_db.toFixed(2)} dB · r = ${fase4_5.dac_sinc.pearson_corr.toFixed(4)}`,
        src: assets.wav_reconstructed_sinc,
        accentClass: 'text-teal-400',
      },
    ],
    [fase1, fase2, fase3, fase4_5, assets]
  );

  const openLightbox = (src: string, title: string, caption?: string) => {
    setLightboxAsset({ src, title, caption });
  };

  return (
    <div className="space-y-32">
      {/* Lightbox Modal */}
      <ImageLightboxDialog asset={lightboxAsset} onClose={() => setLightboxAsset(null)} />

      {/* EXHIBIT 01: Adquisición & Espectro */}
      <section id="exhibit-01" className="scroll-mt-24 space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-(--hairline)">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-(--ink-muted) uppercase">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span>01 // Adquisición Acústica & FFT</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-(--ink)">
              Espectro de la Voz Humana
            </h2>
            <p className="max-w-2xl text-sm sm:text-base text-(--ink-muted) leading-relaxed">
              Captura temporal de voz continua a { (fase1.audio.sample_rate_hz / 1000).toFixed(1) } kHz. Se realiza la Transformada Rápida de Fourier (FFT) para identificar el ancho de banda efectivo y verificar la ausencia de aliasing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              Nyquist: Margen +{(fase1.audio.nyquist_margin_hz / 1000).toFixed(1)} kHz
            </span>
          </div>
        </div>

        {/* Bento Grid: Figure + Telemetry Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Main Visual Plot */}
          <div className="lg:col-span-8 group relative rounded-2xl border border-(--hairline) bg-(--surface-elevated) p-3 overflow-hidden shadow-sm hover:border-(--hairline-hover) transition-all">
            <div className="relative aspect-16/9 w-full rounded-xl overflow-hidden bg-black/40">
              <OptimizedPicture
                src={assets.fig_time_spectrum}
                alt="Señal temporal y espectro de voz original"
                className="w-full h-full object-contain"
              />
              <button
                onClick={() =>
                  openLightbox(
                    assets.fig_time_spectrum,
                    'Adquisición de Audio: Forma de Onda y Espectro FFT',
                    `fs = ${fase1.audio.sample_rate_hz} Hz, fmax = ${fase1.audio.f_max_effective_hz.toFixed(1)} Hz`
                  )
                }
                className="absolute top-3 right-3 p-2 rounded-lg bg-black/60 hover:bg-black/90 text-white backdrop-blur-md transition-opacity opacity-0 group-hover:opacity-100 focus:opacity-100"
                aria-label="Ampliar gráfica de espectro"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center justify-between px-3 pt-3 text-xs font-mono text-(--ink-muted)">
              <span>Figura 01: Dominio Temporal y Espectro FFT (Voz Original)</span>
              <span>fs: {(fase1.audio.sample_rate_hz / 1000).toFixed(1)} kHz</span>
            </div>
          </div>

          {/* Quick Stats Column */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-5 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-4">
              <h3 className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-500" />
                Parámetros Espectrales
              </h3>
              <dl className="space-y-3 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-(--hairline)">
                  <dt className="text-(--ink-muted)">Frecuencia Máxima:</dt>
                  <dd className="font-semibold text-(--ink)">{fase1.audio.f_max_effective_hz.toFixed(1)} Hz</dd>
                </div>
                <div className="flex justify-between py-1 border-b border-(--hairline)">
                  <dt className="text-(--ink-muted)">Tasa Nyquist (2·fmax):</dt>
                  <dd className="font-semibold text-blue-400">{fase1.audio.nyquist_min_rate_hz.toFixed(1)} Hz</dd>
                </div>
                <div className="flex justify-between py-1 border-b border-(--hairline)">
                  <dt className="text-(--ink-muted)">Voltaje Pico (Vp):</dt>
                  <dd className="font-semibold text-(--ink)">{fase1.audio.peak_amplitude.toFixed(4)} V</dd>
                </div>
                <div className="flex justify-between py-1 border-b border-(--hairline)">
                  <dt className="text-(--ink-muted)">Voltaje RMS:</dt>
                  <dd className="font-semibold text-(--ink)">{fase1.audio.rms_voltage.toFixed(4)} V</dd>
                </div>
                <div className="flex justify-between py-1 border-b border-(--hairline)">
                  <dt className="text-(--ink-muted)">Factor de Cresta:</dt>
                  <dd className="font-semibold text-purple-400">{fase1.audio.crest_factor.toFixed(2)}</dd>
                </div>
                <div className="flex justify-between py-1">
                  <dt className="text-(--ink-muted)">Rango Dinámico:</dt>
                  <dd className="font-semibold text-emerald-400">{fase1.audio.dynamic_range_db.toFixed(1)} dB</dd>
                </div>
              </dl>
            </div>

            <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 text-xs text-(--ink-muted) leading-relaxed">
              <p>
                <strong className="font-semibold text-(--ink)">Criterio de Ancho de Banda:</strong> La mayor energía formántica vocal se localiza por debajo de los 3.5 kHz. Al muestrear a 16 o 48 kHz, la condición <code className="text-blue-400">fs &gt; 2·fmax</code> se satisface con amplio margen espectral de guarda.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* EXHIBIT 02: Nyquist-Shannon & PCM */}
      <section id="exhibit-02" className="scroll-mt-24 space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-(--hairline)">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-(--ink-muted) uppercase">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>02 // Teorema Nyquist-Shannon & PCM</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-(--ink)">
              Digitalización por Modulación por Impulsos Codificados
            </h2>
            <p className="max-w-2xl text-sm sm:text-base text-(--ink-muted) leading-relaxed">
              Muestreo a tasa óptima de Nyquist y cuantización uniforme con resolución de {fase1.sampling_pcm.bits_per_sample} bits ({fase1.sampling_pcm.quantization_levels} niveles). Relación señal a ruido de cuantización experimental: {fase1.sampling_pcm.sqnr_empirical_db.toFixed(2)} dB.
            </p>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center p-1 rounded-xl bg-(--surface-elevated) border border-(--hairline)">
            <button
              onClick={() => setExhibit2Plot('nqs')}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                exhibit2Plot === 'nqs'
                  ? 'bg-emerald-500 text-white font-medium shadow-sm'
                  : 'text-(--ink-muted) hover:text-(--ink)'
              }`}
            >
              Muestreo Nyquist
            </button>
            <button
              onClick={() => setExhibit2Plot('quant')}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                exhibit2Plot === 'quant'
                  ? 'bg-emerald-500 text-white font-medium shadow-sm'
                  : 'text-(--ink-muted) hover:text-(--ink)'
              }`}
            >
              Cuantización & SQNR
            </button>
          </div>
        </div>

        {/* Content Bento */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-8 group relative rounded-2xl border border-(--hairline) bg-(--surface-elevated) p-3 overflow-hidden shadow-sm hover:border-(--hairline-hover) transition-all">
            <div className="relative aspect-16/9 w-full rounded-xl overflow-hidden bg-black/40">
              <OptimizedPicture
                src={exhibit2Plot === 'nqs' ? assets.fig_nqs : assets.fig_quantization}
                alt={exhibit2Plot === 'nqs' ? 'Muestreo Nyquist-Shannon' : 'Cuantización PCM y Error de Ruido'}
                className="w-full h-full object-contain"
              />
              <button
                onClick={() =>
                  openLightbox(
                    exhibit2Plot === 'nqs' ? assets.fig_nqs : assets.fig_quantization,
                    exhibit2Plot === 'nqs' ? 'Muestreo Nyquist-Shannon' : 'Cuantización PCM Uniforme (8 bits)',
                    exhibit2Plot === 'nqs'
                      ? `fs submuestreado = ${fase1.sampling_pcm.downsampled_rate_hz} Hz`
                      : `Δ = ${fase1.sampling_pcm.step_size_delta.toFixed(5)} V, SQNR = ${fase1.sampling_pcm.sqnr_empirical_db.toFixed(2)} dB`
                  )
                }
                className="absolute top-3 right-3 p-2 rounded-lg bg-black/60 hover:bg-black/90 text-white backdrop-blur-md transition-opacity opacity-0 group-hover:opacity-100 focus:opacity-100"
                aria-label="Ampliar gráfica de digitalización"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center justify-between px-3 pt-3 text-xs font-mono text-(--ink-muted)">
              <span>
                {exhibit2Plot === 'nqs'
                  ? 'Figura 02A: Espectro y Replicación Periódica por Muestreo'
                  : 'Figura 02B: Cuantización de Amplitud e Histograma de Error e[n]'}
              </span>
              <span>Resolución: {fase1.sampling_pcm.bits_per_sample} bits</span>
            </div>
          </div>

          {/* PCM Bitstream Sample Box */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-5 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-3">
              <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                <Binary className="w-3.5 h-3.5 text-emerald-400" />
                Flujo PCM Codificado (Trama Demo)
              </span>

              <div className="space-y-2">
                <span className="text-[11px] font-mono text-(--ink-muted) block">
                  Secuencia Binaria (Primeros 64 bits):
                </span>
                <div className="p-2.5 rounded-lg bg-black/60 font-mono text-[11px] text-emerald-400 tracking-wider break-all leading-relaxed select-all">
                  {fase1.sampling_pcm.first_64_bits.match(/.{1,8}/g)?.join(' ')}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[11px] font-mono text-(--ink-muted) block">
                  Hex Dump (Primeros 16 Bytes):
                </span>
                <div className="p-2.5 rounded-lg bg-black/60 font-mono text-[11px] text-blue-400 tracking-wider break-all select-all">
                  {fase1.sampling_pcm.first_bytes_hex}
                </div>
              </div>

              <div className="pt-2 border-t border-(--hairline) flex justify-between items-center text-xs font-mono">
                <span className="text-(--ink-muted)">SQNR Teórica:</span>
                <span className="text-white font-medium">{fase1.sampling_pcm.sqnr_theoretical_db.toFixed(1)} dB</span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-(--ink-muted)">SQNR Experimental:</span>
                <span className="text-emerald-400 font-semibold">{fase1.sampling_pcm.sqnr_empirical_db.toFixed(2)} dB</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* EXHIBIT 03: Transceptor Audible & Modulación RF */}
      <section id="exhibit-03" className="scroll-mt-24 space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-(--hairline)">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-(--ink-muted) uppercase">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>03 // Consola de Transmisión RF & Demodulación</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-(--ink)">
              Cónsola de Audio 8-Pistas & Radiotransmisión
            </h2>
            <p className="max-w-2xl text-sm sm:text-base text-(--ink-muted) leading-relaxed">
              Consola de audio en hardware analógico y digital. Reproduce y analiza las 8 etapas del flujo completo: modulación analógica AM-FC, modulación de frecuencia FM-WBFM, transmisión digital FSK y sus respectivos receptores.
            </p>
          </div>
        </div>

        {/* Master 8-Track Audible Hardware Console */}
        <AudibleSignalDeck tracks={tracks} />

        {/* RF Spectral Figures Switcher */}
        <div className="space-y-4 pt-6">
          <div className="flex items-center justify-between flex-wrap gap-3 pb-3 border-b border-(--hairline)">
            <h3 className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
              <Radio className="w-4 h-4 text-amber-400" />
              Espectros y Oscilogramas RF
            </h3>

            <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
              <button
                onClick={() => setRfPlot('am')}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  rfPlot === 'am' ? 'bg-amber-500 text-black font-semibold' : 'text-(--ink-muted) hover:text-(--ink)'
                }`}
              >
                AM-FC Analógica
              </button>
              <button
                onClick={() => setRfPlot('fm')}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  rfPlot === 'fm' ? 'bg-amber-500 text-black font-semibold' : 'text-(--ink-muted) hover:text-(--ink)'
                }`}
              >
                FM Banda Ancha
              </button>
              <button
                onClick={() => setRfPlot('fsk')}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  rfPlot === 'fsk' ? 'bg-amber-500 text-black font-semibold' : 'text-(--ink-muted) hover:text-(--ink)'
                }`}
              >
                2-FSK Digital
              </button>
              <button
                onClick={() => setRfPlot('translation')}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  rfPlot === 'translation' ? 'bg-amber-500 text-black font-semibold' : 'text-(--ink-muted) hover:text-(--ink)'
                }`}
              >
                Traslación Espectral
              </button>
              <button
                onClick={() => setRfPlot('modes')}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                  rfPlot === 'modes' ? 'bg-amber-500 text-black font-semibold' : 'text-(--ink-muted) hover:text-(--ink)'
                }`}
              >
                Modos Demod AM
              </button>
            </div>
          </div>

          {/* Active RF Plot View */}
          <div className="group relative rounded-2xl border border-(--hairline) bg-(--surface-elevated) p-3 overflow-hidden shadow-sm hover:border-(--hairline-hover) transition-all">
            <div className="relative aspect-16/9 w-full rounded-xl overflow-hidden bg-black/40">
              <OptimizedPicture
                src={
                  rfPlot === 'am'
                    ? assets.fig_mod_am
                    : rfPlot === 'fm'
                    ? assets.fig_mod_fm
                    : rfPlot === 'fsk'
                    ? assets.fig_mod_fsk
                    : rfPlot === 'translation'
                    ? assets.fig_spectrum_translation
                    : assets.fig_am_modes
                }
                alt={`Espectro y modulación ${rfPlot}`}
                className="w-full h-full object-contain"
              />
              <button
                onClick={() => {
                  const currentSrc =
                    rfPlot === 'am'
                      ? assets.fig_mod_am
                      : rfPlot === 'fm'
                      ? assets.fig_mod_fm
                      : rfPlot === 'fsk'
                      ? assets.fig_mod_fsk
                      : rfPlot === 'translation'
                      ? assets.fig_spectrum_translation
                      : assets.fig_am_modes;
                  openLightbox(currentSrc, `Análisis de Modulación RF: ${rfPlot.toUpperCase()}`);
                }}
                className="absolute top-3 right-3 p-2 rounded-lg bg-black/60 hover:bg-black/90 text-white backdrop-blur-md transition-opacity opacity-0 group-hover:opacity-100 focus:opacity-100"
                aria-label="Ampliar gráfica de modulación RF"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* EXHIBIT 04: Reconstrucción Whittaker-Shannon & Fidelidad */}
      <section id="exhibit-04" className="scroll-mt-24 space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-(--hairline)">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-(--ink-muted) uppercase">
              <span className="w-2 h-2 rounded-full bg-purple-500" />
              <span>04 // Reconstrucción DAC Whittaker-Shannon</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-(--ink)">
              Interpolación Sinc vs Zero-Order Hold (ZOH)
            </h2>
            <p className="max-w-2xl text-sm sm:text-base text-(--ink-muted) leading-relaxed">
              La interpolación ideal Sinc restaura la forma de onda continua alcanzando una correlación de Pearson de r = {fase4_5.dac_sinc.pearson_corr.toFixed(4)} y SNR = {fase4_5.dac_sinc.snr_db.toFixed(2)} dB, superando ampliamente a la retención de orden cero (ZOH).
            </p>
          </div>
        </div>

        {/* Comparison Plot + Metrics Table */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-8 group relative rounded-2xl border border-(--hairline) bg-(--surface-elevated) p-3 overflow-hidden shadow-sm hover:border-(--hairline-hover) transition-all">
            <div className="relative aspect-16/9 w-full rounded-xl overflow-hidden bg-black/40">
              <OptimizedPicture
                src={assets.fig_fidelity_comparison}
                alt="Comparativa de fidelidad de reconstrucción DAC Sinc vs ZOH"
                className="w-full h-full object-contain"
              />
              <button
                onClick={() =>
                  openLightbox(
                    assets.fig_fidelity_comparison,
                    'Comparativa de Fidelidad: Sinc vs ZOH',
                    `Sinc SNR: ${fase4_5.dac_sinc.snr_db.toFixed(2)} dB, ZOH SNR: ${fase4_5.dac_zoh.snr_db.toFixed(2)} dB`
                  )
                }
                className="absolute top-3 right-3 p-2 rounded-lg bg-black/60 hover:bg-black/90 text-white backdrop-blur-md transition-opacity opacity-0 group-hover:opacity-100 focus:opacity-100"
                aria-label="Ampliar comparativa de fidelidad"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center justify-between px-3 pt-3 text-xs font-mono text-(--ink-muted)">
              <span>Figura 04: Señal Original vs Interpolación Sinc vs ZOH Escalonado</span>
              <span className="text-emerald-400">ΔSNR: +{(fase4_5.dac_sinc.snr_db - fase4_5.dac_zoh.snr_db).toFixed(2)} dB</span>
            </div>
          </div>

          {/* DAC Metrics Box */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-5 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-4">
              <h3 className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-purple-400" />
                Métricas Cuantitativas de Fidelidad
              </h3>

              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-emerald-400 font-semibold">DAC Sinc (Whittaker):</span>
                    <span className="text-emerald-300 font-bold">{fase4_5.dac_sinc.snr_db.toFixed(2)} dB</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-zinc-400">
                    <span>Pearson r: {fase4_5.dac_sinc.pearson_corr.toFixed(4)}</span>
                    <span>MSE: {fase4_5.dac_sinc.mse.toExponential(2)}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-amber-400 font-semibold">DAC ZOH (Escalón):</span>
                    <span className="text-amber-300 font-bold">{fase4_5.dac_zoh.snr_db.toFixed(2)} dB</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-zinc-400">
                    <span>Pearson r: {fase4_5.dac_zoh.pearson_corr.toFixed(4)}</span>
                    <span>MSE: {fase4_5.dac_zoh.mse.toExponential(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Downloads Vault */}
            <div className="p-5 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-3">
              <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                <Download className="w-3.5 h-3.5 text-blue-400" />
                Bóveda de Archivos Generados
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <a
                  href={assets.wav_original}
                  download="voz_original.wav"
                  className="flex items-center gap-1.5 p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
                >
                  <Music className="w-3 h-3 text-blue-400" />
                  <span className="truncate">Voz Original</span>
                </a>
                <a
                  href={assets.wav_reconstructed_sinc}
                  download="audio_sinc.wav"
                  className="flex items-center gap-1.5 p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
                >
                  <Music className="w-3 h-3 text-emerald-400" />
                  <span className="truncate">DAC Sinc</span>
                </a>
                <a
                  href={assets.bin_stream}
                  download="flujo_pcm.bin"
                  className="flex items-center gap-1.5 p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
                >
                  <FileCode className="w-3 h-3 text-amber-400" />
                  <span className="truncate">Trama .BIN</span>
                </a>
                <a
                  href={assets.json_metadata}
                  download="datos_demo.json"
                  className="flex items-center gap-1.5 p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors"
                >
                  <FileCode className="w-3 h-3 text-purple-400" />
                  <span className="truncate">JSON Meta</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
