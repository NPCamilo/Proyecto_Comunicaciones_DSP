"""
Script Maestro de Producción - FASE 2: Modulación Analógica y Digital Pasabanda
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación, Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

USO:
    python fase2_demo.py                      # Ejecuta pipeline completo de modulación (AM, FM, FSK)
    python fase2_demo.py --scheme am --play   # Modula en AM y permite escuchar la portadora
    python fase2_demo.py --scheme fm --play   # Modula en FM y permite escuchar la portadora
    python fase2_demo.py --scheme fsk --play  # Modula en FSK digital y permite escuchar
"""

import argparse
import os
import sys

# Agregar la raíz del proyecto al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.audio_io import load_wav, record_voice_wav, save_wav
from src.core.quantization import quantize_signal, load_digital_stream
from src.modulation.analog_digital_stubs import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator,
    plot_modulated_signal,
    plot_modulation_spectrum_translation,
    play_modulated_audio
)


def run_phase2_pipeline(
    audio_path: str = None,
    scheme: str = "all",
    carrier_am: float = 3000.0,
    carrier_fm: float = 3500.0,
    carrier_fsk: float = 2500.0,
    play: bool = False,
    output_dir: str = "audio_data"
):
    """
    Ejecuta integralmente la Fase 2 del Transceptor DSP:
      1. Carga de audio banda base y trama digital generados en Fase 1.
      2. Modulación analógica AM (DSB-FC) y FM (Regla de Carson).
      3. Modulación digital pasabanda FSK / ASK sobre el flujo de bits.
      4. Generación y exportación de figuras técnicas (zoom temporal y FFT en dBFS).
      5. Exportación de audios WAV pasabanda y reproducción auditiva.
    """
    os.makedirs(output_dir, exist_ok=True)
    sep = "=" * 70

    print(sep)
    print("PROYECTO COMUNICACIONES I - CADENA DSP COMPLETA")
    print("EJECUCIÓN DE FASE 2: MODULACIÓN ANALÓGICA Y DIGITAL PASABANDA")
    print(sep)

    # -------------------------------------------------------------
    # 1. Carga o Adquisición de Señal Banda Base y Bitstream
    # -------------------------------------------------------------
    print("\n[Paso 1/4] Recuperando señal de entrada (Fase 1)...")
    orig_wav = audio_path or os.path.join(output_dir, "voz_original.wav")

    if os.path.exists(orig_wav):
        print(f"   [+] Cargando audio base: {orig_wav}")
        audio = load_wav(orig_wav)
    else:
        print("   [+] Audio no encontrado. Generando muestra acústica sintética...")
        audio = record_voice_wav(orig_wav, duration=3.0, sample_rate=16000)

    print(f"   [+] Duración: {audio.duration:.2f} s | fs = {audio.sample_rate:,} Hz | Muestras = {audio.num_samples:,}")

    # Cargar trama digital si existe
    bin_base = os.path.join(output_dir, "trama_digital_8bits")
    if os.path.exists(f"{bin_base}.bin"):
        print(f"   [+] Cargando trama digital PCM existente: {bin_base}.bin")
        stream = load_digital_stream(bin_base)
    else:
        print("   [+] Cuantizando audio base a 8 bits PCM para modulación digital...")
        stream = quantize_signal(audio, bits_per_sample=8)

    print(f"   [+] Trama digital lista: {stream.total_bits:,} bits ({stream.total_bytes:,} Bytes)")

    scheme_lower = scheme.lower()
    selected_for_play = None

    # -------------------------------------------------------------
    # 2. Modulación AM (Amplitud Modulada - DSB-FC)
    # -------------------------------------------------------------
    if scheme_lower in ("all", "am"):
        print("\n[Paso 2/4] Ejecutando Modulación AM (DSB-FC)...")
        am_modulator = AMModulator(carrier_freq=carrier_am, mod_index=0.8, am_type="DSB-FC")
        
        # Verificar sobremodulación
        is_over, mu, ac = am_modulator.check_overmodulation(audio)
        print(f"   [+] Frecuencia de portadora fc: {carrier_am:,.0f} Hz (Audible)")
        print(f"   [+] Índice de modulación (mu): {mu:.2f} ({'SOBREMODULADA' if is_over else 'NORMAL <= 1.0'})")
        print(f"   [+] Amplitud de portadora Ac: {ac:.3f} V")
        
        mod_am = am_modulator.modulate(audio)
        print(f"   [+] Potencia de portadora: {mod_am.metadata['carrier_power']:.4f} W")
        print(f"   [+] Potencia bandas laterales: {mod_am.metadata['sideband_power']:.4f} W")
        print(f"   [+] Eficiencia de modulación: {mod_am.metadata['efficiency_percent']:.2f}%")

        # Gráfica de señal AM (zoom temporal y espectro)
        plot_am_path = os.path.join(output_dir, "04_modulacion_am_espectro.png")
        plot_modulated_signal(mod_am, base_signal=audio, zoom_ms=10.0, save_path=plot_am_path, show=False)

        # Gráfica de traslación en frecuencia
        plot_trans_path = os.path.join(output_dir, "07_traslacion_espectral_am.png")
        plot_modulation_spectrum_translation(audio, mod_am, save_path=plot_trans_path, show=False)

        # Guardar audio modulado en WAV
        wav_am_path = os.path.join(output_dir, "modulada_am.wav")
        save_wav(wav_am_path, mod_am.to_audio_signal(), bit_depth=16)
        print(f"   [+] Audio pasabanda exportado: {wav_am_path}")

        if scheme_lower == "am":
            selected_for_play = mod_am

    # -------------------------------------------------------------
    # 3. Modulación FM (Frecuencia Modulada - WBFM / NBFM)
    # -------------------------------------------------------------
    if scheme_lower in ("all", "fm"):
        print("\n[Paso 3/4] Ejecutando Modulación FM...")
        fm_modulator = FMModulator(carrier_freq=carrier_fm, freq_dev=1200.0)
        mod_fm = fm_modulator.modulate(audio)

        print(f"   [+] Frecuencia de portadora fc: {carrier_fm:,.0f} Hz (Audible)")
        print(f"   [+] Desviación de frecuencia (Delta_f): {mod_fm.metadata['freq_deviation_hz']:.1f} Hz")
        print(f"   [+] Índice de modulación beta: {mod_fm.metadata['modulation_index_beta']:.2f}")
        print(f"   [+] Régimen FM: {mod_fm.metadata['fm_regime']}")
        print(f"   [+] Ancho de banda de Carson: {mod_fm.metadata['bandwidth_carson_hz']:,.1f} Hz")
        print(f"   [+] Rango de frecuencia instantánea: [{mod_fm.metadata['min_instantaneous_freq']:,.1f}, {mod_fm.metadata['max_instantaneous_freq']:,.1f}] Hz")

        # Gráfica de señal FM
        plot_fm_path = os.path.join(output_dir, "05_modulacion_fm_espectro.png")
        plot_modulated_signal(mod_fm, zoom_ms=8.0, save_path=plot_fm_path, show=False)

        # Guardar audio modulado en WAV
        wav_fm_path = os.path.join(output_dir, "modulada_fm.wav")
        save_wav(wav_fm_path, mod_fm.to_audio_signal(), bit_depth=16)
        print(f"   [+] Audio pasabanda exportado: {wav_fm_path}")

        if scheme_lower == "fm":
            selected_for_play = mod_fm

    # -------------------------------------------------------------
    # 4. Modulación Digital FSK (BFSK de Fase Continua)
    # -------------------------------------------------------------
    if scheme_lower in ("all", "fsk", "ask"):
        print("\n[Paso 4/4] Ejecutando Modulación Digital Pasabanda...")
        
        # Tomar un fragmento representativo del bitstream para modular
        sample_bits = stream.bitstream[:1200]
        fsk_modulator = DigitalShiftKeyingModulator(
            mod_type="FSK",
            carrier_freq=carrier_fsk,
            f0=1800.0,
            f1=3200.0,
            samples_per_symbol=16,
            continuous_phase=True
        )
        mod_fsk = fsk_modulator.modulate(sample_bits)

        print(f"   [+] Esquema digital: FSK Binario de Fase Continua (CPFSK)")
        print(f"   [+] Frecuencia bit 0 (Espacio): {mod_fsk.metadata['f0_hz']:,.0f} Hz")
        print(f"   [+] Frecuencia bit 1 (Marca): {mod_fsk.metadata['f1_hz']:,.0f} Hz")
        print(f"   [+] Tasa binaria (Rb): {mod_fsk.metadata['bit_rate_bps']:,.1f} bps")
        print(f"   [+] Muestras por símbolo (sps): {mod_fsk.metadata['samples_per_symbol']}")

        # Gráfica FSK
        plot_fsk_path = os.path.join(output_dir, "06_modulacion_digital_fsk.png")
        plot_modulated_signal(mod_fsk, zoom_ms=12.0, save_path=plot_fsk_path, show=False)

        # Guardar audio modulado en WAV
        wav_fsk_path = os.path.join(output_dir, "modulada_fsk.wav")
        save_wav(wav_fsk_path, mod_fsk.to_audio_signal(), bit_depth=16)
        print(f"   [+] Audio pasabanda exportado: {wav_fsk_path}")

        if scheme_lower in ("fsk", "ask") or selected_for_play is None:
            selected_for_play = mod_fsk

    # -------------------------------------------------------------
    # 5. Audición de la Señal Modulada (Punto 4.3 del Proyecto)
    # -------------------------------------------------------------
    if play and selected_for_play is not None:
        print(f"\n-> Reproduciendo señal modulada ({selected_for_play.modulation_type}) a través del altavoz...")
        print(f"   [Aviso Psicoacústico] Notará el tono continuo/variable de la portadora modulada en frecuencia audible.")
        play_modulated_audio(selected_for_play, async_play=False)

    print("\n" + sep)
    print("FASE 2 COMPLETADA CON ÉXITO")
    print("Artefactos generados en carpeta:", os.path.abspath(output_dir))
    print(f" 1. Gráfica AM y Espectro: {os.path.join(output_dir, '04_modulacion_am_espectro.png')}")
    print(f" 2. Gráfica FM y Carson: {os.path.join(output_dir, '05_modulacion_fm_espectro.png')}")
    print(f" 3. Gráfica FSK Digital: {os.path.join(output_dir, '06_modulacion_digital_fsk.png')}")
    print(f" 4. Gráfica Traslación Espectral: {os.path.join(output_dir, '07_traslacion_espectral_am.png')}")
    print(f" 5. Audios WAV Modulados: modulada_am.wav, modulada_fm.wav, modulada_fsk.wav")
    print(sep)
    print(">> LISTO PARA TRANSFERIR A FASE 3 (DEMODULACIÓN Y RECUPERACIÓN) <<\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demostración y Validación de Fase 2 - Modulaciones DSP")
    parser.add_argument("--audio", type=str, default=None, help="Ruta a un archivo WAV existente")
    parser.add_argument("--scheme", type=str, default="all", choices=["all", "am", "fm", "fsk", "ask"],
                        help="Esquema a ejecutar (default: all)")
    parser.add_argument("--carrier_am", type=float, default=3000.0, help="Frecuencia portadora AM en Hz")
    parser.add_argument("--carrier_fm", type=float, default=3500.0, help="Frecuencia portadora FM en Hz")
    parser.add_argument("--carrier_fsk", type=float, default=2500.0, help="Frecuencia portadora FSK en Hz")
    parser.add_argument("--play", action="store_true", help="Permite escuchar el audio de la señal modulada")
    parser.add_argument("--outdir", type=str, default="audio_data", help="Directorio de artefactos")
    args = parser.parse_args()

    run_phase2_pipeline(
        audio_path=args.audio,
        scheme=args.scheme,
        carrier_am=args.carrier_am,
        carrier_fm=args.carrier_fm,
        carrier_fsk=args.carrier_fsk,
        play=args.play,
        output_dir=args.outdir
    )
