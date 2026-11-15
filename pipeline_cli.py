"""
Orquestador Integral de la Cadena DSP - FASE 5
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación,
Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

Este módulo expone controladores puros y reutilizables, sin salidas de consola,
listos para ser consumidos por una futura interfaz gráfica. Toda la interacción
con la consola (argparse, progreso, resumen y exportación de gráficas) está
aislada dentro de main() y del bloque if __name__ == "__main__".

Modo directo por defecto:
    Audio -> Muestreo NQS -> Cuantización PCM -> Reconstrucción DAC -> Métricas

Modo con modulación/demodulación (opcional):
    .. -> Modulación -> Demodulación -> Reconstrucción DAC -> Métricas

USO:
    python pipeline_cli.py
    python pipeline_cli.py --wav ruta.wav --fs 8000 --bits 8 --method sinc
    python pipeline_cli.py --fs 8000 --bits 4 --method zoh --plot
"""

import argparse
import inspect
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal_proc

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.base import (
    AudioSignal,
    BaseDemodulator,
    BaseModulator,
    DemodulatedResult,
    DigitalStream,
    ModulatedSignal,
    PerformanceMetrics,
)
from src.core.audio_io import generate_synthetic_speech_phrase, load_wav, save_wav
from src.core.analyzer import analyze_signal_properties
from src.core.quantization import (
    quantize_signal,
    save_digital_stream,
    simulate_sampling_nqs,
)
from src.reconstruction.metrics_stubs import AudioReconstructor, plot_fidelity_comparison

ProgressCallback = Callable[[str, Dict[str, Any]], None]


@dataclass
class AudioLoadResult:
    """Resultado de la adquisición o síntesis de la señal de audio."""

    signal: AudioSignal
    source: str
    generated: bool
    saved_path: Optional[str] = None


@dataclass
class NQSResult:
    """Resultado del muestreo NQS, la cuantización PCM y la serialización digital."""

    source_signal: AudioSignal
    sampled_signal: AudioSignal
    stream: DigitalStream
    sampling_frequency: int
    original_frequency: int
    downsample_factor: int
    properties: Dict[str, Any] = field(default_factory=dict)
    binary_path: Optional[str] = None
    metadata_path: Optional[str] = None


@dataclass
class ModulationResult:
    """Resultado de la etapa opcional de modulación y demodulación."""

    applied: bool
    modulated_signal: Optional[ModulatedSignal] = None
    demodulated_result: Optional[DemodulatedResult] = None
    carrier_freq: Optional[float] = None
    modulation_type: Optional[str] = None
    demodulation_type: Optional[str] = None


@dataclass
class ReconstructionResult:
    """Resultado de la reconstrucción DAC y la evaluación de fidelidad."""

    reconstructed_signal: AudioSignal
    metrics: PerformanceMetrics
    method: str
    used_demodulation: bool
    output_path: Optional[str] = None


@dataclass
class PipelineResult:
    """Contenedor integral del pipeline DSP listo para una GUI."""

    audio: AudioLoadResult
    nqs: NQSResult
    modulation: ModulationResult
    reconstruction: ReconstructionResult
    artifacts: Dict[str, Optional[str]] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


def _emit_progress(callback: Optional[ProgressCallback], stage: str,
                   payload: Dict[str, Any]) -> None:
    if callback is not None:
        callback(stage, payload)


def _sample_signal_to_rate(signal: AudioSignal,
                           sampling_frequency: int) -> Tuple[AudioSignal, int]:
    target_rate = int(sampling_frequency)
    source_rate = int(signal.sample_rate)

    if target_rate <= 0:
        raise ValueError("La frecuencia de muestreo NQS debe ser positiva.")
    if target_rate == source_rate:
        return signal, 1

    if target_rate < source_rate and source_rate % target_rate == 0:
        factor = source_rate // target_rate
        _, samples, effective_rate = simulate_sampling_nqs(
            signal, downsample_factor=factor
        )
        sampled = AudioSignal(
            samples=samples,
            sample_rate=effective_rate,
            bit_depth=signal.bit_depth,
            filename=signal.filename,
            metadata=dict(signal.metadata),
        )
        sampled.metadata.update({
            "nqs_sampling": "decimation",
            "downsample_factor": factor,
        })
        return sampled, factor

    divisor = math.gcd(source_rate, target_rate)
    up = target_rate // divisor
    down = source_rate // divisor
    samples = signal_proc.resample_poly(
        signal.samples, up, down
    ).astype(np.float32)

    sampled = AudioSignal(
        samples=samples,
        sample_rate=target_rate,
        bit_depth=signal.bit_depth,
        filename=signal.filename,
        metadata=dict(signal.metadata),
    )
    sampled.metadata.update({
        "nqs_sampling": "resample_poly",
        "resample_up": up,
        "resample_down": down,
    })
    return sampled, 1


