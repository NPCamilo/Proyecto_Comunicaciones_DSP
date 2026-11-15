"""
API FastAPI - Servidor Backend para la Plataforma Web Audio DSP
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

Permite interactuar en tiempo real con la cadena completa de audio:
- Ingesta de archivos de audio de hasta 10 minutos (WAV, MP3, OGG)
- Muestreo Nyquist-Shannon y cuantización PCM (4, 8, 16 bits)
- Modulación y demodulación analógica (AM, FM) y digital (FSK, ASK, BPSK)
- Reconstrucción DAC por interpolación Sinc de Whittaker-Shannon y ZOH
- Cálculo de métricas de fidelidad cuantitativa (SNR, PSNR, Pearson r, MSE)
"""

import base64
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scipy.io import wavfile

# Asegurar importaciones del proyecto raíz
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.base import AudioSignal, DigitalStream, ModulatedSignal, DemodulatedResult
from src.core.audio_io import load_wav, generate_synthetic_speech_phrase
from src.core.analyzer import analyze_signal_properties
from src.core.quantization import quantize_signal
from src.modulation import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator,
)
from src.demodulation import (
    AMDemodulator,
    FMDemodulator,
    DigitalShiftKeyingDemodulator,
)
from src.reconstruction import AudioReconstructor
from pipeline_cli import run_dsp_pipeline

