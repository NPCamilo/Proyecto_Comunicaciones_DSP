"""
Módulo de Muestreo NQS, Cuantización [Byte/Bit] y Digitalización (Punto 3)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import json
import os
from typing import Dict, Any, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt

from .base import AudioSignal, DigitalStream
from .analyzer import analyze_signal_properties


def simulate_sampling_nqs(signal: AudioSignal, downsample_factor: int = 1) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Simula la obtención de muestras discretas a partir de la señal continua equivalente.
    Permite emular tasas de muestreo variables para explorar el teorema de Nyquist-Shannon.
    
    Args:
        signal (AudioSignal): Señal de entrada.
        downsample_factor (int): Factor de submuestreo M (fs_new = fs_original / M).
        
    Returns:
        Tuple[np.ndarray, np.ndarray, int]:
            - t_discrete: Vector de tiempos de muestreo [s]
            - x_discrete: Amplitudes muestreadas x[n]
            - fs_sub: Nueva frecuencia de muestreo efectiva
    """
    if downsample_factor < 1:
        downsample_factor = 1
        
    x = signal.samples
    fs = signal.sample_rate
    
    # Muestreo por diezmado directo (sin filtro antialiasing previo para poder estudiar el efecto NQS)
    indices = np.arange(0, len(x), downsample_factor)
    x_discrete = x[indices]
    fs_sub = int(fs / downsample_factor)
    t_discrete = indices / fs
    
    return t_discrete, x_discrete, fs_sub


def quantize_signal(signal: AudioSignal, bits_per_sample: int = 8,
                    v_min: float = -1.0, v_max: float = 1.0) -> DigitalStream:
    """
    Aplica cuantización uniforme lineal mid-tread/mid-rise a la señal continua/muestreada
    según la resolución en bits especificada (Técnica de resolución [Byte / Bit]).
    
    Soporta resoluciones típicas:
      - 1 bit (1 bit/muestra: 2 niveles)
      - 4 bits (Nibble: 16 niveles)
      - 8 bits (1 Byte/muestra: 256 niveles)
      - 16 bits (2 Bytes/muestra: 65,536 niveles)
      
    Args:
        signal (AudioSignal): Señal normalizada de entrada.
        bits_per_sample (int): Número de bits por muestra 'b' (1 a 16).
        v_min (float): Límite inferior de la escala de amplitud (default -1.0).
        v_max (float): Límite superior de la escala de amplitud (default +1.0).
        
    Returns:
        DigitalStream: Estructura con bitstream serializado, niveles enteros,
                      valores analógicos cuantizados y métricas SQNR.
    """
    if bits_per_sample < 1 or bits_per_sample > 16:
        raise ValueError(f"Resolución de {bits_per_sample} bits no válida. Debe ser entre 1 y 16.")

    x = np.clip(signal.samples, v_min, v_max)
    num_levels = 2 ** bits_per_sample
    step_size = (v_max - v_min) / (num_levels - 1)

    # 1. Asignación de índices enteros de cuantización: [0, 2^b - 1]
    levels = np.round((x - v_min) / step_size).astype(np.int64)
    levels = np.clip(levels, 0, num_levels - 1)

    # 2. Reconstrucción de los niveles cuantizados continuos: x_q[n]
    x_quantized = v_min + (levels * step_size).astype(np.float32)

    # 3. Cálculo del ruido de cuantización e[n] = x[n] - x_q[n]
    quant_error = x - x_quantized
    power_signal = float(np.mean(x ** 2))
    power_error = float(np.mean(quant_error ** 2))

    if power_error > 1e-12:
        sqnr_empirical = float(10 * np.log10(power_signal / power_error))
    else:
        sqnr_empirical = 99.9  # Prácticamente infinito (resolución perfecta)

    # SQNR teórica para cuantizador uniforme: 6.02*b + 1.76 dB
    sqnr_theoretical = float(6.02 * bits_per_sample + 1.76)

    # 4. Codificación en flujo de bits binarios (Bitstream)
    # Convertir cada entero a b bits (MSB a LSB)
    # Forma vectorial eficiente con numpy unpacking
    if bits_per_sample <= 8:
        uint_levels = levels.astype(np.uint8)
        raw_bytes = uint_levels.tobytes()
        unpacked_bits = np.unpackbits(np.frombuffer(raw_bytes, dtype=np.uint8))
        # Seleccionar únicamente los últimos 'bits_per_sample' bits de cada byte
        bit_matrix = unpacked_bits.reshape(len(levels), 8)[:, (8 - bits_per_sample):]
        flat_bitstream = bit_matrix.flatten()
    else:
        # Para 9 a 16 bits
        shift = np.arange(bits_per_sample - 1, -1, -1, dtype=np.int64)
        bit_matrix = ((levels[:, None] >> shift) & 1).astype(np.uint8)
        flat_bitstream = bit_matrix.flatten()

    stream = DigitalStream(
        bitstream=flat_bitstream,
        quantized_levels=levels,
        reconstructed_levels=x_quantized,
        bits_per_sample=bits_per_sample,
        sample_rate=signal.sample_rate,
        v_min=v_min,
        v_max=v_max,
        sqnr_db=sqnr_empirical,
        sqnr_theoretical_db=sqnr_theoretical
    )

    return stream


