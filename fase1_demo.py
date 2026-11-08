"""
Script Maestro de Producción - FASE 1: Adquisición, Análisis y Digitalización PCM
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación, Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

USO:
    python fase1_demo.py                     # Ejecuta grabación/síntesis, análisis y digitalización
    python fase1_demo.py --audio ruta.wav    # Usa un audio WAV preexistente
    python fase1_demo.py --bits 8 --play     # Cuantiza a 8 bits (1 Byte) y reproduce el audio
"""

import argparse
import os
import sys

# Agregar la raíz del proyecto al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.audio_io import record_voice_wav, load_wav, play_audio, save_wav
from src.core.analyzer import analyze_signal_properties, plot_time_and_frequency
from src.core.quantization import (
    quantize_signal,
    save_digital_stream,
    plot_sampling_nqs_study,
    plot_quantization_analysis
)


def run_phase1_pipeline(audio_path: str = None, duration: float = 3.0,
                        sample_rate: int = 16000, bits: int = 8,
                        play: bool = False, output_dir: str = "audio_data"):
    """
    Ejecuta integralmente la Fase 1:
      1. Adquisición de audio WAV (Punto 1)
      2. Reproducción y análisis temporal y frecuencial (Punto 2)
      3. Muestreo NQS y Cuantización [Byte/Bit] con serialización digital (Punto 3)
    """
    os.makedirs(output_dir, exist_ok=True)
    sep = "=" * 70

    print(sep)
    print("PROYECTO COMUNICACIONES I - CADENA DSP COMPLETA")
    print("EJECUCIÓN DE FASE 1: ADQUISICIÓN, ANÁLISIS Y DIGITALIZACIÓN PCM")
    print(sep)

    # -------------------------------------------------------------
    # 1. Grabación o Carga de la Señal WAV (Punto 1 y 2)
    # -------------------------------------------------------------
    print("\n[Paso 1/3] Adquisición de la señal de voz en formato WAV...")
    if audio_path and os.path.exists(audio_path):
        print(f"-> Cargando archivo existente: {audio_path}")
        signal = load_wav(audio_path)
    else:
        target_wav = os.path.join(output_dir, "voz_original.wav")
        print(f"-> Grabando nota de voz ({duration:.1f} segundos a {sample_rate} Hz)...")
        signal = record_voice_wav(target_wav, duration=duration, sample_rate=sample_rate)

    print(f"   [+] Archivo: {signal.filename}")
    print(f"   [+] Frecuencia de muestreo (fs): {signal.sample_rate:,} Hz")
    print(f"   [+] Muestras totales: {signal.num_samples:,}")
    print(f"   [+] Duracion: {signal.duration:.3f} segundos")

    if play:
        print("-> Reproduciendo audio original capturado...")
        play_audio(signal)

    # -------------------------------------------------------------
    # 2. Análisis Temporal, Espectral y Criterio NQS (Punto 2)
    # -------------------------------------------------------------
    print("\n[Paso 2/3] Analisis de la senal original en tiempo y frecuencia...")
    props = analyze_signal_properties(signal, energy_percent=0.99)

    print(f"   [+] Amplitud Pico: {props['peak_amplitude']:.4f}")
    print(f"   [+] Voltaje RMS: {props['rms_amplitude']:.4f}")
    print(f"   [+] Factor de Cresta: {props['crest_factor']:.2f}")
    print(f"   [+] Rango Dinamico: {props['dynamic_range_db']:.2f} dB")
    print(f"   [+] Frecuencia Maxima Efectiva (99% energia): {props['f_max_effective_hz']:.1f} Hz")
    print(f"   [+] Tasa de Nyquist Minima Teorica (2*f_max): {props['f_nyquist_minimum_hz']:.1f} Hz")
    
    if props['nyquist_satisfied']:
        print(f"   [OK] Condicion Nyquist-Shannon: SATISFECHA (Margen: +{props['nyquist_margin_hz']:.1f} Hz)")
    else:
        print(f"   [ALERTA] Condicion Nyquist-Shannon: NO SATISFECHA (Posible Aliasing)")

    # Generar y guardar gráfica temporal y espectral
    plot1_path = os.path.join(output_dir, "01_analisis_temporal_espectral.png")
    plot_time_and_frequency(signal, save_path=plot1_path, show=False)

    # -------------------------------------------------------------
    # 3. Muestreo NQS y Cuantización [Byte / Bit] (Punto 3)
    # -------------------------------------------------------------
    print(f"\n[Paso 3/3] Muestreo NQS y Cuantizacion Digital a {bits} bits/muestra...")
    
    # 3.1 Estudio gráfico de Nyquist-Shannon
    plot2_path = os.path.join(output_dir, "02_estudio_muestreo_nqs.png")
    plot_sampling_nqs_study(signal, save_path=plot2_path, show=False)

    # 3.2 Cuantización Digital
    stream = quantize_signal(signal, bits_per_sample=bits)
    print(f"   [+] Tecnica de resolucion: {bits} bits/muestra ({bits/8:.2f} Bytes/muestra)")
    print(f"   [+] Niveles discretos de cuantizacion (L = 2^b): {2**bits:,} niveles")
    print(f"   [+] Paso de cuantizacion (Delta): {(stream.v_max - stream.v_min)/(2**bits - 1):.5f} V")
    print(f"   [+] Total de bits en la trama digital: {stream.total_bits:,} bits ({stream.total_bytes:,} Bytes)")
    print(f"   [+] SQNR Experimental medido: {stream.sqnr_db:.2f} dB")
    print(f"   [+] SQNR Teorico (6.02b + 1.76): {stream.sqnr_theoretical_db:.2f} dB")
    print(f"   [+] Primeros 48 bits generados: {''.join(str(b) for b in stream.bitstream[:48])}...")

    # Guardar en disco el bitstream binario empaquetado y sus metadatos
    bin_base = os.path.join(output_dir, f"trama_digital_{bits}bits")
    bin_file, meta_file = save_digital_stream(stream, bin_base)
    print(f"   [+] Archivo binario empaquetado (.bin): {bin_file}")
    print(f"   [+] Metadatos de serializacion (.json): {meta_file}")

    # Gráfica de cuantización y ruido de cuantización
    plot3_path = os.path.join(output_dir, f"03_cuantizacion_{bits}bits_ruido.png")
    plot_quantization_analysis(signal, stream, save_path=plot3_path, show=False)

    print("\n" + sep)
    print("FASE 1 COMPLETADA CON EXITO")
    print("Entregables generados en carpeta:", os.path.abspath(output_dir))
    print(f" 1. Audio WAV original: {signal.filename}")
    print(f" 2. Grafica Tiempo y Espectro: {plot1_path}")
    print(f" 3. Grafica Teorema de Nyquist: {plot2_path}")
    print(f" 4. Trama binaria cuantizada: {bin_file}")
    print(f" 5. Grafica Cuantizacion y Ruido: {plot3_path}")
    print(sep)
    print(">> LISTO PARA TRANSFERIR A LOS COLABORADORES PARA LAS FASES 2, 3 Y 4 <<\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecución de Fase 1 - Proyecto Comunicaciones I DSP")
    parser.add_argument("--audio", type=str, default=None, help="Ruta a un archivo WAV existente")
    parser.add_argument("--duration", type=float, default=3.0, help="Duración de la nota de voz en segundos (2-5s)")
    parser.add_argument("--sample_rate", type=int, default=16000, help="Frecuencia de muestreo fs (Hz)")
    parser.add_argument("--bits", type=int, default=8, help="Resolución en bits para cuantización [1-16] (default: 8 = 1 Byte)")
    parser.add_argument("--play", action="store_true", help="Reproducir el audio al cargar/grabar")
    parser.add_argument("--outdir", type=str, default="audio_data", help="Directorio para guardar artefactos")
    args = parser.parse_args()

    run_phase1_pipeline(
        audio_path=args.audio,
        duration=args.duration,
        sample_rate=args.sample_rate,
        bits=args.bits,
        play=args.play,
        output_dir=args.outdir
    )
