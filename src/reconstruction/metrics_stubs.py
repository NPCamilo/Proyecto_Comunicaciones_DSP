"""
Módulo de Reconstrucción y Comparativa de Calidad - Stubs y Guía para Colaborador 3 (Fase 4)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

ESTE MÓDULO CORRESPONDE AL PUNTO 6 DEL PROYECTO:
"6. Reconstrucción:
    - Reconstruir la señal de audio a partir de los datos digitalizados y/o demodulados.
    - Generar un nuevo archivo WAV.
    - Reproducir el audio reconstruido.
    - Comparar auditivamente y gráficamente la señal original y la señal reconstruida."
"""

from typing import Optional, Tuple
import numpy as np
import scipy.signal as signal_proc
import matplotlib.pyplot as plt

from ..core.base import AudioSignal, DigitalStream, PerformanceMetrics, BaseReconstructor
from ..core.audio_io import save_wav, play_audio


class AudioReconstructor(BaseReconstructor):
    """
    Reconstructor DAC de señal analógica continua a partir de muestras discretas
    o flujos cuantizados.
    
    Técnicas implementables:
      1. Whittaker-Shannon (Interpolación Sinc Ideal):
         x_r(t) = sum_{n} x[n] * sinc((t - n*Ts) / Ts)
      2. Zero-Order Hold (ZOH) + Filtro de Reconstrucción (Smoothing Filter):
         Retenedor de orden cero seguido por un filtro paso bajo Butterworth
         diseñado a la frecuencia de corte f_c <= fs/2.
    """

    def __init__(self, method: str = "zoh_filtered", cutoff_ratio: float = 0.45):
        self.method = method
        self.cutoff_ratio = cutoff_ratio

    def reconstruct_from_quantized(self, stream: DigitalStream) -> AudioSignal:
        """
        Reconstruye la señal de audio a partir del flujo digital cuantizado.
        """
        raw_samples = stream.reconstructed_levels
        fs = stream.sample_rate

        if self.method == "zoh_filtered":
            # Filtro analógico de suavizado (Butterworth paso-bajo orden 4)
            b, a = signal_proc.butter(4, self.cutoff_ratio, btype='low')
            smoothed = signal_proc.filtfilt(b, a, raw_samples)
        else:
            smoothed = raw_samples

        peak = np.max(np.abs(smoothed)) or 1.0
        norm_samples = (smoothed / peak * 0.95).astype(np.float32)

        return AudioSignal(
            samples=norm_samples,
            sample_rate=fs,
            bit_depth=16,
            metadata={"reconstruction_method": self.method, "bits": stream.bits_per_sample}
        )

    def reconstruct(self, samples: np.ndarray, target_rate: int, **kwargs) -> AudioSignal:
        """Reconstruye a partir de muestras directas."""
        return AudioSignal(samples=samples.astype(np.float32), sample_rate=target_rate)

    def evaluate_fidelity(self, original: AudioSignal, reconstructed: AudioSignal) -> PerformanceMetrics:
        """
        Calcula rigurosamente las métricas cuantitativas de distorsión y fidelidad:
          - MSE (Error Cuadrático Medio)
          - SNR (Relación Señal a Ruido en dB)
          - PSNR (Peak Signal-to-Noise Ratio en dB)
          - Coeficiente de correlación de Pearson (r in [-1, 1])
        """
        # Alinear longitud de muestras
        min_len = min(len(original.samples), len(reconstructed.samples))
        x = original.samples[:min_len]
        y = reconstructed.samples[:min_len]

        # 1. Error cuadrático medio
        error = x - y
        mse = float(np.mean(error ** 2))

        # 2. Relación Señal a Ruido (SNR)
        power_sig = float(np.mean(x ** 2))
        power_err = mse
        if power_err > 1e-12:
            snr_db = float(10 * np.log10(power_sig / power_err))
            psnr_db = float(10 * np.log10(1.0 / power_err))
        else:
            snr_db = 99.9
            psnr_db = 99.9

        # 3. Correlación de Pearson
        vx = x - np.mean(x)
        vy = y - np.mean(y)
        denom = np.sqrt(np.sum(vx ** 2) * np.sum(vy ** 2))
        if denom > 1e-12:
            corr = float(np.sum(vx * vy) / denom)
        else:
            corr = 0.0

        return PerformanceMetrics(
            mse=mse,
            snr_db=snr_db,
            psnr_db=psnr_db,
            pearson_corr=corr,
            spectral_distortion_db=0.0
        )


def plot_fidelity_comparison(original: AudioSignal, reconstructed: AudioSignal,
                             metrics: PerformanceMetrics, save_path: Optional[str] = None,
                             show: bool = False) -> plt.Figure:
    """
    Gráfica comparativa de alta fidelidad entre la señal original y la reconstruida.
    Muestra:
      1. Superposición en el dominio del tiempo con el residuo de error.
      2. Superposición de los espectros de magnitud en frecuencia.
    """
    min_len = min(len(original.samples), len(reconstructed.samples))
    t = original.time_vector[:min_len]
    x = original.samples[:min_len]
    y = reconstructed.samples[:min_len]
    err = x - y

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, color='#30363d', linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    # Panel 1: Dominio del Tiempo
    ax1.plot(t, x, color='#58a6ff', linewidth=1.1, label='x(t) Original')
    ax1.plot(t, y, color='#3fb950', linewidth=1.0, linestyle='--', label='x_rec(t) Reconstruida')
    ax1.plot(t, err, color='#f85149', linewidth=0.8, alpha=0.6, label='Error e(t) = x - x_rec')
    ax1.set_title(
        f"Comparación Temporal: Original vs Reconstruida | "
        f"SNR = {metrics.snr_db:.2f} dB | MSE = {metrics.mse:.5f} | Correlación = {metrics.pearson_corr:.4f}",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax1.set_xlabel("Tiempo [s]", color='#c9d1d9')
    ax1.set_ylabel("Amplitud Normalizada", color='#c9d1d9')
    ax1.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right')

    # Panel 2: Dominio de la Frecuencia
    fs = original.sample_rate
    fft_x = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fft_y = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / fs)
    
    db_x = 20 * np.log10(np.clip(fft_x / (np.max(fft_x) + 1e-12), 1e-5, 1.0))
    db_y = 20 * np.log10(np.clip(fft_y / (np.max(fft_y) + 1e-12), 1e-5, 1.0))

    ax2.plot(freqs, db_x, color='#58a6ff', linewidth=1.1, label='Espectro Original |X(f)|')
    ax2.plot(freqs, db_y, color='#3fb950', linewidth=1.0, linestyle='--', label='Espectro Reconstruido |Y(f)|')
    ax2.set_title("Comparación Espectral (Fidelidad de Armónicos y Formantes Vocales)",
                  color='#f0f6fc', fontsize=11, fontweight='bold', pad=8)
    ax2.set_xlabel("Frecuencia [Hz]", color='#c9d1d9')
    ax2.set_ylabel("Magnitud [dBFS]", color='#c9d1d9')
    ax2.set_xlim(0, fs / 2.0)
    ax2.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right')

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    if show:
        plt.show()

    return fig