def load_or_generate_audio(wav_path: Optional[str] = None, duration: float = 3.0,
                           sample_rate: int = 16000, output_dir: str = "audio_data",
                           save_generated: bool = True,
                           seed: Optional[int] = None,
                           progress_callback: Optional[ProgressCallback] = None
                           ) -> AudioLoadResult:
    """
    Carga un archivo WAV o genera una frase de voz sintética de prueba.

    No imprime en consola. Retorna un AudioLoadResult con la señal lista para
    el resto de la cadena DSP.
    """
    if sample_rate <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")
    if duration <= 0:
        raise ValueError("La duración debe ser positiva.")

    if wav_path is not None:
        if not os.path.exists(wav_path):
            raise FileNotFoundError(
                f"No se encontró el archivo de audio: {wav_path}"
            )
        signal = load_wav(wav_path)
        result = AudioLoadResult(
            signal=signal,
            source="wav",
            generated=False,
        )
    else:
        random_state = np.random.get_state()
        if seed is not None:
            np.random.seed(seed)
        try:
            samples = generate_synthetic_speech_phrase(
                duration=duration, sample_rate=sample_rate
            )
        finally:
            if seed is not None:
                np.random.set_state(random_state)

        signal = AudioSignal(
            samples=samples,
            sample_rate=int(sample_rate),
            bit_depth=16,
            duration=float(duration),
        )

        saved_path = None
        if save_generated:
            os.makedirs(output_dir, exist_ok=True)
            saved_path = save_wav(
                os.path.join(output_dir, "pipeline_voz_generada.wav"),
                signal,
                bit_depth=16,
            )
            signal.filename = saved_path

        result = AudioLoadResult(
            signal=signal,
            source="synthetic",
            generated=True,
            saved_path=saved_path,
        )

    _emit_progress(progress_callback, "audio_loaded", {
        "source": result.source,
        "generated": result.generated,
        "sample_rate": result.signal.sample_rate,
        "num_samples": result.signal.num_samples,
        "duration": result.signal.duration,
    })
    return result


def process_nqs_pcm(signal: AudioSignal, sampling_frequency: int = 8000,
                    bits_per_sample: int = 8, output_dir: str = "audio_data",
                    save_artifacts: bool = True,
                    bitstream_base_name: Optional[str] = None,
                    progress_callback: Optional[ProgressCallback] = None
                    ) -> NQSResult:
    """
    Realiza el muestreo NQS a la frecuencia objetivo y la cuantización PCM.

    No imprime en consola. Retorna un NQSResult con la señal muestreada, el
    DigitalStream, las propiedades espectrales y las rutas de los artefactos.
    """
    if not isinstance(signal, AudioSignal):
        raise TypeError("signal debe ser una instancia de AudioSignal.")
    if sampling_frequency <= 0:
        raise ValueError("La frecuencia de muestreo NQS debe ser positiva.")

    bits = int(bits_per_sample)
    if bits < 1 or bits > 16:
        raise ValueError(
            f"Resolución de {bits} bits no válida. Debe ser entre 1 y 16."
        )

    source_properties = analyze_signal_properties(signal)
    sampled_signal, downsample_factor = _sample_signal_to_rate(
        signal, sampling_frequency
    )
    sampled_properties = analyze_signal_properties(sampled_signal)

    stream = quantize_signal(sampled_signal, bits_per_sample=bits)

    binary_path = None
    metadata_path = None
    if save_artifacts:
        os.makedirs(output_dir, exist_ok=True)
        base_name = bitstream_base_name or os.path.join(
            output_dir, f"pipeline_trama_digital_{bits}bits"
        )
        binary_path, metadata_path = save_digital_stream(stream, base_name)

    properties: Dict[str, Any] = dict(sampled_properties)
    properties.update({
        "source_properties": source_properties,
        "downsample_factor": downsample_factor,
        "sampling_frequency_hz": sampled_signal.sample_rate,
        "bits_per_sample": stream.bits_per_sample,
        "sqnr_empirical_db": stream.sqnr_db,
        "sqnr_theoretical_db": stream.sqnr_theoretical_db,
    })

    result = NQSResult(
        source_signal=signal,
        sampled_signal=sampled_signal,
        stream=stream,
        sampling_frequency=sampled_signal.sample_rate,
        original_frequency=signal.sample_rate,
        downsample_factor=downsample_factor,
        properties=properties,
        binary_path=binary_path,
        metadata_path=metadata_path,
    )

    _emit_progress(progress_callback, "nqs_quantized", {
        "sampling_frequency": result.sampling_frequency,
        "original_frequency": result.original_frequency,
        "bits": stream.bits_per_sample,
        "num_samples": len(stream.quantized_levels),
        "total_bits": stream.total_bits,
        "sqnr_db": stream.sqnr_db,
        "binary_path": binary_path,
        "metadata_path": metadata_path,
    })
    return result


