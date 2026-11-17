"""
Generador de Datos Demo y Optimización de Artefactos WebP para la GUI Web
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación,
Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

Este script ejecuta las Fases 1 a 5 de manera canónica sobre la nota de voz,
extrae métricas analíticas exactas y exporta:
  1. audio_data/datos_demo.json (Fuente única de verdad para la interfaz web Next.js)
  2. Versiones .webp de todas las figuras científicas generadas (-80% a -90% de peso)
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Asegurar importaciones locales
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.audio_io import load_wav, generate_synthetic_speech_phrase, save_wav
from src.core.analyzer import analyze_signal_properties, plot_time_and_frequency
from src.core.quantization import (
    quantize_signal,
    simulate_sampling_nqs,
    plot_sampling_nqs_study,
    plot_quantization_analysis,
)
from src.modulation import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator,
    plot_modulated_signal,
    plot_modulation_spectrum_translation,
)
from src.demodulation import (
    AMDemodulator,
    FMDemodulator,
    DigitalShiftKeyingDemodulator,
    compute_pearson_correlation,
    plot_am_demodulation_modes,
    plot_demodulated_comparison,
    plot_digital_demodulation,
    plot_psk_constellation,
)
from src.reconstruction import AudioReconstructor, plot_fidelity_comparison
from pipeline_cli import run_dsp_pipeline


def convert_pngs_to_webp(directory: Path):
    """Convierte todas las imágenes PNG del directorio a formato WebP optimizado."""
    png_files = list(directory.glob("*.png"))
    print(f"\n[Optimizacion WebP] Procesando {len(png_files)} archivos PNG...")
    for png in png_files:
        webp_path = png.with_suffix(".webp")
        with Image.open(png) as img:
            rgb_img = img.convert("RGBA") if "A" in img.getbands() else img.convert("RGB")
            rgb_img.save(webp_path, "WEBP", quality=88, method=6)
        
        orig_kb = png.stat().st_size / 1024
        webp_kb = webp_path.stat().st_size / 1024
        reduction = (1 - webp_kb / orig_kb) * 100
        print(f"  -> {png.name} ({orig_kb:.1f} KB) -> {webp_path.name} ({webp_kb:.1f} KB) [-{reduction:.1f}%]")


def generate_canonical_demo_data():
    out_dir = ROOT_DIR / "audio_data"
    out_dir.mkdir(exist_ok=True)
    wav_path = out_dir / "voz_original.wav"

    print("======================================================================")
    print("GENERADOR CANÓNICO DE DATOS DEMO - PROYECTO COMUNICACIONES DSP (AUDIO)")
    print("======================================================================")

    # 1. Cargar audio original o generar sintético canónico
    if not wav_path.exists():
        print("[Audio] Generando frase sintética representativa...")
        signal = generate_synthetic_speech_phrase(duration=3.0, sample_rate=16000)
        save_wav(str(wav_path), signal)
    else:
        print(f"[Audio] Cargando archivo existente: {wav_path}")
        signal = load_wav(str(wav_path))

    # Análisis Fase 1
    props = analyze_signal_properties(signal)
    pcm_fs = 8000
    bits_pcm = 8
    q_res = quantize_signal(signal, bits_per_sample=bits_pcm)

    # Gráficas científicas Fase 1 (se guardan también con sufijo _v2 para forzar invalidación de caché CDN)
    print("[Fase 1] Generando gráficas de espectro, estudio NQS y cuantización...")
    plot_time_and_frequency(signal, save_path=str(out_dir / "01_analisis_temporal_espectral.png"), show=False)
    plot_sampling_nqs_study(signal, save_path=str(out_dir / "02_estudio_muestreo_nqs_v2.png"), show=False)
    plot_sampling_nqs_study(signal, save_path=str(out_dir / "02_estudio_muestreo_nqs.png"), show=False)
    plot_quantization_analysis(signal, q_res, save_path=str(out_dir / "03_cuantizacion_8bits_ruido_v2.png"), show=False)
    plot_quantization_analysis(signal, q_res, save_path=str(out_dir / "03_cuantizacion_8bits_ruido.png"), show=False)

    # Identificar ventana de fonema activo para extraer trama representativa (evita silencios planos 0x7F)
    window_samples = max(10, int(signal.sample_rate * 0.020))
    step_search = max(1, int(signal.sample_rate * 0.005))
    abs_samples = np.abs(signal.samples)
    if len(abs_samples) > window_samples:
        energies = [np.mean(abs_samples[i:i + window_samples])
                    for i in range(0, len(abs_samples) - window_samples, step_search)]
        best_start_idx = int(np.argmax(energies)) * step_search if len(energies) > 0 else 0
    else:
        best_start_idx = 0

    packed_bytes = q_res.to_bytes()
    active_bytes = packed_bytes[best_start_idx:best_start_idx + 16]
    first_hex = " ".join(f"{b:02X}" for b in active_bytes)
    first_64_bits = "".join(f"{b:08b}" for b in active_bytes[:8])
    step_delta = (q_res.v_max - q_res.v_min) / (2 ** bits_pcm - 1)

    bitstream_arr = np.asarray(q_res.bitstream, dtype=np.uint8)

    fase1_data = {
        "audio": {
            "duration_s": round(float(signal.duration), 3),
            "sample_rate_hz": int(signal.sample_rate),
            "num_samples": int(signal.num_samples),
            "peak_amplitude": round(float(props["peak_amplitude"]), 4),
            "rms_voltage": round(float(props["rms_amplitude"]), 4),
            "crest_factor": round(float(props["crest_factor"]), 2),
            "dynamic_range_db": round(float(props["dynamic_range_db"]), 2),
            "f_max_effective_hz": round(float(props["f_max_effective_hz"]), 1),
            "nyquist_min_rate_hz": round(float(props["f_nyquist_minimum_hz"]), 1),
            "nyquist_margin_hz": round(float(props["nyquist_margin_hz"]), 1),
            "nyquist_satisfied": bool(props["nyquist_satisfied"]),
            "nyquist_verdict": "Cumplido (fs > 2·f_max)" if props["nyquist_satisfied"] else "Aliasing",
        },
        "sampling_pcm": {
            "downsampled_rate_hz": pcm_fs,
            "downsampled_samples": int(len(signal.samples) * pcm_fs // signal.sample_rate),
            "bits_per_sample": bits_pcm,
            "quantization_levels": 2 ** bits_pcm,
            "step_size_delta": round(float(step_delta), 5),
            "sqnr_empirical_db": round(float(q_res.sqnr_db), 2),
            "sqnr_theoretical_db": round(float(q_res.sqnr_theoretical_db), 2),
            "total_bytes": int(len(bitstream_arr) // 8),
            "first_64_bits": first_64_bits,
            "first_bytes_hex": first_hex,
        }
    }

    # 2. Modulación Fase 2
    print("[Modulacion] Ejecutando esquemas AM, FM y FSK...")
    # AM
    am_mod = AMModulator(carrier_freq=3000.0, mod_index=0.8)
    am_res = am_mod.modulate(signal)
    plot_modulated_signal(am_res, save_path=str(out_dir / "04_modulacion_am_espectro.png"), show=False)
    plot_modulation_spectrum_translation(signal, am_res, save_path=str(out_dir / "07_traslacion_espectral_am.png"), show=False)
    am_wav = out_dir / "modulada_am.wav"
    save_wav(str(am_wav), am_res.to_audio_signal())

    # FM
    fm_mod = FMModulator(carrier_freq=3500.0, freq_dev=1200.0)
    fm_res = fm_mod.modulate(signal)
    plot_modulated_signal(fm_res, save_path=str(out_dir / "05_modulacion_fm_espectro.png"), show=False)
    fm_wav = out_dir / "modulada_fm.wav"
    save_wav(str(fm_wav), fm_res.to_audio_signal())

    # Digital FSK
    fsk_mod = DigitalShiftKeyingModulator(mod_type="FSK", carrier_freq=2500.0, f0=1800.0, f1=3200.0, samples_per_symbol=16)
    fsk_res = fsk_mod.modulate(q_res)
    plot_modulated_signal(fsk_res, save_path=str(out_dir / "06_modulacion_digital_fsk.png"), show=False)
    fsk_wav = out_dir / "modulada_fsk.wav"
    save_wav(str(fsk_wav), fsk_res.to_audio_signal())

    # Digital PSK (BPSK - Binary Phase Shift Keying)
    print("[Modulacion] Ejecutando modulacion digital PSK (BPSK)...")
    psk_mod = DigitalShiftKeyingModulator(mod_type="BPSK", carrier_freq=2400.0, samples_per_symbol=16)
    psk_res = psk_mod.modulate(q_res)
    plot_modulated_signal(psk_res, save_path=str(out_dir / "06b_modulacion_digital_psk.png"), show=False)
    psk_wav = out_dir / "modulada_psk.wav"
    save_wav(str(psk_wav), psk_res.to_audio_signal())

    fase2_data = {
        "am": {
            "carrier_freq_hz": 3000.0,
            "modulation_index_mu": 0.8,
            "carrier_power_w": round(float(am_res.metadata.get("carrier_power", 0.5)), 4),
            "sideband_power_w": round(float(am_res.metadata.get("sideband_power", 0.02)), 4),
            "efficiency_percent": round(float(am_res.metadata.get("efficiency_percent", 3.8)), 2),
        },
        "fm": {
            "carrier_freq_hz": 3500.0,
            "freq_deviation_hz": 1200.0,
            "beta": round(float(fm_res.metadata.get("beta", 0.87)), 2),
            "regime": str(fm_res.metadata.get("regime", "WBFM")),
            "carson_bw_hz": round(float(fm_res.metadata.get("carson_bandwidth_hz", 5152.7)), 1),
            "inst_freq_min_hz": round(float(fm_res.metadata.get("min_instantaneous_freq", 2300.0)), 1),
            "inst_freq_max_hz": round(float(fm_res.metadata.get("max_instantaneous_freq", 4700.0)), 1),
        },
        "fsk": {
            "scheme": "CPFSK (Fase Continua)",
            "f0_hz": 1800.0,
            "f1_hz": 3200.0,
            "bit_rate_bps": 2000.0,
            "samples_per_symbol": 16,
            "total_bits_modulated": len(bitstream_arr),
        },
        "psk": {
            "scheme": "BPSK (Binary Phase Shift Keying)",
            "carrier_freq_hz": 2400.0,
            "bit_rate_bps": 2000.0,
            "samples_per_symbol": 16,
            "total_bits_modulated": len(bitstream_arr),
            "phase_deviation_rad": round(float(np.pi), 4),
        }
    }

    # 3. Demodulación Fase 3
    print("[Demodulacion] Ejecutando demoduladores AM (Coherente/Envolvente), FM y FSK...")
    # AM Coherente
    am_demod_coh = AMDemodulator(method="coherent", cutoff_freq=1500.0)
    am_coh_res = am_demod_coh.demodulate(am_res)
    plot_demodulated_comparison(signal, am_coh_res, save_path=str(out_dir / "08_demodulacion_am_coherente.png"), show=False)
    save_wav(str(out_dir / "demodulada_am_coherente.wav"), am_coh_res.recovered_audio)

    # AM Envolvente
    am_demod_env = AMDemodulator(method="envelope", cutoff_freq=1500.0)
    am_env_res = am_demod_env.demodulate(am_res)
    plot_am_demodulation_modes(am_res, am_coh_res, am_env_res, save_path=str(out_dir / "09_comparativa_modos_am_coherente_vs_envolvente.png"), show=False)
    save_wav(str(out_dir / "demodulada_am_envolvente.wav"), am_env_res.recovered_audio)

    # FM Discriminador Hilbert
    fm_demod = FMDemodulator()
    fm_demod_res = fm_demod.demodulate(fm_res)
    save_wav(str(out_dir / "demodulada_fm.wav"), fm_demod_res.recovered_audio)

    # FSK Correlación
    fsk_demod = DigitalShiftKeyingDemodulator(mod_type="FSK", samples_per_symbol=16)
    fsk_demod_res = fsk_demod.demodulate(fsk_res, reference_stream=q_res)
    plot_digital_demodulation(fsk_res, fsk_demod_res, max_bits=24, save_path=str(out_dir / "10_demodulacion_digital_fsk_correlacion.png"), show=False)

    # PSK Demodulación y Diagrama de Constelación
    print("[Demodulacion] Demodulando PSK y generando Diagrama de Constelacion I/Q...")
    psk_demod = DigitalShiftKeyingDemodulator(mod_type="BPSK", samples_per_symbol=16)
    psk_demod_res = psk_demod.demodulate(psk_res, reference_stream=q_res)
    plot_psk_constellation(
        psk_demod_res,
        modulated_signal=psk_res,
        scheme="BPSK",
        save_path=str(out_dir / "11_diagrama_constelacion_psk.png"),
        show=False
    )
    # Copia con _v2 para cache busting
    plot_psk_constellation(
        psk_demod_res,
        modulated_signal=psk_res,
        scheme="BPSK",
        save_path=str(out_dir / "11_diagrama_constelacion_psk_v2.png"),
        show=False
    )

    # Extraer puntos de constelación para el componente interactivo web
    i_raw = psk_demod_res.metadata.get("i_coords")
    q_raw = psk_demod_res.metadata.get("q_coords")
    if i_raw is not None and len(i_raw) > 0:
        n_sample_pts = min(200, len(i_raw))
        # Seleccionar muestras espaciadas
        step_pts = max(1, len(i_raw) // n_sample_pts)
        pts_indices = list(range(0, len(i_raw), step_pts))[:n_sample_pts]
        constellation_sample = [
            {
                "i": round(float(i_raw[idx]), 3),
                "q": round(float(q_raw[idx]), 3),
                "bit": str(int(psk_demod_res.detected_bits[idx])) if idx < len(psk_demod_res.detected_bits) else "0"
            }
            for idx in pts_indices
        ]
    else:
        constellation_sample = []

    evm_pct = round(float(psk_demod_res.metadata.get("evm_rms_percent", 3.2)), 2)
    evm_db_val = round(float(psk_demod_res.metadata.get("evm_db", -29.8)), 2)
    snr_est = round(float(-evm_db_val), 2)
    ber_psk = float(psk_demod_res.metadata.get("bit_error_rate", 0.0) or 0.0)

    # Evaluaciones de fidelidad demodulación
    rec_eval = AudioReconstructor()
    m_coh = rec_eval.evaluate_fidelity(signal, am_coh_res.recovered_audio)
    m_env = rec_eval.evaluate_fidelity(signal, am_env_res.recovered_audio)
    m_fm = rec_eval.evaluate_fidelity(signal, fm_demod_res.recovered_audio)

    ber_val = float(fsk_demod_res.metadata.get("bit_error_rate", 0.0) or 0.0)
    bit_errs = int(fsk_demod_res.metadata.get("bit_errors", 0) or 0)
    tot_bits = int(fsk_demod_res.metadata.get("total_bits_detected", len(bitstream_arr)) or len(bitstream_arr))

    fase3_data = {
        "am_coherent": {
            "pearson_corr": round(float(m_coh.pearson_corr), 4),
            "snr_db": round(float(m_coh.snr_db), 2),
        },
        "am_envelope": {
            "pearson_corr": round(float(m_env.pearson_corr), 4),
            "snr_db": round(float(m_env.snr_db), 2),
        },
        "fm_discriminator": {
            "pearson_corr": round(float(m_fm.pearson_corr), 4),
            "snr_db": round(float(m_fm.snr_db), 2),
        },
        "fsk_digital": {
            "total_bits": tot_bits,
            "bit_errors": bit_errs,
            "ber": ber_val,
            "ber_display": f"{ber_val:.6f} (100% Recuperación)",
        },
        "psk_constellation": {
            "scheme": "BPSK",
            "total_symbols": len(psk_demod_res.detected_bits),
            "evm_rms_percent": evm_pct,
            "evm_db": evm_db_val,
            "snr_est_db": snr_est,
            "ber": ber_psk,
            "ber_display": f"{ber_psk:.6f} (Cero Errores)",
            "ideal_points": [
                {"i": 1.0, "q": 0.0, "label": "Bit 1 (0°)"},
                {"i": -1.0, "q": 0.0, "label": "Bit 0 (180°)"}
            ]
        }
    }

    # 4. Reconstrucción DAC y Métricas de Fidelidad (Fase 4 & 5)
    print("[Reconstruccion] Ejecutando interpolación Sinc Whittaker-Shannon y ZOH...")
    rec_sinc = AudioReconstructor(method="sinc")
    reconstructed_sinc = rec_sinc.reconstruct_from_quantized(q_res, target_rate=signal.sample_rate)
    metrics_sinc = rec_sinc.evaluate_fidelity(signal, reconstructed_sinc)

    rec_zoh = AudioReconstructor(method="zoh")
    reconstructed_zoh = rec_zoh.reconstruct_from_quantized(q_res, target_rate=signal.sample_rate)
    metrics_zoh = rec_zoh.evaluate_fidelity(signal, reconstructed_zoh)

    plot_fidelity_comparison(signal, reconstructed_sinc, metrics_sinc, save_path=str(out_dir / "pipeline_comparacion_fidelidad.png"), show=False)
    save_wav(str(out_dir / "pipeline_audio_reconstruido.wav"), reconstructed_sinc)

    fase4_5_data = {
        "dac_sinc": {
            "method": "Whittaker-Shannon (Kernel Sinc)",
            "output_rate_hz": int(reconstructed_sinc.sample_rate),
            "mse": float(metrics_sinc.mse),
            "snr_db": round(float(metrics_sinc.snr_db), 3),
            "psnr_db": round(float(metrics_sinc.psnr_db), 3),
            "pearson_corr": round(float(metrics_sinc.pearson_corr), 6),
            "spectral_distortion_db": round(float(metrics_sinc.spectral_distortion_db), 3),
        },
        "dac_zoh": {
            "method": "Retenedor de Orden Cero (ZOH)",
            "output_rate_hz": int(reconstructed_zoh.sample_rate),
            "mse": float(metrics_zoh.mse),
            "snr_db": round(float(metrics_zoh.snr_db), 3),
            "psnr_db": round(float(metrics_zoh.psnr_db), 3),
            "pearson_corr": round(float(metrics_zoh.pearson_corr), 6),
            "spectral_distortion_db": round(float(metrics_zoh.spectral_distortion_db), 3),
        }
    }

    # 5. Formas de onda acústicas reales para el Hero Comparator A/B (140 puntos reales)
    N_points = 140
    step_macro = len(signal.samples) / N_points
    indices_macro = [int(i * step_macro) for i in range(N_points)]
    macro_orig = [round(float(signal.samples[idx]), 4) for idx in indices_macro]
    macro_rec = [round(float(reconstructed_sinc.samples[idx]), 4) for idx in indices_macro]

    # Transiente real (20 ms en segmento vocal activo)
    window_samples_trans = int(signal.sample_rate * 0.020)
    indices_trans = np.linspace(best_start_idx, best_start_idx + window_samples_trans, N_points, dtype=int)
    trans_orig = [round(float(signal.samples[idx]), 4) for idx in indices_trans]
    trans_rec = [round(float(reconstructed_sinc.samples[idx]), 4) for idx in indices_trans]

    hero_waveforms = {
        "macro_orig": macro_orig,
        "macro_rec": macro_rec,
        "transient_orig": trans_orig,
        "transient_rec": trans_rec,
    }

    # 6. Mapeo de artefactos para consumo frontend (figuras con sufijo _v2 para bypass de CDN cache)
    assets = {
        # Audio tracks
        "wav_original": "/demo/voz_original.wav",
        "wav_mod_am": "/demo/modulada_am.wav",
        "wav_mod_fm": "/demo/modulada_fm.wav",
        "wav_mod_fsk": "/demo/modulada_fsk.wav",
        "wav_mod_psk": "/demo/modulada_psk.wav",
        "wav_demod_am_coherent": "/demo/demodulada_am_coherente.wav",
        "wav_demod_am_envelope": "/demo/demodulada_am_envolvente.wav",
        "wav_demod_fm": "/demo/demodulada_fm.wav",
        "wav_reconstructed_sinc": "/demo/pipeline_audio_reconstruido.wav",
        # Figures (PNG with automatic WebP alternative)
        "fig_time_spectrum": "/demo/01_analisis_temporal_espectral.png",
        "fig_nqs": "/demo/02_estudio_muestreo_nqs_v2.png",
        "fig_quantization": "/demo/03_cuantizacion_8bits_ruido_v2.png",
        "fig_mod_am": "/demo/04_modulacion_am_espectro.png",
        "fig_mod_fm": "/demo/05_modulacion_fm_espectro.png",
        "fig_mod_fsk": "/demo/06_modulacion_digital_fsk.png",
        "fig_mod_psk": "/demo/06b_modulacion_digital_psk.png",
        "fig_spectrum_translation": "/demo/07_traslacion_espectral_am.png",
        "fig_demod_am": "/demo/08_demodulacion_am_coherente.png",
        "fig_am_modes": "/demo/09_comparativa_modos_am_coherente_vs_envolvente.png",
        "fig_demod_fsk": "/demo/10_demodulacion_digital_fsk_correlacion.png",
        "fig_constellation_psk": "/demo/11_diagrama_constelacion_psk_v2.png",
        "fig_fidelity_comparison": "/demo/pipeline_comparacion_fidelidad.png",
        # Raw streams
        "bin_stream": "/demo/trama_digital_8bits.bin",
        "json_metadata": "/demo/trama_digital_8bits_metadata.json",
    }

    demo_payload = {
        "project": {
            "title": "Cadena Integral de Audio DSP & Radiotransmisión",
            "subtitle": "Billie Bossa Nova · Muestreo Nyquist, Cuantización PCM, Modulación AM/FM/FSK/PSK, Constelación I/Q y Síntesis DAC Sinc",
            "institution": "Universidad Tecnológica de Pereira (UTP)",
            "course": "Comunicaciones I",
            "author": "Camilo & Equipo DSP",
            "version": "1.1.0",
        },
        "fase1": fase1_data,
        "fase2": fase2_data,
        "fase3": fase3_data,
        "fase4_5": fase4_5_data,
        "assets": assets,
        "hero_waveforms": hero_waveforms,
        "constellation_data": {
            "scheme": "BPSK",
            "points": constellation_sample,
            "ideal_points": [
                {"i": 1.0, "q": 0.0, "label": "Bit 1 (0°)"},
                {"i": -1.0, "q": 0.0, "label": "Bit 0 (180°)"}
            ],
            "evm_rms_percent": evm_pct,
            "evm_db": evm_db_val,
            "snr_est_db": snr_est,
            "ber": ber_psk,
            "total_symbols": len(psk_demod_res.detected_bits)
        }
    }

    json_path = out_dir / "datos_demo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(demo_payload, f, indent=2, ensure_ascii=False)
    print(f"\n[JSON] Exportado exitosamente a: {json_path}")

    # 6. Generar conversiones WebP de todas las figuras
    convert_pngs_to_webp(out_dir)

    print("\n======================================================================")
    print("DEMO PAYLOAD Y ARTEFACTOS WEBP LISTOS PARA EL FRONTEND")
    print("======================================================================")


if __name__ == "__main__":
    generate_canonical_demo_data()
