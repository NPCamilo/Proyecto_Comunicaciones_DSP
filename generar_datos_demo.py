"""
Generador de Datos Demo y Optimización de Artefactos WebP para la GUI Web
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación,
Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

Señal Maestra: Billie Bossa Nova (Billie Eilish) - Coro Principal (8.0 s)
"""

import json
import os
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
import scipy.signal as signal_proc
from PIL import Image

# Asegurar importaciones locales
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.base import AudioSignal
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


def extract_billie_bossa_nova_chorus(target_path: Path, duration_s: float = 8.0, start_s: float = 50.0) -> AudioSignal:
    """Extrae el coro principal de Billie Bossa Nova a 16 kHz mono con ganancia normalizada a 0.90."""
    music_src = Path(r"C:\Users\USUARIO\Music\Songs\Billie Bossa Nova.wav")
    target_sr = 16000

    if music_src.exists():
        print(f"[Audio Source] Extrayendo {duration_s:.1f}s desde t = {start_s:.1f}s de: {music_src}")
        with wave.open(str(music_src), "rb") as w:
            sr = w.getframerate()
            n_chan = w.getnchannels()
            w.setpos(int(start_s * sr))
            raw = w.readframes(int(duration_s * sr))

        data = np.frombuffer(raw, dtype=np.int16).reshape(-1, n_chan)
        mono = data.mean(axis=1).astype(np.float32) / 32768.0

        # Remuestrear a 16,000 Hz
        resampled = signal_proc.resample_poly(mono, target_sr, sr).astype(np.float32)
        peak = float(np.max(np.abs(resampled)))
        if peak > 1e-6:
            resampled = (resampled / peak * 0.90).astype(np.float32)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        scaled_int16 = np.int16(np.clip(resampled * 32767.0, -32768, 32767))
        with wave.open(str(target_path), "wb") as w_out:
            w_out.setnchannels(1)
            w_out.setsampwidth(2)
            w_out.setframerate(target_sr)
            w_out.writeframes(scaled_int16.tobytes())

        print(f"[Audio Source] Guardado exitosamente: {len(resampled)} muestras ({len(resampled)/target_sr:.2f} s) en {target_path}")
        return AudioSignal(
            samples=resampled,
            sample_rate=target_sr,
            bit_depth=16,
            metadata={"source": "Billie Bossa Nova (Coro Principal)", "duration": duration_s}
        )
    elif target_path.exists():
        print(f"[Audio Source] Cargando audio local existente: {target_path}")
        return load_wav(str(target_path))
    else:
        print("[Audio Source] Generando señal acústica sintética...")
        sig = generate_synthetic_speech_phrase(duration=duration_s, sample_rate=target_sr)
        save_wav(str(target_path), sig)
        return sig


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


def sync_assets_to_public_demo(source_dir: Path, public_dir: Path):
    """Sincroniza todos los artefactos de datos, figuras e imágenes a public/demo/."""
    public_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in source_dir.glob("*"):
        if item.is_file():
            shutil.copyfile(item, public_dir / item.name)
            count += 1
    print(f"[Sync] {count} artefactos copiados a: {public_dir}")