def _invoke_modulator(modulator: BaseModulator, input_data: Any,
                      carrier_freq: float, kwargs: Dict[str, Any]
                      ) -> ModulatedSignal:
    signature = inspect.signature(modulator.modulate)
    parameters = signature.parameters
    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    if "carrier_freq" in parameters or accepts_kwargs:
        return modulator.modulate(
            input_data, carrier_freq=carrier_freq, **kwargs
        )
    return modulator.modulate(input_data, **kwargs)


def modulate_and_demodulate(input_data: Any,
                            modulator: Optional[BaseModulator] = None,
                            demodulator: Optional[BaseDemodulator] = None,
                            carrier_freq: float = 3000.0,
                            progress_callback: Optional[ProgressCallback] = None,
                            **kwargs) -> ModulationResult:
    """
    Aplica la etapa opcional de modulación y demodulación.

    Si no se inyectan ambos componentes, retorna applied=False para permitir el
    modo directo (bypass). No imprime en consola.
    """
    if modulator is None and demodulator is None:
        return ModulationResult(applied=False)

    if modulator is None or demodulator is None:
        raise ValueError(
            "Debe inyectar simultáneamente un BaseModulator y un BaseDemodulator."
        )

    modulated = _invoke_modulator(
        modulator, input_data, float(carrier_freq), kwargs
    )
    if not isinstance(modulated, ModulatedSignal):
        raise TypeError("El modulador debe retornar una instancia de ModulatedSignal.")

    demodulated = demodulator.demodulate(modulated, **kwargs)
    if not isinstance(demodulated, DemodulatedResult):
        raise TypeError(
            "El demodulador debe retornar una instancia de DemodulatedResult."
        )

    result = ModulationResult(
        applied=True,
        modulated_signal=modulated,
        demodulated_result=demodulated,
        carrier_freq=float(carrier_freq),
        modulation_type=modulated.modulation_type,
        demodulation_type=demodulated.demodulation_type,
    )

    _emit_progress(progress_callback, "modulated", {
        "modulation_type": result.modulation_type,
        "demodulation_type": result.demodulation_type,
        "carrier_freq": result.carrier_freq,
    })
    return result


