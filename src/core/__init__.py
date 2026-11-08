"""
Módulos Núcleo de DSP: Tipos base, Entrada/Salida, Análisis y Cuantización
"""

from .base import (
    AudioSignal,
    DigitalStream,
    ModulatedSignal,
    DemodulatedResult,
    PerformanceMetrics,
    BaseModulator,
    BaseDemodulator,
    BaseReconstructor
)
from .audio_io import (
    load_wav,
    save_wav,
    play_audio,
    record_voice_wav,
    generate_synthetic_speech_phrase
)
from .analyzer import (
    analyze_signal_properties,
    compute_spectrum,
    estimate_max_frequency,
    plot_time_and_frequency
)
from .quantization import (
    simulate_sampling_nqs,
    quantize_signal,
    save_digital_stream,
    load_digital_stream,
    plot_sampling_nqs_study,
    plot_quantization_analysis
)

__all__ = [
    "AudioSignal",
    "DigitalStream",
    "ModulatedSignal",
    "DemodulatedResult",
    "PerformanceMetrics",
    "BaseModulator",
    "BaseDemodulator",
    "BaseReconstructor",
    "load_wav",
    "save_wav",
    "play_audio",
    "record_voice_wav",
    "generate_synthetic_speech_phrase",
    "analyze_signal_properties",
    "compute_spectrum",
    "estimate_max_frequency",
    "plot_time_and_frequency",
    "simulate_sampling_nqs",
    "quantize_signal",
    "save_digital_stream",
    "load_digital_stream",
    "plot_sampling_nqs_study",
    "plot_quantization_analysis",
]