app = FastAPI(
    title="Audio DSP Transceiver API",
    description="Motor analítico y de comunicaciones para la cadena de Audio DSP (UTP)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def audio_signal_to_wav_base64(signal: AudioSignal) -> str:
    """Convierte un AudioSignal a cadena base64 en formato WAV PCM 16-bit."""
    buffer = io.BytesIO()
    samples = np.asarray(signal.samples, dtype=np.float32)
    # Escalar a int16 sin saturar
    peak = float(np.max(np.abs(samples))) or 1.0
    int16_samples = np.clip(samples / peak * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(buffer, int(signal.sample_rate), int16_samples)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def extract_waveform_summary(samples: np.ndarray, num_points: int = 120) -> list[float]:
    """Genera un perfil reducido de amplitud para renderizado reactivo en el frontend."""
    if len(samples) == 0:
        return [0.0] * num_points
    chunk_size = max(1, len(samples) // num_points)
    summary = []
    for i in range(num_points):
        start = i * chunk_size
        end = min(len(samples), start + chunk_size)
        if start >= len(samples):
            summary.append(0.0)
        else:
            chunk = samples[start:end]
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            summary.append(round(min(1.0, rms * 2.0), 3))
    return summary


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Audio DSP Transceiver API", "engine": "Python 3.14 + FastAPI"}


@app.get("/api/audio/demo")
async def get_demo_data():
    demo_path = ROOT_DIR / "audio_data" / "datos_demo.json"
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="No se encontró el archivo canónico datos_demo.json")
    with open(demo_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.post("/api/audio/process")
async def process_audio_pipeline(
    file: Optional[UploadFile] = File(None),
    synthetic_duration: float = Form(3.0),
    sample_rate: Optional[int] = Form(None),
    sampling_frequency: Optional[int] = Form(None),
    pcm_bits: Optional[int] = Form(None),
    bits_per_sample: Optional[int] = Form(None),
    dac_method: str = Form("sinc"),
    modulation: Optional[str] = Form(None),
    modulation_scheme: Optional[str] = Form(None),
    carrier_freq: float = Form(20000.0),
    am_mode: str = Form("coherent"),
    samples_per_symbol: int = Form(16),
):
    temp_wav_path: Optional[str] = None
    try:
        # Resolver parámetros unificados
        final_sample_rate = int(sampling_frequency or sample_rate or 8000)
        final_pcm_bits = int(bits_per_sample or pcm_bits or 8)
        final_modulation = str(modulation_scheme or modulation or "none").lower().strip()
        duration_clamped = min(600.0, max(0.5, float(synthetic_duration)))

        # 1. Cargar señal de audio (archivo subido o sintético)
        if file is not None and file.filename:
            file_bytes = await file.read()
            if len(file_bytes) > 100 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="El archivo excede el límite máximo de 100 MB.")
            buffer = io.BytesIO(file_bytes)
            fs_read, raw_samples = wavfile.read(buffer)
            if raw_samples.ndim > 1:
                raw_samples = np.mean(raw_samples, axis=1)

            if raw_samples.dtype == np.int16:
                float_samples = raw_samples.astype(np.float32) / 32768.0
            elif raw_samples.dtype == np.int32:
                float_samples = raw_samples.astype(np.float32) / 2147483648.0
            elif raw_samples.dtype == np.uint8:
                float_samples = (raw_samples.astype(np.float32) - 128.0) / 128.0
            else:
                float_samples = raw_samples.astype(np.float32)

            peak = float(np.max(np.abs(float_samples))) or 1.0
            norm_samples = (float_samples / peak * 0.95).astype(np.float32)

            max_samples = int(fs_read * 600)
            if len(norm_samples) > max_samples:
                norm_samples = norm_samples[:max_samples]

            temp_f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_wav_path = temp_f.name
            temp_f.close()
            wavfile.write(temp_wav_path, int(fs_read), (norm_samples * 32767).astype(np.int16))

        # 2. Configurar modulador y demodulador según el esquema seleccionado
        modulator = None
        demodulator = None
        mod_input = "audio"

        if final_modulation != "none":
            if final_modulation == "am":
                modulator = AMModulator(carrier_freq=carrier_freq, mod_index=0.8)
                demodulator = AMDemodulator(method=am_mode)
                mod_input = "sampled_audio"
            elif final_modulation == "fm":
                modulator = FMModulator(carrier_freq=carrier_freq, freq_dev=1000.0)
                demodulator = FMDemodulator()
                mod_input = "sampled_audio"
            elif final_modulation in ("fsk", "ask", "bpsk"):
                modulator = DigitalShiftKeyingModulator(
                    mod_type=final_modulation.upper(),
                    carrier_freq=carrier_freq,
                    samples_per_symbol=samples_per_symbol,
                )
                demodulator = DigitalShiftKeyingDemodulator(
                    mod_type=final_modulation.upper(),
                    carrier_freq=carrier_freq,
                    samples_per_symbol=samples_per_symbol,
                )
                mod_input = "digital"

        # 3. Ejecutar la cadena DSP orquestada
        result = run_dsp_pipeline(
            wav_path=temp_wav_path,
            sampling_frequency=final_sample_rate,
            bits_per_sample=final_pcm_bits,
            method=dac_method,
            duration=duration_clamped,
            source_sample_rate=16000,
            modulator=modulator,
            demodulator=demodulator,
            carrier_freq=carrier_freq,
            modulation_input=mod_input,
            save_artifacts=False,
        )

        signal = result.audio.signal
        props = analyze_signal_properties(signal)
        reconstructed = result.reconstruction.reconstructed_signal
        metrics = result.reconstruction.metrics

        # Convertir a audio base64 para reproducción instantánea en el navegador
        original_b64 = audio_signal_to_wav_base64(signal)
        reconstructed_b64 = audio_signal_to_wav_base64(reconstructed)

        mod_b64 = None
        demod_b64 = None
        if result.modulation.applied and result.modulation.modulated_signal:
            mod_b64 = audio_signal_to_wav_base64(result.modulation.modulated_signal.to_audio_signal())
        if result.modulation.applied and result.modulation.demodulated_result:
            demod_b64 = audio_signal_to_wav_base64(result.modulation.demodulated_result.recovered_audio)

        return {
            "success": True,
            "message": "Pipeline DSP ejecutado exitosamente",
            "duration_s": round(float(signal.duration), 3),
            "sample_rate_hz": int(signal.sample_rate),
            "f_max_hz": round(float(props["f_max_effective_hz"]), 1),
            "nyquist_satisfied": bool(props["nyquist_satisfied"]),
            "pcm_rate_hz": int(final_sample_rate),
            "pcm_bits": int(final_pcm_bits),
            "sqnr_db": round(float(result.nqs.stream.sqnr_db), 2),
            "modulation_applied": bool(result.modulation.applied),
            "modulation_type": str(result.modulation.modulation_type or "none"),
            "demodulation_type": str(result.modulation.demodulation_type or "none"),
            "carrier_freq_hz": float(carrier_freq),
            "snr_db": round(float(metrics.snr_db), 3),
            "psnr_db": round(float(metrics.psnr_db), 3),
            "pearson_corr": round(float(metrics.pearson_corr), 6),
            "mse": float(metrics.mse),
            "audio_original_b64": original_b64,
            "audio_reconstructed_b64": reconstructed_b64,
            "audio_modulated_b64": mod_b64,
            "audio_demodulated_b64": demod_b64,
            "waveform_original": extract_waveform_summary(signal.samples, 120),
            "waveform_reconstructed": extract_waveform_summary(reconstructed.samples, 120),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.unlink(temp_wav_path)
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
