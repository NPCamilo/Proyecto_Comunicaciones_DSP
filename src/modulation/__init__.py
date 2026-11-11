"""
Módulo de Modulación (Fase 2)
"""
from .analog_digital_stubs import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator,
    plot_modulated_signal,
    plot_modulation_spectrum_translation,
    play_modulated_audio
)

__all__ = [
    "AMModulator",
    "FMModulator",
    "DigitalShiftKeyingModulator",
    "plot_modulated_signal",
    "plot_modulation_spectrum_translation",
    "play_modulated_audio"
]
