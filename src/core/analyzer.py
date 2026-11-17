"""
Módulo de Análisis Temporal y Espectral (Puntos 2 y 3 del Proyecto)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt

from .base import AudioSignal


def analyze_signal_properties(signal: AudioSignal, energy_percent: float = 0.99) -> Dict[str, Any]:
    """
    Realiza una caracterización cuantitativa exhaustiva de la señal de audio
    en el dominio del tiempo y la frecuencia.
    
    Args:
        signal (AudioSignal): Señal de audio a caracterizar.
        energy_percent (float): Porcentaje acumulado de energía (e.g. 0.99 = 99%)
                                para estimar el ancho de banda efectivo f_max.
                                
    Returns:
        Dict[str, Any]: Diccionario con parámetros temporales, espectrales y de Nyquist.
    """
    x = signal.samples
    fs = signal.sample_rate
    n = len(x)
    ts = 1.0 / fs if fs > 0 else 0.0
    duration = n * ts

    # Métricas temporales
    peak_val = float(np.max(np.abs(x)))
    rms_val = float(np.sqrt(np.mean(x ** 2)))
    crest_factor = float(peak_val / rms_val) if rms_val > 1e-6 else 0.0
    dc_offset = float(np.mean(x))
    dynamic_range_db = float(20 * np.log10(peak_val / (rms_val + 1e-9)))

    # Métricas espectrales (FFT de un solo lado con ventana Hann)
    freqs, mag_linear, mag_db = compute_spectrum(signal, window="hann")
    f_max_eff = estimate_max_frequency(freqs, mag_linear, energy_threshold=energy_percent)
    f_nyquist_req = 2.0 * f_max_eff
    nyquist_margin = fs - f_nyquist_req
    nyquist_satisfied = bool(fs >= f_nyquist_req)

    results = {
        "sample_rate_hz": fs,
        "sampling_period_s": ts,
        "sampling_period_ms": ts * 1000.0,
        "total_samples": n,
        "duration_s": duration,
        "peak_amplitude": peak_val,
        "rms_amplitude": rms_val,
        "crest_factor": crest_factor,
        "dc_offset": dc_offset,
        "dynamic_range_db": dynamic_range_db,
        "f_max_effective_hz": f_max_eff,
        "f_nyquist_minimum_hz": f_nyquist_req,
        "nyquist_satisfied": nyquist_satisfied,
        "nyquist_margin_hz": nyquist_margin,
    }

    # Adjuntar a metadatos de la señal
    signal.metadata.update(results)
    return results


def compute_spectrum(signal: AudioSignal, window: str = "hann") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula la Transformada Rápida de Fourier (FFT) unilateral de amplitud calibrada.
    
    Args:
        signal (AudioSignal): Señal de entrada.
        window (str): Tipo de ventaneo ('hann', 'hamming', 'boxcar' / rectangular).
        
    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]:
            - freqs: Vector de frecuencias [0, fs/2] (Hz)
            - mag_linear: Amplitud lineal normalizada
            - mag_db: Amplitud espectral en dBFS (0 dBFS = pico máximo)
    """
    x = signal.samples
    n = len(x)
    fs = signal.sample_rate

    # Aplicación de ventana para mitigar dispersión espectral (spectral leakage)
    if window == "hann":
        win = np.hanning(n)
    elif window == "hamming":
        win = np.hamming(n)
    else:
        win = np.ones(n)

    # Factor de escala por pérdida de energía de la ventana
    coherent_gain = np.sum(win) / n
    x_win = x * win

    # FFT unilateral
    fft_vals = np.fft.rfft(x_win)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    # Magnitud normalizada de un solo lado (duplicando componentes AC)
    mag_linear = np.abs(fft_vals) / (n * coherent_gain)
    if len(mag_linear) > 2:
        mag_linear[1:-1] *= 2.0  # Conservar energía unilateral

    # Evitar logaritmo de cero
    mag_db = 20 * np.log10(np.clip(mag_linear / (np.max(mag_linear) + 1e-12), 1e-6, 1.0))

    return freqs, mag_linear, mag_db


def estimate_max_frequency(freqs: np.ndarray, mag_linear: np.ndarray, energy_threshold: float = 0.99) -> float:
    """
    Estima la frecuencia máxima significativa f_max integrando la energía espectral acumulada.
    Para señales de voz humana, esto delimita la banda base útil (ancho de banda efectivo).
    """
    energy = mag_linear ** 2
    total_energy = np.sum(energy)
    if total_energy <= 1e-12:
        return float(freqs[-1])

    cumulative_energy = np.cumsum(energy) / total_energy
    idx = np.searchsorted(cumulative_energy, energy_threshold)
    idx = min(idx, len(freqs) - 1)
    return float(freqs[idx])


