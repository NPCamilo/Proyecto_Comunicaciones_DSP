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

import os
from typing import Optional, Tuple
import numpy as np
import scipy.signal as signal_proc
import matplotlib.pyplot as plt

from ..core.base import (
    AudioSignal,
    DigitalStream,
    DemodulatedResult,
    PerformanceMetrics,
    BaseReconstructor,
)
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

    def __init__(self, method: str = "zoh_filtered", cutoff_ratio: float = 0.45,
                 sinc_half_width: int = 32, block_size: int = 8192):
        self.method = method
        self.cutoff_ratio = cutoff_ratio
        self.sinc_half_width = int(sinc_half_width)
        self.block_size = int(block_size)

    def _zoh_interpolate(self, samples: np.ndarray, input_rate: int,
                         target_rate: int) -> np.ndarray:
        """Retenedor de orden cero (ZOH) para remuestrear de input_rate a target_rate."""
        x = np.asarray(samples, dtype=np.float64)
        if len(x) == 0:
            return np.array([], dtype=np.float32)
        if int(input_rate) == int(target_rate):
            return x.astype(np.float32)

        num_out = int(np.floor(len(x) * float(target_rate) / float(input_rate)))
        positions = np.arange(num_out, dtype=np.float64) * (float(input_rate) / float(target_rate))
        indices = np.clip(np.floor(positions).astype(np.int64), 0, len(x) - 1)
        return x[indices].astype(np.float32)

    def _sinc_interpolate(self, samples: np.ndarray, input_rate: int, target_rate: int,
                          half_width: Optional[int] = None,
                          block_size: Optional[int] = None) -> np.ndarray:
        """
        Interpolación Sinc ideal de Whittaker-Shannon evaluada por bloques:
            x_r(t) = sum_n x[n] * sinc((t - n*Ts) / Ts)
        Se usa una ventana de Lanczos de soporte finito para limitar el costo
        computacional y evitar matrices de tamaño N x N en señales largas.
        """
        x = np.asarray(samples, dtype=np.float64)
        if len(x) == 0:
            return np.array([], dtype=np.float32)
        if input_rate <= 0 or target_rate <= 0:
            raise ValueError("Las frecuencias de muestreo deben ser positivas.")

        half_width = int(self.sinc_half_width if half_width is None else half_width)
        block_size = int(self.block_size if block_size is None else block_size)
        block_size = max(1, block_size)
        half_width = max(1, half_width)

        ratio = float(target_rate) / float(input_rate)
        num_out = int(np.floor(len(x) * ratio))
        if num_out == 0:
            return np.array([], dtype=np.float32)

        offsets = np.arange(-half_width + 1, half_width + 1, dtype=np.int64)
        output = np.empty(num_out, dtype=np.float32)

        for start in range(0, num_out, block_size):
            stop = min(start + block_size, num_out)
            k = np.arange(start, stop, dtype=np.float64)
            t = k / ratio
            center = np.floor(t).astype(np.int64)

            indices = center[:, None] + offsets[None, :]
            arg = t[:, None] - indices
            kernel = np.sinc(arg) * np.sinc(arg / float(half_width))

            valid = (indices >= 0) & (indices < len(x))
            clipped = np.clip(indices, 0, len(x) - 1)
            values = np.where(valid, x[clipped], 0.0)

            # Normalizar el kernel válido para conservar la amplitud en los bordes.
            kernel_valid = np.where(valid, kernel, 0.0)
            norm = np.sum(kernel_valid, axis=1)
            norm = np.where(np.abs(norm) < 1e-12, 1.0, norm)
            output[start:stop] = np.sum(values * kernel, axis=1) / norm

        return output

    def _smooth_with_butterworth(self, samples: np.ndarray) -> np.ndarray:
        """Aplica el filtro paso-bajo de reconstrucción (Butterworth orden 4)."""
        y = np.asarray(samples, dtype=np.float64)
        if len(y) == 0:
            return y.astype(np.float32)

        b, a = signal_proc.butter(4, self.cutoff_ratio, btype='low')
        padlen = 3 * max(len(a), len(b))
        if len(y) > padlen:
            return signal_proc.filtfilt(b, a, y).astype(np.float32)
        return signal_proc.lfilter(b, a, y).astype(np.float32)

    def reconstruct_from_quantized(self, stream: DigitalStream,
                                   target_rate: Optional[int] = None) -> AudioSignal:
        """
        Reconstruye la señal de audio a partir del flujo digital cuantizado.
        """
        raw_samples = np.asarray(stream.reconstructed_levels, dtype=np.float32)
        fs = int(stream.sample_rate)
        out_rate = int(target_rate) if target_rate is not None else fs

        if self.method == "sinc":
            smoothed = self._sinc_interpolate(raw_samples, fs, out_rate)
        elif self.method == "zoh":
            smoothed = self._zoh_interpolate(raw_samples, fs, out_rate)
        else:
            held = self._zoh_interpolate(raw_samples, fs, out_rate)
            smoothed = self._smooth_with_butterworth(held)

        peak = float(np.max(np.abs(smoothed))) if len(smoothed) else 0.0
        peak = peak or 1.0
        norm_samples = (smoothed / peak * 0.95).astype(np.float32)

        return AudioSignal(
            samples=norm_samples,
            sample_rate=out_rate,
            bit_depth=16,
            metadata={
                "reconstruction_method": self.method,
                "bits": stream.bits_per_sample,
                "source_rate": fs,
            }
        )

    def reconstruct_from_demodulated(self, result: DemodulatedResult,
                                     target_rate: Optional[int] = None,
                                     **kwargs) -> AudioSignal:
        """Reconstruye la señal de audio recuperada por el demodulador (Fase 3)."""
        recovered = result.recovered_audio
        out_rate = int(target_rate) if target_rate is not None else int(recovered.sample_rate)
        reconstructed = self.reconstruct(
            recovered.samples,
            target_rate=out_rate,
            input_rate=int(recovered.sample_rate),
            **kwargs
        )
        reconstructed.metadata.update({
            "demodulation_type": result.demodulation_type,
            "demod_metadata": dict(result.metadata),
        })
        return reconstructed

    def reconstruct(self, samples: np.ndarray, target_rate: int, **kwargs) -> AudioSignal:
        """Reconstruye a partir de muestras directas."""
        x = np.asarray(samples, dtype=np.float32)
        input_rate = int(kwargs.get("input_rate", kwargs.get("source_rate", target_rate)))

        if self.method == "sinc":
            y = self._sinc_interpolate(
                x, input_rate, target_rate,
                half_width=kwargs.get("half_width"),
                block_size=kwargs.get("block_size"),
            )
        elif self.method in ("zoh", "zoh_filtered"):
            y = self._zoh_interpolate(x, input_rate, target_rate)
            if self.method == "zoh_filtered":
                y = self._smooth_with_butterworth(y)
        elif input_rate != int(target_rate) and len(x) > 0:
            # Remuestreo racional genérico como respaldo para otros métodos.
            from math import gcd
            g = gcd(int(input_rate), int(target_rate))
            y = signal_proc.resample_poly(
                x, int(target_rate) // g, int(input_rate) // g
            ).astype(np.float32)
        else:
            y = x

        return AudioSignal(
            samples=np.asarray(y, dtype=np.float32),
            sample_rate=int(target_rate),
            bit_depth=16,
            metadata={"reconstruction_method": self.method, "source_rate": input_rate}
        )

    def export_reconstructed_wav(self, signal: AudioSignal,
                                 filepath: Optional[str] = None,
                                 play: bool = False,
                                 bit_depth: int = 16) -> str:
        """
        Exporta la señal reconstruida a audio_data/audio_reconstruido.wav
        y opcionalmente la reproduce para verificación auditiva.
        """
        if filepath is None:
            filepath = os.path.join("audio_data", "audio_reconstruido.wav")
        saved_path = save_wav(filepath, signal, bit_depth=bit_depth)
        if play:
            play_audio(saved_path)
        return saved_path

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

        if min_len == 0:
            return PerformanceMetrics(
                mse=0.0,
                snr_db=99.9,
                psnr_db=99.9,
                pearson_corr=0.0,
                spectral_distortion_db=0.0
            )

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

        # 4. Distorsión espectral logarítmica (RMS de la diferencia de magnitudes en dB)
        if min_len > 1:
            window = np.hanning(min_len)
            spec_x = np.abs(np.fft.rfft(x * window))
            spec_y = np.abs(np.fft.rfft(y * window))
            peak_x = float(np.max(spec_x))
            peak_y = float(np.max(spec_y))
            floor_x = peak_x * 1e-6 if peak_x > 1e-12 else 1e-12
            floor_y = peak_y * 1e-6 if peak_y > 1e-12 else 1e-12
            mag_x = np.maximum(spec_x, floor_x) / max(peak_x, 1e-12)
            mag_y = np.maximum(spec_y, floor_y) / max(peak_y, 1e-12)
            log_x = 20.0 * np.log10(np.maximum(mag_x, 1e-12))
            log_y = 20.0 * np.log10(np.maximum(mag_y, 1e-12))
            spectral_distortion_db = float(np.sqrt(np.mean((log_x - log_y) ** 2)))
        else:
            spectral_distortion_db = 0.0

        return PerformanceMetrics(
            mse=mse,
            snr_db=snr_db,
            psnr_db=psnr_db,
            pearson_corr=corr,
            spectral_distortion_db=spectral_distortion_db
        )