def save_digital_stream(stream: DigitalStream, base_filepath: str) -> Tuple[str, str]:
    """
    Serializa y almacena en disco el resultado de la digitalización:
      - Archivo binario (.bin): Datos empaquetados bit a bit (resolución por Byte).
      - Archivo JSON (.json): Metadatos de ingeniería (resolución, tasa, niveles, SQNR).
      
    Args:
        stream (DigitalStream): Flujo digital a guardar.
        base_filepath (str): Ruta base sin extensión o con .bin
        
    Returns:
        Tuple[str, str]: Rutas de los archivos binario y JSON generados.
    """
    root, _ = os.path.splitext(base_filepath)
    bin_path = f"{root}.bin"
    meta_path = f"{root}_metadata.json"

    os.makedirs(os.path.dirname(os.path.abspath(bin_path)), exist_ok=True)

    # Guardar bytes empaquetados
    raw_bytes = stream.to_bytes()
    with open(bin_path, "wb") as f_bin:
        f_bin.write(raw_bytes)

    # Guardar metadatos
    metadata = {
        "bits_per_sample": stream.bits_per_sample,
        "sample_rate": stream.sample_rate,
        "total_bits": stream.total_bits,
        "total_bytes": len(raw_bytes),
        "total_samples": len(stream.quantized_levels),
        "quantization_levels": 2 ** stream.bits_per_sample,
        "v_min": stream.v_min,
        "v_max": stream.v_max,
        "step_size_delta": float((stream.v_max - stream.v_min) / (2 ** stream.bits_per_sample - 1)),
        "sqnr_empirical_db": round(stream.sqnr_db, 2),
        "sqnr_theoretical_db": round(stream.sqnr_theoretical_db, 2),
        "first_64_bits": "".join(str(b) for b in stream.bitstream[:64])
    }

    with open(meta_path, "w", encoding="utf-8") as f_json:
        json.dump(metadata, f_json, indent=4)

    return os.path.abspath(bin_path), os.path.abspath(meta_path)


def load_digital_stream(base_filepath: str) -> DigitalStream:
    """
    Carga un flujo digital a partir de sus archivos .bin y _metadata.json.
    """
    root, _ = os.path.splitext(base_filepath)
    bin_path = f"{root}.bin"
    meta_path = f"{root}_metadata.json"

    with open(meta_path, "r", encoding="utf-8") as f_json:
        meta = json.load(f_json)

    with open(bin_path, "rb") as f_bin:
        raw_bytes = f_bin.read()

    stream = DigitalStream.from_bytes(
        raw_bytes=raw_bytes,
        total_bits=meta["total_bits"],
        bits_per_sample=meta["bits_per_sample"],
        sample_rate=meta["sample_rate"],
        v_min=meta["v_min"],
        v_max=meta["v_max"]
    )
    stream.sqnr_db = meta.get("sqnr_empirical_db", 0.0)
    return stream