def plot_time_and_frequency(signal: AudioSignal, save_path: Optional[str] = None,
                            show: bool = False, title_prefix: str = "Billie Bossa Nova (Billie Eilish)") -> plt.Figure:
    """
    Genera una visualización técnica con doble panel:
      1. Forma de onda en el dominio del tiempo s(t) con límites y nivel RMS.
      2. Espectro de magnitud en el dominio de la frecuencia |S(f)| indicando f_max y Nyquist.
      
    Args:
        signal (AudioSignal): Señal a graficar.
        save_path (Optional[str]): Ruta para exportar imagen (.png).
        show (bool): Si True, llama a plt.show().
        title_prefix (str): Título superior de la figura.
        
    Returns:
        plt.Figure: Objeto de figura de Matplotlib.
    """
    props = analyze_signal_properties(signal)
    freqs, _, mag_db = compute_spectrum(signal)
    t = signal.time_vector

    fig, (ax_time, ax_freq) = plt.subplots(2, 1, figsize=(11, 7.5), constrained_layout=True)
    fig.patch.set_facecolor('#090d16')

    # Configuración de estilos técnicos oscuros
    for ax in (ax_time, ax_freq):
        ax.set_facecolor('#111827')
        ax.tick_params(colors='#94a3b8', labelsize=9)
        ax.grid(True, color='#1e293b', linestyle='--', linewidth=0.7, alpha=0.85)
        for spine in ax.spines.values():
            spine.set_color('#1e293b')

    # --- PANEL 1: DOMINIO DEL TIEMPO ---
    ax_time.fill_between(t, signal.samples, 0, color='#38bdf8', alpha=0.25)
    ax_time.plot(t, signal.samples, color='#38bdf8', linewidth=0.6, label='s(t) Amplitud Acústica (Billie Bossa Nova)')
    ax_time.axhline(props['rms_amplitude'], color='#34d399', linestyle=':', linewidth=1.3,
                   label=f"Nivel RMS (+{props['rms_amplitude']:.3f} V)")
    ax_time.axhline(-props['rms_amplitude'], color='#34d399', linestyle=':', linewidth=1.3,
                   label=f"Nivel RMS (-{props['rms_amplitude']:.3f} V)")
    ax_time.set_title(f"1. Forma de Onda Temporal: {title_prefix} (fs = {signal.sample_rate:,} Hz | {signal.duration:.1f} s)",
                      color='#f8fafc', fontsize=11, fontweight='bold', pad=10)
    ax_time.set_xlabel("Tiempo [segundos]", color='#cbd5e1', fontsize=9.5)
    ax_time.set_ylabel("Amplitud Normalizada [-1.0, 1.0]", color='#cbd5e1', fontsize=9.5)
    ax_time.set_xlim(0, signal.duration)
    ax_time.set_ylim(-1.05, 1.05)
    ax_time.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', loc='upper right', fontsize=8.5)

    # --- PANEL 2: DOMINIO DE LA FRECUENCIA ---
    ax_freq.fill_between(freqs, mag_db, -65, color='#a855f7', alpha=0.18)
    ax_freq.plot(freqs, mag_db, color='#c084fc', linewidth=0.8, label='Espectro Normalizado |S(f)|')
    f_max = props['f_max_effective_hz']
    f_nyq = props['f_nyquist_minimum_hz']
    
    ax_freq.axvline(f_max, color='#f87171', linestyle='--', linewidth=1.4,
                    label=f"f_max (99% energía acústica) = {f_max:,.1f} Hz")
    ax_freq.axvline(f_nyq, color='#fbbf24', linestyle='-.', linewidth=1.4,
                    label=f"Tasa Nyquist Requerida (2·f_max) = {f_nyq:,.1f} Hz")
    
    ax_freq.set_title(f"2. Espectro de Magnitud Unilateral - Billie Bossa Nova (Transformada Rápida de Fourier)",
                      color='#f8fafc', fontsize=11, fontweight='bold', pad=10)
    ax_freq.set_xlabel("Frecuencia [Hz]", color='#cbd5e1', fontsize=9.5)
    ax_freq.set_ylabel("Magnitud Normalizada [dBFS]", color='#cbd5e1', fontsize=9.5)
    ax_freq.set_ylim(-65, 5)
    ax_freq.set_xlim(0, min(props['sample_rate_hz'] / 2.0, max(8000.0, f_nyq * 1.5)))
    ax_freq.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', loc='upper right', fontsize=8.5)

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"[Grafica] Figura exportada a: {save_path}")

    if show:
        plt.show()

    return fig