def plot_fidelity_comparison(original: AudioSignal, reconstructed: AudioSignal,
                             metrics: PerformanceMetrics, save_path: Optional[str] = None,
                             show: bool = False) -> plt.Figure:
    """
    Gráfica comparativa de alta fidelidad entre la señal original y la reconstruida.
    Muestra:
      1. Superposición en el dominio del tiempo con el residuo de error.
      2. Superposición de los espectros de magnitud en frecuencia.
      3. Histograma de residuos del error e[n] = x[n] - x_rec[n].
    """
    min_len = min(len(original.samples), len(reconstructed.samples))
    t = original.time_vector[:min_len]
    x = original.samples[:min_len]
    y = reconstructed.samples[:min_len]
    err = x - y

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 11), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax1, ax2, ax3):
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

    # Panel 3: Histograma de residuos del error
    error_mean = float(np.mean(err)) if len(err) else 0.0
    error_std = float(np.std(err)) if len(err) else 0.0
    error_rms = float(np.sqrt(np.mean(err ** 2))) if len(err) else 0.0
    ax3.hist(err, bins=60, color='#d2a8ff', alpha=0.85, edgecolor='#30363d')
    ax3.axvline(error_mean, color='#f85149', linewidth=1.4,
                label=f'Media = {error_mean:.2e}')
    ax3.axvline(error_mean + error_std, color='#e3b341', linewidth=1.0,
                linestyle='--', label=f'Media ± σ (σ = {error_std:.2e})')
    ax3.axvline(error_mean - error_std, color='#e3b341', linewidth=1.0, linestyle='--')
    ax3.set_title(
        f"Histograma de Residuos del Error | RMS = {error_rms:.3e} | "
        f"Distorsión Espectral = {metrics.spectral_distortion_db:.2f} dB",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax3.set_xlabel("Residuo e[n] = x[n] - x_rec[n]", color='#c9d1d9')
    ax3.set_ylabel("Número de muestras", color='#c9d1d9')
    ax3.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right')

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    if show:
        plt.show()

    return fig