def reconstruct_and_evaluate(original_signal: AudioSignal,
                             stream: Optional[DigitalStream] = None,
                             demodulated: Optional[DemodulatedResult] = None,
                             method: str = "sinc",
                             target_rate: Optional[int] = None,
                             output_path: Optional[str] = None,
                             save_output: bool = True,
                             reconstructor: Optional[AudioReconstructor] = None,
                             progress_callback: Optional[ProgressCallback] = None
                             ) -> ReconstructionResult:
    """
    Reconstruye la señal desde el flujo cuantizado o desde el resultado
    demodulado, exporta el WAV y calcula las métricas de fidelidad.

    Si demodulated es None se usa reconstruct_from_quantized, implementando el
    modo directo de la cadena. No imprime en consola.
    """
    if not isinstance(original_signal, AudioSignal):
        raise TypeError("original_signal debe ser una instancia de AudioSignal.")
    if stream is None and demodulated is None:
        raise ValueError(
            "Debe proporcionar un DigitalStream o un DemodulatedResult."
        )
    if method not in ("sinc", "zoh", "zoh_filtered"):
        raise ValueError(
            "Método de reconstrucción no válido. Use 'sinc' o 'zoh'."
        )

    active_reconstructor = reconstructor or AudioReconstructor(method=method)
    output_rate = (
        int(target_rate) if target_rate is not None
        else int(original_signal.sample_rate)
    )
    if output_rate <= 0:
        raise ValueError("La frecuencia de reconstrucción debe ser positiva.")

    used_demodulation = demodulated is not None
    if used_demodulation:
        reconstructed = active_reconstructor.reconstruct_from_demodulated(
            demodulated, target_rate=output_rate
        )
    else:
        reconstructed = active_reconstructor.reconstruct_from_quantized(
            stream, target_rate=output_rate
        )

    metrics = active_reconstructor.evaluate_fidelity(
        original_signal, reconstructed
    )

    saved_path = None
    if save_output:
        destination = output_path or os.path.join(
            "audio_data", "pipeline_audio_reconstruido.wav"
        )
        saved_path = active_reconstructor.export_reconstructed_wav(
            reconstructed, filepath=destination, play=False
        )

    result = ReconstructionResult(
        reconstructed_signal=reconstructed,
        metrics=metrics,
        method=active_reconstructor.method,
        used_demodulation=used_demodulation,
        output_path=saved_path,
    )

    _emit_progress(progress_callback, "reconstructed", {
        "method": result.method,
        "used_demodulation": used_demodulation,
        "target_rate": output_rate,
        "num_samples": reconstructed.num_samples,
        "output_path": saved_path,
        "mse": metrics.mse,
        "snr_db": metrics.snr_db,
        "psnr_db": metrics.psnr_db,
        "pearson_corr": metrics.pearson_corr,
        "spectral_distortion_db": metrics.spectral_distortion_db,
    })
    return result


def run_dsp_pipeline(wav_path: Optional[str] = None,
                     sampling_frequency: int = 8000,
                     bits_per_sample: int = 8,
                     method: str = "sinc",
                     output_path: Optional[str] = None,
                     duration: float = 3.0,
                     source_sample_rate: int = 16000,
                     output_dir: str = "audio_data",
                     target_rate: Optional[int] = None,
                     modulator: Optional[BaseModulator] = None,
                     demodulator: Optional[BaseDemodulator] = None,
                     carrier_freq: float = 3000.0,
                     modulation_input: str = "audio",
                     save_artifacts: bool = True,
                     reconstructor: Optional[AudioReconstructor] = None,
                     seed: Optional[int] = None,
                     progress_callback: Optional[ProgressCallback] = None
                     ) -> PipelineResult:
    """
    Orquesta la cadena DSP completa de extremo a extremo.

    Entrada -> Muestreo NQS + PCM -> [Modulación/Demodulación opcional] ->
    Reconstrucción DAC -> Métricas de fidelidad. No imprime en consola.
    """
    if modulation_input not in ("audio", "sampled_audio", "digital"):
        raise ValueError(
            "modulation_input debe ser 'audio', 'sampled_audio' o 'digital'."
        )

    config = {
        "wav_path": wav_path,
        "sampling_frequency": int(sampling_frequency),
        "bits_per_sample": int(bits_per_sample),
        "method": method,
        "output_path": output_path,
        "duration": float(duration),
        "source_sample_rate": int(source_sample_rate),
        "output_dir": output_dir,
        "target_rate": target_rate,
        "carrier_freq": float(carrier_freq),
        "modulation_input": modulation_input,
        "save_artifacts": bool(save_artifacts),
    }
    _emit_progress(progress_callback, "start", {"config": config})

    audio_result = load_or_generate_audio(
        wav_path=wav_path,
        duration=duration,
        sample_rate=source_sample_rate,
        output_dir=output_dir,
        save_generated=save_artifacts,
        seed=seed,
        progress_callback=progress_callback,
    )

    nqs_result = process_nqs_pcm(
        audio_result.signal,
        sampling_frequency=sampling_frequency,
        bits_per_sample=bits_per_sample,
        output_dir=output_dir,
        save_artifacts=save_artifacts,
        progress_callback=progress_callback,
    )

    if modulator is None and demodulator is None:
        modulation_result = ModulationResult(applied=False)
        _emit_progress(progress_callback, "modulation_skipped", {})
    else:
        if modulation_input == "digital":
            stage_input: Any = nqs_result.stream
        elif modulation_input == "sampled_audio":
            stage_input = nqs_result.sampled_signal
        else:
            stage_input = audio_result.signal

        modulation_result = modulate_and_demodulate(
            stage_input,
            modulator=modulator,
            demodulator=demodulator,
            carrier_freq=carrier_freq,
            progress_callback=progress_callback,
        )

    demodulated = (
        modulation_result.demodulated_result
        if modulation_result.applied else None
    )

    reconstruction_result = reconstruct_and_evaluate(
        original_signal=audio_result.signal,
        stream=nqs_result.stream,
        demodulated=demodulated,
        method=method,
        target_rate=target_rate,
        output_path=output_path,
        save_output=save_artifacts,
        reconstructor=reconstructor,
        progress_callback=progress_callback,
    )

    artifacts = {
        "original_wav": audio_result.signal.filename,
        "synthetic_wav": audio_result.saved_path,
        "digital_bitstream": nqs_result.binary_path,
        "digital_metadata": nqs_result.metadata_path,
        "reconstructed_wav": reconstruction_result.output_path,
    }

    result = PipelineResult(
        audio=audio_result,
        nqs=nqs_result,
        modulation=modulation_result,
        reconstruction=reconstruction_result,
        artifacts=artifacts,
        config=config,
    )

    _emit_progress(progress_callback, "completed", {
        "artifacts": artifacts,
        "modulation_applied": modulation_result.applied,
    })
    return result