def plot_sampling_nqs_study(signal: AudioSignal, save_path: Optional[str] = None,
                            show: bool = False) -> plt.Figure:
    """
    Genera una gráfica comparativa del Muestreo aplicando el Teorema de Nyquist-Shannon (NQS).
    Evalúa 3 escenarios críticos:
      1. Sobremuestreo (fs original >> 2*f_max)
      2. Muestreo crítico o cercano a Nyquist (fs ~ 2*f_max)
      3. Submuestreo severo (fs < 2*f_max con aliasing evidente)
    """
    props = analyze_signal_properties(signal)
    f_max = max(100.0, props['f_max_effective_hz'])
    fs_orig = signal.sample_rate

    # Factores de submuestreo ilustrativos
    factor_nyquist = max(2, int(round(fs_orig / (2.0 * f_max))))
    factor_aliased = factor_nyquist * 4  # Muy por debajo de Nyquist

    t_sub_nyq, x_sub_nyq, fs_nyq = simulate_sampling_nqs(signal, downsample_factor=factor_nyquist)
    t_sub_alias, x_sub_alias, fs_alias = simulate_sampling_nqs(signal, downsample_factor=factor_aliased)

    # Ventana de visualización microscópica (primeros 15 ms para apreciar las muestras discretas)
    zoom_ms = 15.0
    zoom_s = zoom_ms / 1000.0
    mask_orig = signal.time_vector <= zoom_s
    mask_nyq = t_sub_nyq <= zoom_s
    mask_alias = t_sub_alias <= zoom_s

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    configs = [
        (axes[0], signal.time_vector[mask_orig], signal.samples[mask_orig], '#58a6ff',
         f"1. Sobremuestreo (Señal Continua Original: fs = {fs_orig:,} Hz > 2·f_max)",
         'Señal Continua x(t)'),
        (axes[1], t_sub_nyq[mask_nyq], x_sub_nyq[mask_nyq], '#d29922',
         f"2. Muestreo en Rango de Nyquist (fs' = {fs_nyq:,} Hz ≈ 2·f_max)",
         f"Muestras Discretas x[n] (Ts = {1000.0/fs_nyq:.2f} ms)"),
        (axes[2], t_sub_alias[mask_alias], x_sub_alias[mask_alias], '#f85149',
         f"3. Submuestreo / Violación NQS (fs'' = {fs_alias:,} Hz << 2·f_max) -> ALIASING",
         f"Muestras Discretas (Ts = {1000.0/fs_alias:.2f} ms)")
    ]

    for ax, t_plot, x_plot, color, title, label_text in configs:
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9', labelsize=9)
        ax.grid(True, color='#30363d', linestyle='--', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color('#30363d')
            
        # Dibujar siempre la señal continua tenue de fondo para referencia
        ax.plot(signal.time_vector[mask_orig] * 1000.0, signal.samples[mask_orig],
                color='#8b949e', linewidth=0.8, alpha=0.4, label='x(t) Original')

        if ax == axes[0]:
            ax.plot(t_plot * 1000.0, x_plot, color=color, linewidth=1.5, label=label_text)
        else:
            # Stem plot para representar impulsos discretos
            markerline, stemlines, baseline = ax.stem(
                t_plot * 1000.0, x_plot,
                linefmt='-', markerfmt='o', basefmt='-'
            )
            plt.setp(stemlines, color=color, linewidth=1.2)
            plt.setp(markerline, color=color, markersize=5)
            plt.setp(baseline, color='#30363d', linewidth=0.8)
            # Línea discontinua interpolada
            ax.plot(t_plot * 1000.0, x_plot, color=color, linestyle=':', alpha=0.7, label='Envolvente Muestreada')

        ax.set_title(title, color='#f0f6fc', fontsize=11, fontweight='bold', pad=8)
        ax.set_xlabel("Tiempo [milisegundos]", color='#c9d1d9', fontsize=9)
        ax.set_ylabel("Amplitud [-1.0, 1.0]", color='#c9d1d9', fontsize=9)
        ax.set_xlim(0, zoom_ms)
        ax.set_ylim(-1.05, 1.05)
        ax.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"[Grafica NQS] Figura exportada a: {save_path}")

    if show:
        plt.show()

    return fig


