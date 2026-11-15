'use client';

import React, { useEffect, useRef, useState } from 'react';
import { DemoData } from '@/types/dsp';
import { X, Activity, Cpu, Radio, ShieldCheck, Binary, Copy, Check } from 'lucide-react';

interface TelemetryDrawerProps {
  demoData: DemoData | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function TelemetryDrawer({ demoData, isOpen, onClose }: TelemetryDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [activeTab, setActiveTab] = useState<'sampling' | 'pcm' | 'rf' | 'dac'>('sampling');
  const [copiedHex, setCopiedHex] = useState(false);
  const [copiedBin, setCopiedBin] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }
  }, [isOpen]);

  // Handle escape and backdrop click
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (e: Event) => {
      e.preventDefault();
      onClose();
    };

    const handleClick = (e: MouseEvent) => {
      if (e.target === dialog) {
        onClose();
      }
    };

    dialog.addEventListener('cancel', handleCancel);
    dialog.addEventListener('click', handleClick);
    return () => {
      dialog.removeEventListener('cancel', handleCancel);
      dialog.removeEventListener('click', handleClick);
    };
  }, [onClose]);

  if (!demoData) return null;

  const { fase1, fase2, fase3, fase4_5 } = demoData;

  const copyToClipboard = (text: string, type: 'hex' | 'bin') => {
    navigator.clipboard.writeText(text);
    if (type === 'hex') {
      setCopiedHex(true);
      setTimeout(() => setCopiedHex(false), 2000);
    } else {
      setCopiedBin(true);
      setTimeout(() => setCopiedBin(false), 2000);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="fixed inset-0 m-auto z-50 w-[95vw] max-w-4xl max-h-[90vh] bg-zinc-950/95 text-zinc-100 rounded-2xl border border-zinc-800 shadow-2xl backdrop:bg-black/70 backdrop:backdrop-blur-md p-0 overflow-hidden outline-none animate-in fade-in zoom-in-95 duration-200"
      aria-label="Cónsola de Telemetría DSP Acústica"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/60">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-mono text-xs uppercase tracking-wider text-zinc-400">
            TELEMETRY MATRIX // DSP SPEECH PIPELINE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-zinc-400 bg-zinc-800 border border-zinc-700 rounded">
            ESC
          </kbd>
          <button
            onClick={onClose}
            className="p-1 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800/80 transition-colors focus:outline-none focus:ring-1 focus:ring-white/20"
            aria-label="Cerrar telemetría"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Segmented Tab Bar */}
      <div className="flex items-center gap-1 px-6 pt-3 pb-2 border-b border-zinc-800/80 bg-zinc-950 overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('sampling')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === 'sampling'
              ? 'bg-zinc-800 text-white font-medium border border-zinc-700 shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          <span>01. Muestreo & Nyquist</span>
        </button>

        <button
          onClick={() => setActiveTab('pcm')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === 'pcm'
              ? 'bg-zinc-800 text-white font-medium border border-zinc-700 shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
          }`}
        >
          <Binary className="w-3.5 h-3.5 text-emerald-400" />
          <span>02. Digitalización PCM</span>
        </button>

        <button
          onClick={() => setActiveTab('rf')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === 'rf'
              ? 'bg-zinc-800 text-white font-medium border border-zinc-700 shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-amber-400" />
          <span>03. Modulación RF & BER</span>
        </button>

        <button
          onClick={() => setActiveTab('dac')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === 'dac'
              ? 'bg-zinc-800 text-white font-medium border border-zinc-700 shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
          }`}
        >
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span>04. Reconstrucción DAC Sinc</span>
        </button>
      </div>

      {/* Drawer Content */}
      <div className="p-6 overflow-y-auto max-h-[calc(90vh-125px)] text-sm space-y-6">
        {/* TAB 01: Muestreo & Nyquist */}
        {activeTab === 'sampling' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">Frecuencia Muestreo</span>
                <span className="text-lg font-mono font-medium text-white">
                  {(fase1.audio.sample_rate_hz / 1000).toFixed(1)} kHz
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">fs original</span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">fmax Efectiva</span>
                <span className="text-lg font-mono font-medium text-blue-400">
                  {fase1.audio.f_max_effective_hz.toFixed(1)} Hz
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">Espectro de voz</span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">Tasa Nyquist Mínima</span>
                <span className="text-lg font-mono font-medium text-amber-400">
                  {fase1.audio.nyquist_min_rate_hz.toFixed(1)} Hz
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">2 * fmax</span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">Margen Nyquist</span>
                <span className="text-lg font-mono font-medium text-emerald-400">
                  +{(fase1.audio.nyquist_margin_hz / 1000).toFixed(2)} kHz
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">fs - 2*fmax</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase text-zinc-400">Veredicto Criterio Nyquist-Shannon</span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  CUMPLE SIN ALIASING
                </span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                {fase1.audio.nyquist_verdict}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="text-xs font-mono text-zinc-400">Voltaje Pico (Vp)</span>
                <p className="text-base font-mono text-white mt-1">
                  {fase1.audio.peak_amplitude.toFixed(4)} V
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="text-xs font-mono text-zinc-400">Voltaje RMS</span>
                <p className="text-base font-mono text-white mt-1">
                  {fase1.audio.rms_voltage.toFixed(4)} V
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <span className="text-xs font-mono text-zinc-400">Factor de Cresta / Dinámica</span>
                <p className="text-base font-mono text-white mt-1">
                  {fase1.audio.crest_factor.toFixed(2)} ({fase1.audio.dynamic_range_db.toFixed(1)} dB)
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 02: PCM */}
        {activeTab === 'pcm' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">fs Submuestreada</span>
                <span className="text-lg font-mono font-medium text-white">
                  {(fase1.sampling_pcm.downsampled_rate_hz / 1000).toFixed(1)} kHz
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">NQS Submuestreo</span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">Resolución PCM</span>
                <span className="text-lg font-mono font-medium text-emerald-400">
                  {fase1.sampling_pcm.bits_per_sample} bits
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">
                  {fase1.sampling_pcm.quantization_levels} niveles cuánticos
                </span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">Paso Cuantización (Δ)</span>
                <span className="text-lg font-mono font-medium text-blue-400">
                  {fase1.sampling_pcm.step_size_delta.toFixed(5)} V
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">2 * Vp / 2^b</span>
              </div>
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80">
                <span className="text-zinc-500 text-xs font-mono block">SQNR Empírica</span>
                <span className="text-lg font-mono font-medium text-purple-400">
                  {fase1.sampling_pcm.sqnr_empirical_db.toFixed(2)} dB
                </span>
                <span className="text-[10px] text-zinc-500 font-mono block mt-1">
                  Teórica: {fase1.sampling_pcm.sqnr_theoretical_db.toFixed(1)} dB
                </span>
              </div>
            </div>

            {/* Hex and Binary Stream Dump */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs uppercase text-zinc-400">
                    Hexadecimal Dump (Primeros 16 Bytes codificados)
                  </span>
                  <button
                    onClick={() => copyToClipboard(fase1.sampling_pcm.first_bytes_hex, 'hex')}
                    className="flex items-center gap-1.5 px-2 py-1 text-xs font-mono text-zinc-400 hover:text-white rounded bg-zinc-800 hover:bg-zinc-700 transition-colors"
                  >
                    {copiedHex ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedHex ? 'Copiado' : 'Copiar Hex'}</span>
                  </button>
                </div>
                <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800/90 font-mono text-xs text-emerald-400 tracking-wider break-all select-all">
                  {fase1.sampling_pcm.first_bytes_hex}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs uppercase text-zinc-400">
                    Binary Stream Dump (Primeros 64 Bits PCM)
                  </span>
                  <button
                    onClick={() => copyToClipboard(fase1.sampling_pcm.first_64_bits, 'bin')}
                    className="flex items-center gap-1.5 px-2 py-1 text-xs font-mono text-zinc-400 hover:text-white rounded bg-zinc-800 hover:bg-zinc-700 transition-colors"
                  >
                    {copiedBin ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedBin ? 'Copiado' : 'Copiar Bits'}</span>
                  </button>
                </div>
                <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800/90 font-mono text-xs text-blue-400 tracking-widest break-all select-all">
                  {fase1.sampling_pcm.first_64_bits.match(/.{1,8}/g)?.join(' ')}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 03: Modulación RF & BER */}
        {activeTab === 'rf' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* AM Card */}
              <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-3">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <span className="font-mono text-xs font-semibold text-blue-400">AM-FC Analógica</span>
                  <span className="text-[10px] font-mono text-zinc-500">DSB-FC</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Portadora (fc):</span>
                    <span className="text-white">{(fase2.am.carrier_freq_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Índice Mod (μ):</span>
                    <span className="text-white">{fase2.am.modulation_index_mu.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Eficiencia RF:</span>
                    <span className="text-emerald-400">{fase2.am.efficiency_percent.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Demod Coherente SNR:</span>
                    <span className="text-emerald-400">{fase3.am_coherent.snr_db.toFixed(2)} dB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Demod Envolvente SNR:</span>
                    <span className="text-amber-400">{fase3.am_envelope.snr_db.toFixed(2)} dB</span>
                  </div>
                </div>
              </div>

              {/* FM Card */}
              <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-3">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <span className="font-mono text-xs font-semibold text-purple-400">FM-WBFM Analógica</span>
                  <span className="text-[10px] font-mono text-zinc-500">{fase2.fm.regime}</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Portadora (fc):</span>
                    <span className="text-white">{(fase2.fm.carrier_freq_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Desviación (Δf):</span>
                    <span className="text-white">{(fase2.fm.freq_deviation_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Índice β:</span>
                    <span className="text-white">{fase2.fm.beta.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Ancho Carson (BW):</span>
                    <span className="text-purple-400">{(fase2.fm.carson_bw_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Demod Discrim SNR:</span>
                    <span className="text-emerald-400">{fase3.fm_discriminator.snr_db.toFixed(2)} dB</span>
                  </div>
                </div>
              </div>

              {/* FSK Card */}
              <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-3">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <span className="font-mono text-xs font-semibold text-emerald-400">FSK Digital</span>
                  <span className="text-[10px] font-mono text-zinc-500">2-FSK</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Frecuencia f0 (Bit 0):</span>
                    <span className="text-white">{(fase2.fsk.f0_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Frecuencia f1 (Bit 1):</span>
                    <span className="text-white">{(fase2.fsk.f1_hz / 1000).toFixed(1)} kHz</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Tasa Símbolo (Rb):</span>
                    <span className="text-white">{fase2.fsk.bit_rate_bps.toFixed(0)} bps</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Bits Procesados:</span>
                    <span className="text-white">{fase3.fsk_digital.total_bits.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between border-t border-zinc-800/80 pt-1 mt-1">
                    <span className="text-emerald-400 font-semibold">Tasa Error Bit (BER):</span>
                    <span className="text-emerald-400 font-bold">{fase3.fsk_digital.ber_display}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 04: DAC */}
        {activeTab === 'dac' && (
          <div className="space-y-6">
            <div className="overflow-x-auto rounded-xl border border-zinc-800">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-zinc-900/80 text-zinc-400 border-b border-zinc-800">
                  <tr>
                    <th className="py-3 px-4">Método DAC</th>
                    <th className="py-3 px-4">SNR (dB)</th>
                    <th className="py-3 px-4">PSNR (dB)</th>
                    <th className="py-3 px-4">Pearson r</th>
                    <th className="py-3 px-4">MSE</th>
                    <th className="py-3 px-4">Distorsión Espectral</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 bg-zinc-950">
                  <tr className="hover:bg-zinc-900/30">
                    <td className="py-3 px-4 font-semibold text-emerald-400">
                      Sinc Interpolation (Whittaker-Shannon)
                    </td>
                    <td className="py-3 px-4 text-white font-medium">
                      {fase4_5.dac_sinc.snr_db.toFixed(2)} dB
                    </td>
                    <td className="py-3 px-4 text-white">
                      {fase4_5.dac_sinc.psnr_db.toFixed(2)} dB
                    </td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">
                      {fase4_5.dac_sinc.pearson_corr.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-zinc-400">
                      {fase4_5.dac_sinc.mse.toExponential(3)}
                    </td>
                    <td className="py-3 px-4 text-zinc-400">
                      {fase4_5.dac_sinc.spectral_distortion_db.toFixed(2)} dB
                    </td>
                  </tr>
                  <tr className="hover:bg-zinc-900/30">
                    <td className="py-3 px-4 font-semibold text-amber-400">
                      Zero-Order Hold (ZOH Escalonado)
                    </td>
                    <td className="py-3 px-4 text-white font-medium">
                      {fase4_5.dac_zoh.snr_db.toFixed(2)} dB
                    </td>
                    <td className="py-3 px-4 text-white">
                      {fase4_5.dac_zoh.psnr_db.toFixed(2)} dB
                    </td>
                    <td className="py-3 px-4 text-amber-400 font-bold">
                      {fase4_5.dac_zoh.pearson_corr.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-zinc-400">
                      {fase4_5.dac_zoh.mse.toExponential(3)}
                    </td>
                    <td className="py-3 px-4 text-zinc-400">
                      {fase4_5.dac_zoh.spectral_distortion_db.toFixed(2)} dB
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 space-y-2">
              <span className="font-mono text-xs uppercase text-zinc-400">
                Conclusión Teórica Whittaker-Shannon
              </span>
              <p className="text-xs text-zinc-400 leading-relaxed">
                La interpolación Sinc sinc(π·(t - n·Ts)/Ts) recupera de forma continua y sin armónicos espurios la señal de voz analógica, superando a la reconstrucción ZOH por más de 10 dB en relación señal-a-ruido y eliminando los escalones que generan atenuación en alta frecuencia tipo sinc(f/fs).
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-zinc-800 bg-zinc-900/40 flex items-center justify-between text-xs font-mono text-zinc-500">
        <span>DSP Audio Telemetry Engine v{demoData.project.version}</span>
        <button
          onClick={onClose}
          className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg transition-colors"
        >
          Cerrar
        </button>
      </div>
    </dialog>
  );
}
