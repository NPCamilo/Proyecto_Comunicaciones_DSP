"""
Módulo de Demodulación - Stubs y Guía para Colaborador 2 (Fase 3)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

ESTE MÓDULO CORRESPONDE AL PUNTO 5 DEL PROYECTO:
"5. Demodulación:
    - Implementar el proceso de demodulación correspondiente.
    - Recuperar la señal original a partir de la señal modulada.
    - Mostrar la señal demodulada mediante una gráfica.
    - Reproducir la señal demodulada para verificar la recuperación de la información."
"""

import numpy as np
import scipy.signal as signal_proc
import matplotlib.pyplot as plt
from typing import Optional
from ..core.base import AudioSignal, ModulatedSignal, DemodulatedResult, BaseDemodulator


class AMDemodulator(BaseDemodulator):
    """
    Demodulador para AM (Convencional o Coherente).
    
    Técnicas recomendadas:
      1. Coherente / Síncrono:
         Multiplicar por cos(2*pi*fc*t) -> genera componente DC/banda base + término en 2*fc.
         Filtrar con un filtro Butterworth paso bajo (fc_cutoff ≈ f_audio_max).
      2. Detector de Envolvente / Transformada de Hilbert:
         env = np.abs(scipy.signal.hilbert(s_am))
         Eliminar nivel DC de portadora: audio_rec = env - np.mean(env).
    """

    def __init__(self, method: str = "coherent", cutoff_freq: float = 3500.0):
        self.method = method
        self.cutoff_freq = cutoff_freq

    def demodulate(self, modulated: ModulatedSignal, **kwargs) -> DemodulatedResult:
        fs = modulated.sampling_rate
        fc = modulated.carrier_freq
        t = modulated.time_vector
        s = modulated.samples

        if self.method == "envelope":
            # Demodulación por envolvente analítica (Hilbert)
            analytic_sig = signal_proc.hilbert(s)
            envelope = np.abs(analytic_sig)
            # Quitar componente DC de portadora
            demod_audio = envelope - np.mean(envelope)
        else:
            # Demodulación Coherente
            # Multiplicador local
            mixed = s * np.cos(2 * np.pi * fc * t) * 2.0
            
            # Filtro Butterworth paso bajo orden 5
            nyq = 0.5 * fs
            normal_cutoff = min(self.cutoff_freq / nyq, 0.95)
            b, a = signal_proc.butter(5, normal_cutoff, btype='low', analog=False)
            filtered = signal_proc.filtfilt(b, a, mixed)
            demod_audio = filtered - np.mean(filtered)

        # Normalizar amplitud
        peak = np.max(np.abs(demod_audio)) or 1.0
        demod_audio = demod_audio / peak * 0.90

        recovered = AudioSignal(
            samples=demod_audio.astype(np.float32),
            sample_rate=fs,
            bit_depth=16,
            metadata={"demod_method": self.method, "carrier_freq": fc}
        )

        return DemodulatedResult(
            recovered_audio=recovered,
            demodulation_type=f"AM-{self.method.capitalize()}",
            metadata={"cutoff_freq": self.cutoff_freq}
        )


def plot_demodulated_comparison(original: AudioSignal, demodulated: AudioSignal,
                                save_path: Optional[str] = None, show: bool = False) -> plt.Figure:
    """
    Compara gráficamente la señal demodulada con la señal original en el dominio del tiempo.
    """
    t_orig = original.time_vector
    t_demod = demodulated.time_vector
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')
    
    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, color='#30363d', linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    ax1.plot(t_orig, original.samples, color='#58a6ff', linewidth=1.0)
    ax1.set_title("Señal Original x(t)", color='#f0f6fc', fontsize=11, fontweight='bold')
    ax1.set_ylabel("Amplitud", color='#c9d1d9')

    ax2.plot(t_demod, demodulated.samples, color='#3fb950', linewidth=1.0)
    ax2.set_title(f"Señal Demodulada Recuperada ({demodulated.metadata.get('demod_method', 'Base')})",
                  color='#f0f6fc', fontsize=11, fontweight='bold')
    ax2.set_xlabel("Tiempo [segundos]", color='#c9d1d9')
    ax2.set_ylabel("Amplitud", color='#c9d1d9')

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    if show:
        plt.show()

    return fig
