"""
Módulo de Modulación - Stubs y Guía de Implementación para Colaborador 1 (Fase 2)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

ESTE MÓDULO CORRESPONDE AL PUNTO 4 DEL PROYECTO:
"4. Modulación:
    - Aplicar una técnica de modulación (AM, FM, ASK, FSK, PSK, QAM, GFSK, MFSK).
    - Mostrar la señal modulada gráficamente.
    - Permitir escuchar el resultado de la señal modulada."
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from ..core.base import AudioSignal, DigitalStream, ModulatedSignal, BaseModulator


class AMModulator(BaseModulator):
    """
    Modulador de Amplitud Analógica (AM Convencional / DSB-FC o DSB-SC).
    Ecuación DSB-FC: s(t) = [A_c + m(t)] * cos(2*pi*f_c*t)
    Donde:
      - m(t) es la señal de audio banda base normalizada
      - A_c es la amplitud de portadora (índice de modulación mu = max|m(t)| / A_c)
      - f_c es la frecuencia portadora (e.g., 2000 Hz a 5000 Hz para audio audible)
    """

    def __init__(self, carrier_freq: float = 3000.0, mod_index: float = 0.8):
        self.carrier_freq = carrier_freq
        self.mod_index = mod_index

    def modulate(self, audio: AudioSignal, **kwargs) -> ModulatedSignal:
        """
        Genera la señal modulada en AM.
        Nota: Para evitar aliasing en la simulación numérica, la tasa de muestreo
        de la señal de audio (e.g. 16 kHz) debe ser suficientemente mayor a 2*f_c.
        """
        fs = audio.sample_rate
        if fs < 4 * self.carrier_freq:
            # Sugerencia: re-muestrear si fs es bajo
            pass
        
        t = audio.time_vector
        m = audio.samples
        ac = 1.0 / self.mod_index
        carrier = np.cos(2 * np.pi * self.carrier_freq * t)
        
        # Modulación AM convencional:
        s_am = (ac + m) * carrier
        # Normalizar para reproducción segura
        s_am_norm = s_am / np.max(np.abs(s_am))

        return ModulatedSignal(
            samples=s_am_norm.astype(np.float32),
            carrier_freq=self.carrier_freq,
            sampling_rate=fs,
            modulation_type="AM-DSB-FC",
            is_digital=False,
            metadata={"mod_index": self.mod_index, "carrier_freq": self.carrier_freq}
        )


class DigitalShiftKeyingModulator(BaseModulator):
    """
    Modulador Digital por Desplazamiento (ASK / FSK / BPSK).
    Opera directamente sobre el DigitalStream generado en la Fase 1.
    
    Implementación sugerida para Colaborador 1:
      - ASK: s(t) = A_k * cos(2*pi*fc*t), donde A_k in {0, 1} o {A_min, A_max}
      - FSK: s(t) = cos(2*pi*f_k*t), donde f_k = f1 si bit=0, f_k = f2 si bit=1
      - BPSK: s(t) = cos(2*pi*fc*t + pi * bit)
    """

    def __init__(self, mod_type: str = "ASK", carrier_freq: float = 2000.0,
                 samples_per_symbol: int = 16):
        self.mod_type = mod_type.upper()
        self.carrier_freq = carrier_freq
        self.samples_per_symbol = samples_per_symbol

    def modulate(self, stream: DigitalStream, **kwargs) -> ModulatedSignal:
        """
        Mapea el flujo binario (0s y 1s) a símbolos pasabanda.
        """
        bits = stream.bitstream
        # TODO Colaborador 1: Implementar modulación de símbolos bit a bit
        # Ejemplo: FSK o ASK
        pass


def plot_modulated_signal(modulated: ModulatedSignal, zoom_ms: float = 10.0,
                          save_path: Optional[str] = None, show: bool = False) -> plt.Figure:
    """
    Grafica la señal modulada en tiempo (con zoom para ver oscilaciones de portadora)
    y en frecuencia (mostrando los lóbulos laterales de modulación).
    """
    fs = modulated.sampling_rate
    samples = modulated.samples
    t = modulated.time_vector
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')
    
    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, color='#30363d', linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    # Zoom temporal
    num_zoom = min(int(zoom_ms * 1e-3 * fs), len(samples))
    ax1.plot(t[:num_zoom] * 1000.0, samples[:num_zoom], color='#79c0ff', linewidth=1.1)
    ax1.set_title(f"Señal Modulada {modulated.modulation_type} - Zoom Temporal ({zoom_ms} ms)",
                  color='#f0f6fc', fontsize=11, fontweight='bold')
    ax1.set_xlabel("Tiempo [ms]", color='#c9d1d9')
    ax1.set_ylabel("Amplitud", color='#c9d1d9')

    # Espectro
    fft_vals = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
    freqs = np.fft.rfftfreq(len(samples), d=1.0 / fs)
    fft_db = 20 * np.log10(np.clip(fft_vals / (np.max(fft_vals) + 1e-12), 1e-6, 1.0))
    ax2.plot(freqs, fft_db, color='#d2a8ff', linewidth=1.0)
    ax2.axvline(modulated.carrier_freq, color='#f85149', linestyle='--',
                label=f'Portadora fc = {modulated.carrier_freq:.1f} Hz')
    ax2.set_title(f"Densidad Espectral de la Señal Modulada {modulated.modulation_type}",
                  color='#f0f6fc', fontsize=11, fontweight='bold')
    ax2.set_xlabel("Frecuencia [Hz]", color='#c9d1d9')
    ax2.set_ylabel("Magnitud [dBFS]", color='#c9d1d9')
    ax2.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc')

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    if show:
        plt.show()

    return fig
