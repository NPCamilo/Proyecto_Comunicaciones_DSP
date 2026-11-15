'use client';

import React, { useState, useRef } from 'react';
import { LiveAudioProcessResponse } from '@/types/dsp';
import {
  Upload,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  Radio,
  Cpu,
  CheckCircle2,
  AlertCircle,
  FileAudio,
  Sparkles,
  Download
} from 'lucide-react';

export default function LiveAudioTransceiver() {
  const [file, setFile] = useState<File | null>(null);
  const [useSynthetic, setUseSynthetic] = useState(false);
  const [sampleRate, setSampleRate] = useState<number>(16000);
  const [pcmBits, setPcmBits] = useState<number>(8);
  const [modulation, setModulation] = useState<string>('am');
  const [carrierFreq, setCarrierFreq] = useState<number>(20000);
  const [amMode, setAmMode] = useState<string>('coherent');
  const [dacMethod, setDacMethod] = useState<string>('sinc');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LiveAudioProcessResponse | null>(null);

  // Audio players
  const [activePlayer, setActivePlayer] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      // Max 100MB (~10 min audio)
      if (selected.size > 100 * 1024 * 1024) {
        setError('El archivo excede el límite máximo de 100 MB (~10 minutos de audio).');
        return;
      }
      setFile(selected);
      setUseSynthetic(false);
      setError(null);
    }
  };

  const handleProcess = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      if (!useSynthetic) {
        if (!file) {
          setError('Por favor selecciona un archivo de audio o activa la generación de voz sintética.');
          setLoading(false);
          return;
        }
        formData.append('file', file);
      }
      formData.append('sample_rate', sampleRate.toString());
      formData.append('pcm_bits', pcmBits.toString());
      formData.append('modulation', modulation);
      formData.append('carrier_freq', carrierFreq.toString());
      formData.append('am_mode', amMode);
      formData.append('dac_method', dacMethod);

      const res = await fetch('/api/audio/process', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Error en el servidor (${res.status})`);
      }

      const data: LiveAudioProcessResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Error procesando el pipeline de audio.');
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (b64Audio: string | undefined, tag: string) => {
    if (!b64Audio) return;
    if (activePlayer === tag && audioRef.current) {
      if (audioRef.current.paused) {
        audioRef.current.play();
      } else {
        audioRef.current.pause();
        setActivePlayer(null);
      }
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(`data:audio/wav;base64,${b64Audio}`);
    audioRef.current = audio;
    setActivePlayer(tag);
    audio.play();
    audio.onended = () => setActivePlayer(null);
  };

  return (
    <div id="workbench" className="scroll-mt-24 space-y-10">
      <audio ref={audioRef} className="hidden" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-(--hairline)">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-(--ink-muted) uppercase">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>05 // Banco de Pruebas Transceptor en Vivo</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-(--ink)">
            Laboratorio Interactivo de Audio DSP
          </h2>
          <p className="max-w-2xl text-sm sm:text-base text-(--ink-muted) leading-relaxed">
            Inyecta cualquier archivo de audio de hasta 10 minutos (WAV o MP3) o genera habla sintética armónica para experimentar en tiempo real con frecuencias de muestreo Nyquist, resolución PCM, modulación analógica o digital y reconstrucción DAC Sinc.
          </p>
        </div>
      </div>

      {/* Control Panel Bento */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Controls Column */}
        <div className="lg:col-span-6 space-y-6">
          {/* File Input Card */}
          <div className="p-6 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                <FileAudio className="w-4 h-4 text-emerald-400" />
                Fuente de Audio de Entrada (Máx 10 min)
              </span>
              <button
                type="button"
                onClick={() => {
                  setUseSynthetic(!useSynthetic);
                  if (!useSynthetic) setFile(null);
                }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                  useSynthetic
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'bg-zinc-800 text-zinc-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{useSynthetic ? 'Usando Sintético' : 'Generar Voz Sintética'}</span>
              </button>
            </div>

            {!useSynthetic ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-zinc-700 hover:border-emerald-500/60 rounded-xl p-6 text-center cursor-pointer transition-colors bg-black/20 group"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/wav,audio/mp3,audio/x-wav,audio/mpeg"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <Upload className="w-8 h-8 mx-auto text-zinc-500 group-hover:text-emerald-400 transition-colors mb-2" />
                {file ? (
                  <div className="space-y-1">
                    <p className="font-mono text-xs font-medium text-emerald-400 truncate">{file.name}</p>
                    <p className="font-mono text-[10px] text-zinc-500">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB // Listo para procesar
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs text-zinc-300">Arrastra un audio o haz clic para explorar</p>
                    <p className="text-[10px] font-mono text-zinc-500">WAV, MP3 hasta 100 MB (10 minutos)</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs font-mono text-purple-300 space-y-1">
                <p className="font-semibold">Voz Sintética Formántica Multitonal</p>
                <p className="text-[11px] text-purple-400/80">
                  Genera una señal de prueba armónica que simula formantes vocálicos humanos (200 Hz fundamental + armónicos en 700 Hz y 2400 Hz) con modulación de amplitud envolvente.
                </p>
              </div>
            )}
          </div>

          {/* DSP Configuration Parameters */}
          <div className="p-6 rounded-2xl border border-(--hairline) bg-(--surface-elevated) space-y-5">
            <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Parámetros de Telecomunicaciones DSP
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Sample Rate */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-(--ink-muted) block">
                  Tasa Muestreo fs (Hz):
                </label>
                <select
                  value={sampleRate}
                  onChange={(e) => setSampleRate(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value={8000}>8,000 Hz (Telefonía NQS)</option>
                  <option value={16000}>16,000 Hz (Banda Ancha Voz)</option>
                  <option value={24000}>24,000 Hz (Estudio HD)</option>
                  <option value={44100}>44,100 Hz (Calidad CD)</option>
                </select>
              </div>

              {/* PCM Resolution */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-(--ink-muted) block">
                  Resolución PCM (bits):
                </label>
                <select
                  value={pcmBits}
                  onChange={(e) => setPcmBits(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value={4}>4 bits (16 niveles, SQNR ~25 dB)</option>
                  <option value={8}>8 bits (256 niveles, SQNR ~49 dB)</option>
                  <option value={16}>16 bits (65536 niveles, SQNR ~98 dB)</option>
                </select>
              </div>

              {/* Modulation Scheme */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-(--ink-muted) block">
                  Esquema de Modulación:
                </label>
                <select
                  value={modulation}
                  onChange={(e) => setModulation(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="none">Sin Modulación (Banda Base)</option>
                  <option value="am">AM-FC (Analógica DSB)</option>
                  <option value="fm">FM-WBFM (Analógica)</option>
                  <option value="fsk">2-FSK (Digital)</option>
                  <option value="ask">ASK (Digital)</option>
                  <option value="bpsk">BPSK (Digital)</option>
                </select>
              </div>

              {/* Carrier Frequency */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-(--ink-muted) block">
                  Frecuencia Portadora fc:
                </label>
                <select
                  value={carrierFreq}
                  disabled={modulation === 'none'}
                  onChange={(e) => setCarrierFreq(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-40"
                >
                  <option value={10000}>10,000 Hz</option>
                  <option value={20000}>20,000 Hz</option>
                  <option value={30000}>30,000 Hz</option>
                  <option value={40000}>40,000 Hz</option>
                </select>
              </div>

              {/* AM Mode */}
              {modulation === 'am' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-(--ink-muted) block">
                    Modo Demodulación AM:
                  </label>
                  <select
                    value={amMode}
                    onChange={(e) => setAmMode(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="coherent">Coherente (Sincrónica)</option>
                    <option value="envelope">Detector de Envolvente</option>
                  </select>
                </div>
              )}

              {/* DAC Reconstruction */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-(--ink-muted) block">
                  Reconstrucción DAC:
                </label>
                <select
                  value={dacMethod}
                  onChange={(e) => setDacMethod(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="sinc">Sinc (Whittaker-Shannon Ideal)</option>
                  <option value="zoh">ZOH (Zero-Order Hold Escalonado)</option>
                </select>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400 text-xs font-mono">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Execute Button */}
            <button
              type="button"
              disabled={loading}
              onClick={handleProcess}
              className="w-full py-3 px-4 rounded-xl font-mono text-xs font-semibold tracking-wider uppercase transition-all bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/20 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  <span>Procesando DSP en Tiempo Real...</span>
                </>
              ) : (
                <>
                  <Cpu className="w-4 h-4" />
                  <span>Ejecutar Pipeline DSP Completo</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results & Waveform Column */}
        <div className="lg:col-span-6 space-y-6">
          <div className="p-6 rounded-2xl border border-(--hairline) bg-(--surface-elevated) min-h-[460px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-(--hairline)">
                <span className="font-mono text-xs uppercase tracking-wider text-(--ink-muted) flex items-center gap-2">
                  <Radio className="w-4 h-4 text-emerald-400" />
                  Telemetría del Transceptor en Vivo
                </span>
                {result && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Procesado exitosamente
                  </span>
                )}
              </div>

              {result ? (
                <div className="mt-5 space-y-5">
                  {/* Performance metrics banner */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-black/40 border border-zinc-800">
                      <span className="text-[10px] font-mono text-zinc-500 block">SNR Fidelidad</span>
                      <span className="text-base font-mono font-bold text-emerald-400">
                        {result.snr_db.toFixed(2)} dB
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-zinc-800">
                      <span className="text-[10px] font-mono text-zinc-500 block">Pearson r</span>
                      <span className="text-base font-mono font-bold text-white">
                        {result.pearson_corr.toFixed(4)}
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-zinc-800">
                      <span className="text-[10px] font-mono text-zinc-500 block">SQNR Cuantiz.</span>
                      <span className="text-base font-mono font-bold text-blue-400">
                        {result.sqnr_db.toFixed(1)} dB
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-zinc-800">
                      <span className="text-[10px] font-mono text-zinc-500 block">Duración</span>
                      <span className="text-base font-mono font-bold text-purple-400">
                        {result.duration_s.toFixed(2)} s
                      </span>
                    </div>
                  </div>

                  {/* Audio Listeners */}
                  <div className="space-y-3 pt-2">
                    <span className="font-mono text-xs text-zinc-400 block">
                      Escuchar Etapas Procesadas:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {result.audio_original_b64 && (
                        <button
                          onClick={() => playAudio(result.audio_original_b64, 'original')}
                          className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono transition-colors ${
                            activePlayer === 'original'
                              ? 'bg-blue-500/20 border-blue-500/40 text-blue-300'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                          }`}
                        >
                          <span>1. Audio Original</span>
                          {activePlayer === 'original' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                      )}

                      {result.audio_modulated_b64 && (
                        <button
                          onClick={() => playAudio(result.audio_modulated_b64, 'mod')}
                          className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono transition-colors ${
                            activePlayer === 'mod'
                              ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                          }`}
                        >
                          <span>2. Señal RF Modulada</span>
                          {activePlayer === 'mod' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                      )}

                      {result.audio_demodulated_b64 && (
                        <button
                          onClick={() => playAudio(result.audio_demodulated_b64, 'demod')}
                          className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono transition-colors ${
                            activePlayer === 'demod'
                              ? 'bg-purple-500/20 border-purple-500/40 text-purple-300'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                          }`}
                        >
                          <span>3. Audio Demodulado</span>
                          {activePlayer === 'demod' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                      )}

                      {result.audio_reconstructed_b64 && (
                        <button
                          onClick={() => playAudio(result.audio_reconstructed_b64, 'rec')}
                          className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono transition-colors ${
                            activePlayer === 'rec'
                              ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                          }`}
                        >
                          <span>4. Reconstrucción DAC</span>
                          {activePlayer === 'rec' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Waveform Canvas Representation */}
                  <div className="pt-2">
                    <span className="font-mono text-xs text-zinc-400 block mb-2">
                      Oscilograma Comparativo (Original vs Reconstruido):
                    </span>
                    <div className="h-28 w-full bg-black/60 rounded-xl border border-zinc-800 relative flex items-center justify-center p-2 overflow-hidden">
                      {/* SVG Waveform render */}
                      <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                        {/* Original in Blue */}
                        <polyline
                          fill="none"
                          stroke="#38bdf8"
                          strokeWidth="1.2"
                          strokeOpacity="0.7"
                          points={result.waveform_original
                            .map((v, i) => `${(i / (result.waveform_original.length - 1)) * 100},${50 - v * 45}`)
                            .join(' ')}
                        />
                        {/* Reconstructed in Emerald */}
                        <polyline
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="1.2"
                          strokeDasharray="2,2"
                          points={result.waveform_reconstructed
                            .map((v, i) => `${(i / (result.waveform_reconstructed.length - 1)) * 100},${50 - v * 45}`)
                            .join(' ')}
                        />
                      </svg>
                      <div className="absolute bottom-1 right-2 flex items-center gap-3 text-[10px] font-mono">
                        <span className="flex items-center gap-1 text-sky-400">
                          <span className="w-2 h-0.5 bg-sky-400 inline-block" /> Original
                        </span>
                        <span className="flex items-center gap-1 text-emerald-400">
                          <span className="w-2 h-0.5 bg-emerald-400 inline-block" /> DAC Sinc
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-20 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-500">
                    <Cpu className="w-6 h-6" />
                  </div>
                  <p className="text-xs font-mono text-zinc-400">
                    El oscilograma y métricas en vivo aparecerán aquí tras la ejecución.
                  </p>
                </div>
              )}
            </div>

            {result?.audio_reconstructed_b64 && (
              <div className="pt-4 border-t border-(--hairline) mt-4 flex justify-end">
                <a
                  href={`data:audio/wav;base64,${result.audio_reconstructed_b64}`}
                  download="audio_procesado_sinc.wav"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-white transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Descargar WAV Reconstruido</span>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