def main(argv: Optional[list] = None) -> int:
    """Punto de entrada CLI. Concentra todo el manejo de consola."""

    def progress(stage: str, payload: Dict[str, Any]) -> None:
        if stage == "start":
            print("=" * 78)
            print("PROYECTO COMUNICACIONES I - PIPELINE DSP INTEGRAL (FASE 5)")
            print("=" * 78)
        elif stage == "audio_loaded":
            origin = (
                "archivo WAV" if payload.get("source") == "wav"
                else "síntesis de voz"
            )
            print(
                f"[1/4] Audio listo desde {origin}: "
                f"{payload.get('sample_rate', 0):,} Hz | "
                f"{payload.get('num_samples', 0):,} muestras | "
                f"{payload.get('duration', 0.0):.3f} s"
            )
        elif stage == "nqs_quantized":
            print(
                f"[2/4] Muestreo NQS a {payload.get('sampling_frequency', 0):,} Hz "
                f"y cuantización PCM a {payload.get('bits', 0)} bits"
            )
        elif stage == "modulation_skipped":
            print("[3/4] Modulación/Demodulación omitida (modo directo bypass)")
        elif stage == "modulated":
            print(
                f"[3/4] Modulación {payload.get('modulation_type')} y "
                f"demodulación {payload.get('demodulation_type')}"
            )
        elif stage == "reconstructed":
            print(
                f"[4/4] Reconstrucción DAC {payload.get('method')} completada"
            )

    parser = argparse.ArgumentParser(
        description=(
            "Pipeline DSP completo: adquisición, NQS, PCM, "
            "reconstrucción DAC y métricas de fidelidad."
        )
    )
    parser.add_argument(
        "--wav", type=str, default=None,
        help="Ruta a un archivo WAV de entrada. Si se omite, genera voz sintética."
    )
    parser.add_argument(
        "--fs", dest="sampling_frequency", type=int, default=8000,
        help="Frecuencia de muestreo NQS en Hz (default: 8000)."
    )
    parser.add_argument(
        "--bits", dest="bits_per_sample", type=int, default=8,
        choices=(4, 8, 16),
        help="Resolución PCM en bits: 4, 8 o 16 (default: 8)."
    )
    parser.add_argument(
        "--method", type=str, default="sinc", choices=("sinc", "zoh"),
        help="Método de reconstrucción DAC: sinc o zoh (default: sinc)."
    )
    parser.add_argument(
        "--output", dest="output_path", type=str, default=None,
        help="Ruta del WAV reconstruido de salida."
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Muestra las gráficas comparativas de fidelidad."
    )
    parser.add_argument(
        "--outdir", type=str, default="audio_data",
        help="Directorio de artefactos (default: audio_data)."
    )
    parser.add_argument(
        "--duration", type=float, default=3.0,
        help="Duración de la señal sintética en segundos (default: 3.0)."
    )
    parser.add_argument(
        "--source-rate", dest="source_sample_rate", type=int, default=16000,
        help="Frecuencia de la señal de entrada o sintética (default: 16000)."
    )
    parser.add_argument(
        "--target-rate", dest="target_rate", type=int, default=None,
        help="Frecuencia de salida de la reconstrucción DAC."
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="No exporta WAV, bitstream ni gráficas a disco."
    )

    args = parser.parse_args(argv)

    output_path = args.output_path or os.path.join(
        args.outdir, "pipeline_audio_reconstruido.wav"
    )
    save_artifacts = not args.no_save

    try:
        result = run_dsp_pipeline(
            wav_path=args.wav,
            sampling_frequency=args.sampling_frequency,
            bits_per_sample=args.bits_per_sample,
            method=args.method,
            output_path=output_path,
            duration=args.duration,
            source_sample_rate=args.source_sample_rate,
            output_dir=args.outdir,
            target_rate=args.target_rate,
            save_artifacts=save_artifacts,
            progress_callback=progress,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    original = result.audio.signal
    reconstructed = result.reconstruction.reconstructed_signal
    metrics = result.reconstruction.metrics
    stream = result.nqs.stream

    plot_path = None
    if save_artifacts:
        os.makedirs(args.outdir, exist_ok=True)
        plot_path = os.path.abspath(
            os.path.join(args.outdir, "pipeline_comparacion_fidelidad.png")
        )

    figure = plot_fidelity_comparison(
        original,
        reconstructed,
        metrics,
        save_path=plot_path,
        show=args.plot,
    )
    if not args.plot:
        plt.close(figure)

    print("\n" + "-" * 78)
    print(f"{'ETAPA / MÉTRICA':<40}{'VALOR':>36}")
    print("-" * 78)
    print(f"{'Frecuencia original (Hz)':<40}{original.sample_rate:>36,}")
    print(f"{'Frecuencia de muestreo NQS (Hz)':<40}{result.nqs.sampling_frequency:>36,}")
    print(f"{'Resolución PCM (bits)':<40}{stream.bits_per_sample:>36}")
    print(f"{'Muestras digitalizadas':<40}{len(stream.quantized_levels):>36,}")
    sqnr_value = f"{stream.sqnr_db:.2f} / {stream.sqnr_theoretical_db:.2f}"
    print(f"{'SQNR experimental / teórico (dB)':<40}{sqnr_value:>36}")
    print(f"{'Método de reconstrucción DAC':<40}{result.reconstruction.method:>36}")
    modulation_value = (
        f"{result.modulation.modulation_type} / "
        f"{result.modulation.demodulation_type}"
        if result.modulation.applied else "bypass (modo directo)"
    )
    print(f"{'Modulación / Demodulación':<40}{modulation_value:>36}")
    print("-" * 78)
    print(f"{'MSE':<40}{metrics.mse:>36.10f}")
    print(f"{'SNR (dB)':<40}{metrics.snr_db:>36.3f}")
    print(f"{'PSNR (dB)':<40}{metrics.psnr_db:>36.3f}")
    print(f"{'Correlación de Pearson':<40}{metrics.pearson_corr:>36.6f}")
    print(f"{'Distorsión espectral (dB)':<40}{metrics.spectral_distortion_db:>36.3f}")
    print("-" * 78)
    print("ARTEFACTOS EXPORTADOS")
    print("-" * 78)

    artifact_labels = (
        ("Audio de entrada", "original_wav"),
        ("Audio sintético generado", "synthetic_wav"),
        ("Trama digital (.bin)", "digital_bitstream"),
        ("Metadatos del flujo (.json)", "digital_metadata"),
        ("Audio reconstruido (.wav)", "reconstructed_wav"),
    )
    for label, key in artifact_labels:
        value = result.artifacts.get(key)
        if value:
            print(f"  {label}: {value}")
    if plot_path:
        print(f"  Comparación de fidelidad (.png): {plot_path}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