def plot_quantization_analysis(signal: AudioSignal, stream: DigitalStream,
                               save_path: Optional[str] = None, show: bool = False) -> plt.Figure:
    """
    Muestra la gráfica de resolución [Byte / Bit]:
      - Señal continua vs cuantizada (efecto escalera)
      - Señal de error de cuantización e[n] con bandas de incertidumbre ±Δ/2
      - Desglose de bitstream de las primeras muestras
    """
    b = stream.bits_per_sample
    v_min, v_max = stream.v_min, stream.v_max
    step_delta = (v_max - v_min) / (2 ** b - 1)
    
    # Ventana corta para observar los escalones claramente (primeros 10 ms)
    zoom_samples = min(int(signal.sample_rate * 0.010), len(signal.samples))
    t_zoom = signal.time_vector[:zoom_samples] * 1000.0  # ms
    x_orig = signal.samples[:zoom_samples]
    x_quant = stream.reconstructed_levels[:zoom_samples]
    error = x_orig - x_quant

    fig, (ax_quant, ax_err) = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax_quant, ax_err):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9', labelsize=9)
        ax.grid(True, color='#30363d', linestyle='--', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    # PANEL 1: Cuantización (Escalera)
    ax_quant.plot(t_zoom, x_orig, color='#58a6ff', linewidth=1.2, label='Señal Continua Original x(t)')
    ax_quant.step(t_zoom, x_quant, where='mid', color='#f0883e', linewidth=1.4,
                  label=f"Cuantizada x_q(t) [{b} bits | {2**b} niveles | {b/8:.1f} Byte/m]")
    ax_quant.set_title(
        f"Cuantización Uniforme: Resolución de {b} bits ({b/8:.2f} Bytes/muestra) | "
        f"Paso Δ = {step_delta:.4f} V | SQNR = {stream.sqnr_db:.2f} dB (Teor: {stream.sqnr_theoretical_db:.2f} dB)",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax_quant.set_xlabel("Tiempo [milisegundos]", color='#c9d1d9', fontsize=9)
    ax_quant.set_ylabel("Amplitud [-1.0, 1.0]", color='#c9d1d9', fontsize=9)
    ax_quant.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    # PANEL 2: Ruido de Cuantización
    ax_err.plot(t_zoom, error, color='#f85149', linewidth=1.0, label='Error e(t) = x(t) - x_q(t)')
    ax_err.axhline(step_delta / 2.0, color='#d29922', linestyle='--', linewidth=1.2,
                   label=f'+Δ/2 (+{step_delta/2.0:.4f})')
    ax_err.axhline(-step_delta / 2.0, color='#d29922', linestyle='--', linewidth=1.2,
                   label=f'-Δ/2 (-{step_delta/2.0:.4f})')
    ax_err.set_title("Ruido de Cuantización Instantáneo (Confinado en banda [-Δ/2, +Δ/2])",
                     color='#f0f6fc', fontsize=11, fontweight='bold', pad=8)
    ax_err.set_xlabel("Tiempo [milisegundos]", color='#c9d1d9', fontsize=9)
    ax_err.set_ylabel("Error de Amplitud", color='#c9d1d9', fontsize=9)
    ax_err.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"[Grafica Cuantizacion] Figura exportada a: {save_path}")

    if show:
        plt.show()

    return fig