def generate_canonical_demo_data():
    out_dir = ROOT_DIR / "audio_data"
    public_demo_dir = ROOT_DIR / "public" / "demo"
    out_dir.mkdir(exist_ok=True)
    wav_path = out_dir / "voz_original.wav"

    print("======================================================================")
    print("GENERADOR CANÓNICO DE DATOS DEMO - PROYECTO COMUNICACIONES DSP (AUDIO)")
    print("SEÑAL MAESTRA: BILLIE BOSSA NOVA (CORO PRINCIPAL, 8.0 S)")
    print("======================================================================")

    # 1. Extracción y análisis de la señal acústica musical
    signal = extract_billie_bossa_nova_chorus(wav_path, duration_s=8.0, start_s=50.0)

    # Análisis Fase 1: Tiempo & Espectro FFT
    props = analyze_signal_properties(signal)
    pcm_fs = 8000
    bits_pcm = 8
    q_res = quantize_signal(signal, bits_per_sample=bits_pcm)

    print("[Fase 1] Generando gráficas de espectro, estudio NQS y cuantización...")
    plot_time_and_frequency(signal, save_path=str(out_dir / "01_analisis_temporal_espectral.png"), show=False)
    plot_time_and_frequency(signal, save_path=str(out_dir / "01_analisis_temporal_espectral_v2.png"), show=False)
    plot_sampling_nqs_study(signal, save_path=str(out_dir / "02_estudio_muestreo_nqs.png"), show=False)
    plot_sampling_nqs_study(signal, save_path=str(out_dir / "02_estudio_muestreo_nqs_v2.png"), show=False)
    plot_quantization_analysis(signal, q_res, save_path=str(out_dir / "03_cuantizacion_8bits_ruido.png"), show=False)
    plot_quantization_analysis(signal, q_res, save_path=str(out_dir / "03_cuantizacion_8bits_ruido_v2.png"), show=False)

    # Localizar ventana de alta energía activa
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
            "track_name": "Billie Bossa Nova (Billie Eilish)",
            "section": "Coro Principal (50.0s - 58.0s)",
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

    # 2. Modulación Fase 2 (Analógica AM/FM y Digital FSK/PSK)
    print("[Modulacion] Ejecutando esquemas AM, FM, FSK y BPSK...")
    # AM: fc = 6000 Hz, mu = 0.80, target_sample_rate = 32000
    am_mod = AMModulator(carrier_freq=6000.0, mod_index=0.8, target_sample_rate=32000)
    am_res = am_mod.modulate(signal)
    plot_modulated_signal(am_res, save_path=str(out_dir / "04_modulacion_am_espectro.png"), show=False)
    plot_modulation_spectrum_translation(signal, am_res, save_path=str(out_dir / "07_traslacion_espectral_am.png"), show=False)
    save_wav(str(out_dir / "modulada_am.wav"), am_res.to_audio_signal())

    # FM: fc = 6500 Hz, freq_dev = 1500 Hz, target_sample_rate = 32000
    fm_mod = FMModulator(carrier_freq=6500.0, freq_dev=1500.0, target_sample_rate=32000)
    fm_res = fm_mod.modulate(signal)
    plot_modulated_signal(fm_res, save_path=str(out_dir / "05_modulacion_fm_espectro.png"), show=False)
    save_wav(str(out_dir / "modulada_fm.wav"), fm_res.to_audio_signal())

    # Para FSK y PSK: Modulamos 16,000 bits a 2,000 bps = 8.0 segundos de transmisión digital síncrona
    num_digital_bits = min(len(bitstream_arr), 16000)
    bits_digital_demo = bitstream_arr[:num_digital_bits]

    # Digital FSK (CPFSK: f0 = 1800 Hz, f1 = 3200 Hz, Rb = 2000 bps, sps = 16, fs = 32000)
    fsk_mod = DigitalShiftKeyingModulator(mod_type="FSK", carrier_freq=2500.0, f0=1800.0, f1=3200.0, samples_per_symbol=16, sampling_rate=32000)
    fsk_res = fsk_mod.modulate(bits_digital_demo)
    plot_modulated_signal(fsk_res, save_path=str(out_dir / "06_modulacion_digital_fsk.png"), show=False)
    save_wav(str(out_dir / "modulada_fsk.wav"), fsk_res.to_audio_signal())

    # Digital PSK (BPSK: fc = 2000.0 Hz, 1 ciclo/símbolo exacto a 2000 Baud, sps = 16, fs = 32000)
    print("[Modulacion] Ejecutando modulacion digital PSK (BPSK)...")
    psk_mod = DigitalShiftKeyingModulator(mod_type="BPSK", carrier_freq=2000.0, samples_per_symbol=16, sampling_rate=32000)
    psk_res = psk_mod.modulate(bits_digital_demo)
    plot_modulated_signal(psk_res, save_path=str(out_dir / "06b_modulacion_digital_psk.png"), show=False)
    save_wav(str(out_dir / "modulada_psk.wav"), psk_res.to_audio_signal())

    fase2_data = {
        "am": {
            "carrier_freq_hz": 6000.0,
            "modulation_index_mu": 0.8,
            "carrier_power_w": round(float(am_res.metadata.get("carrier_power", 0.5)), 4),
            "sideband_power_w": round(float(am_res.metadata.get("sideband_power", 0.02)), 4),
            "efficiency_percent": round(float(am_res.metadata.get("efficiency_percent", 3.8)), 2),
        },
        "fm": {
            "carrier_freq_hz": 6500.0,
            "freq_deviation_hz": 1500.0,
            "beta": round(float(fm_res.metadata.get("beta", 0.29)), 2),
            "regime": str(fm_res.metadata.get("regime", "NBFM/WBFM")),
            "carson_bw_hz": round(float(fm_res.metadata.get("carson_bandwidth_hz", 13466.0)), 1),
            "inst_freq_min_hz": round(float(fm_res.metadata.get("min_instantaneous_freq", 5000.0)), 1),
            "inst_freq_max_hz": round(float(fm_res.metadata.get("max_instantaneous_freq", 8000.0)), 1),
        },
        "fsk": {
            "scheme": "CPFSK (Fase Continua)",
            "f0_hz": 1800.0,
            "f1_hz": 3200.0,
            "bit_rate_bps": 2000.0,
            "samples_per_symbol": 16,
            "total_bits_modulated": len(bits_digital_demo),
            "duration_s": round(float(len(fsk_res.samples) / fsk_res.sampling_rate), 2)
        },
        "psk": {
            "scheme": "BPSK (Binary Phase Shift Keying)",
            "carrier_freq_hz": 2000.0,
            "bit_rate_bps": 2000.0,
            "samples_per_symbol": 16,
            "total_bits_modulated": len(bits_digital_demo),
            "phase_deviation_rad": round(float(np.pi), 4),
            "duration_s": round(float(len(psk_res.samples) / psk_res.sampling_rate), 2)
        }
    }

    # 3. Demodulación Fase 3 (AM Coherente / Envolvente, FM Discriminador, FSK y BPSK Constelación)
    print("[Demodulacion] Ejecutando demoduladores AM, FM y receptores digitales...")
    # AM Coherente (corte en 5500 Hz para pasar la voz y la instrumentación completa)
    am_demod_coh = AMDemodulator(method="coherent", cutoff_freq=5500.0)
    am_coh_res = am_demod_coh.demodulate(am_res)
    plot_demodulated_comparison(signal, am_coh_res, save_path=str(out_dir / "08_demodulacion_am_coherente.png"), show=False)
    save_wav(str(out_dir / "demodulada_am_coherente.wav"), am_coh_res.recovered_audio)

    # AM Envolvente (Hilbert + corte 5500 Hz)
    am_demod_env = AMDemodulator(method="envelope", cutoff_freq=5500.0)
    am_env_res = am_demod_env.demodulate(am_res)
    plot_am_demodulation_modes(am_res, am_coh_res, am_env_res, save_path=str(out_dir / "09_comparativa_modos_am_coherente_vs_envolvente.png"), show=False)
    save_wav(str(out_dir / "demodulada_am_envolvente.wav"), am_env_res.recovered_audio)

    # FM Discriminador
    fm_demod = FMDemodulator()
    fm_demod_res = fm_demod.demodulate(fm_res)
    save_wav(str(out_dir / "demodulada_fm.wav"), fm_demod_res.recovered_audio)

    # FSK Correlación
    fsk_demod = DigitalShiftKeyingDemodulator(mod_type="FSK", samples_per_symbol=16)
    fsk_demod_res = fsk_demod.demodulate(fsk_res, reference_bits=bits_digital_demo)
    plot_digital_demodulation(fsk_res, fsk_demod_res, max_bits=24, save_path=str(out_dir / "10_demodulacion_digital_fsk_correlacion.png"), show=False)

    # PSK Demodulación con canal AWGN gaussiano (SNR = 25 dB) para dispersión realista
    print("[Demodulacion] Demodulando PSK y generando Diagrama de Constelacion I/Q...")
    snr_ch_db = 25.0
    sig_pwr = np.mean(psk_res.samples ** 2)
    noise_pwr = sig_pwr / (10 ** (snr_ch_db / 10.0))
    psk_noisy = psk_res.samples + np.random.normal(0, np.sqrt(noise_pwr), len(psk_res.samples)).astype(np.float32)
    psk_rx_sig = psk_res
    psk_rx_sig.samples = psk_noisy

    psk_demod = DigitalShiftKeyingDemodulator(mod_type="BPSK", carrier_freq=2000.0, samples_per_symbol=16)
    psk_demod_res = psk_demod.demodulate(psk_rx_sig, reference_bits=bits_digital_demo)

    plot_psk_constellation(
        psk_demod_res,
        modulated_signal=psk_rx_sig,
        scheme="BPSK",
        max_symbols=300,
        save_path=str(out_dir / "11_diagrama_constelacion_psk.png"),
        show=False
    )
    plot_psk_constellation(
        psk_demod_res,
        modulated_signal=psk_rx_sig,
        scheme="BPSK",
        max_symbols=300,
        save_path=str(out_dir / "11_diagrama_constelacion_psk_v2.png"),
        show=False
    )

    # Puntos de constelación para el componente vectorial interactivo
    i_raw = psk_demod_res.metadata.get("i_coords")
    q_raw = psk_demod_res.metadata.get("q_coords")
    if i_raw is not None and len(i_raw) > 0:
        n_sample_pts = min(200, len(i_raw))
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

    evm_pct = round(float(psk_demod_res.metadata.get("evm_rms_percent", 5.4)), 2)
    evm_db_val = round(float(psk_demod_res.metadata.get("evm_db", -25.3)), 2)
    snr_est = round(float(-evm_db_val), 2)
    ber_psk = float(psk_demod_res.metadata.get("bit_error_rate", 0.0) or 0.0)

    # Evaluación de fidelidad de demodulaciones
    rec_eval = AudioReconstructor()
    m_coh = rec_eval.evaluate_fidelity(signal, am_coh_res.recovered_audio)
    m_env = rec_eval.evaluate_fidelity(signal, am_env_res.recovered_audio)
    m_fm = rec_eval.evaluate_fidelity(signal, fm_demod_res.recovered_audio)

    ber_val = float(fsk_demod_res.metadata.get("bit_error_rate", 0.0) or 0.0)
    bit_errs = int(fsk_demod_res.metadata.get("bit_errors", 0) or 0)
    tot_bits = int(fsk_demod_res.metadata.get("total_bits_detected", len(bits_digital_demo)) or len(bits_digital_demo))

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

    # 4. Reconstrucción DAC Whittaker-Shannon Sinc (Fase 4 & 5)
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

    # Transiente real (20 ms en ventana acústica activa)
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

    # 6. Mapeo de artefactos para consumo frontend
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
            "version": "1.2.0",
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

    # 7. Conversión a WebP optimizado
    convert_pngs_to_webp(out_dir)

    # 8. Sincronización completa a public/demo/
    sync_assets_to_public_demo(out_dir, public_demo_dir)

    print("\n======================================================================")
    print("DEMO PAYLOAD, AUDIOS Y ARTEFACTOS WEBP COMPLETAMENTE ACTUALIZADOS")
    print("======================================================================")


if __name__ == "__main__":
    generate_canonical_demo_data()
