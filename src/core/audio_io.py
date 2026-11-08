"""
Módulo de Entrada/Salida y Grabación de Audio (Punto 1 y 2 del Proyecto)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import os
import platform
import time
from typing import Optional, Tuple
import numpy as np
from scipy.io import wavfile

from .base import AudioSignal


def load_wav(filepath: str) -> AudioSignal:
    """
    Carga un archivo WAV, lo convierte a mono si es necesario, normaliza su amplitud
    al intervalo estándar [-1.0, 1.0] en float32 y extrae sus metadatos físicos.
    
    Args:
        filepath (str): Ruta completa o relativa al archivo .wav
        
    Returns:
        AudioSignal: Objeto normalizado con las muestras y parámetros de muestreo.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo de audio: {filepath}")

    # scipy.io.wavfile maneja la mayoría de formatos PCM
    sr, raw_data = wavfile.read(filepath)
    
    # Determinar tipo de dato y rango de normalización original
    bit_depth = 16
    if raw_data.dtype == np.int16:
        bit_depth = 16
        norm_factor = 32768.0
        float_data = raw_data.astype(np.float32) / norm_factor
    elif raw_data.dtype == np.int32:
        bit_depth = 32
        norm_factor = 2147483648.0
        float_data = raw_data.astype(np.float32) / norm_factor
    elif raw_data.dtype == np.uint8:
        bit_depth = 8
        float_data = (raw_data.astype(np.float32) - 128.0) / 128.0
    elif raw_data.dtype == np.float32 or raw_data.dtype == np.float64:
        bit_depth = 32
        float_data = raw_data.astype(np.float32)
    else:
        # Fallback genérico
        norm_factor = float(np.max(np.abs(raw_data))) or 1.0
        float_data = raw_data.astype(np.float32) / norm_factor

    # Si es estéreo o multicanal, mezclar promediando canales a mono
    if float_data.ndim > 1:
        float_data = np.mean(float_data, axis=1)

    # Evitar saturación por redondeo
    float_data = np.clip(float_data, -1.0, 1.0)
    duration = float(len(float_data) / sr)

    metadata = {
        "source_file": filepath,
        "original_dtype": str(raw_data.dtype),
        "peak_amplitude": float(np.max(np.abs(float_data))),
        "rms_energy": float(np.sqrt(np.mean(float_data ** 2))),
    }

    return AudioSignal(
        samples=float_data,
        sample_rate=sr,
        bit_depth=bit_depth,
        duration=duration,
        filename=os.path.abspath(filepath),
        metadata=metadata
    )


def save_wav(filepath: str, signal: AudioSignal, bit_depth: int = 16) -> str:
    """
    Exporta un AudioSignal a un archivo WAV PCM estándar compatible con cualquier reproductor.
    
    Args:
        filepath (str): Ruta de destino para guardar el archivo .wav
        signal (AudioSignal): Señal de audio a guardar.
        bit_depth (int): 16 (int16 estándar) o 32 (float32).
        
    Returns:
        str: Ruta absoluta del archivo creado.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    samples = np.clip(signal.samples, -1.0, 1.0)
    
    if bit_depth == 16:
        pcm_data = (samples * 32767.0).astype(np.int16)
        wavfile.write(filepath, signal.sample_rate, pcm_data)
    elif bit_depth == 32:
        wavfile.write(filepath, signal.sample_rate, samples.astype(np.float32))
    elif bit_depth == 8:
        pcm_data = ((samples + 1.0) * 127.5).astype(np.uint8)
        wavfile.write(filepath, signal.sample_rate, pcm_data)
    else:
        raise ValueError(f"Profundidad de bits {bit_depth} no soportada directamente. Use 8, 16 o 32.")

    return os.path.abspath(filepath)


def play_audio(audio_input: AudioSignal | str, async_play: bool = False) -> bool:
    """
    Reproduce una señal de audio utilizando los controladores nativos del sistema operativo.
    En Windows utiliza `winsound` (cero dependencias externas).
    
    Args:
        audio_input: Instancia de AudioSignal o ruta de archivo WAV.
        async_play: Si True, reproduce en segundo plano; si False, espera a terminar.
        
    Returns:
        bool: True si la reproducción fue exitosa.
    """
    # Si recibimos un AudioSignal, guardamos en un archivo temporal
    temp_file = None
    if isinstance(audio_input, AudioSignal):
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"playback_temp_{int(time.time()*1000)}.wav")
        save_wav(temp_file, audio_input, bit_depth=16)
        target_path = temp_file
    else:
        target_path = audio_input

    if not os.path.exists(target_path):
        print(f"[play_audio] Error: El archivo {target_path} no existe.")
        return False

    current_os = platform.system()
    try:
        if current_os == "Windows":
            import winsound
            flags = winsound.SND_FILENAME
            if async_play:
                flags |= winsound.SND_ASYNC
            winsound.PlaySound(target_path, flags)
            return True
        else:
            # En Linux / macOS intentar con sounddevice si está instalado, o comandos estándar
            try:
                import sounddevice as sd
                sr, data = wavfile.read(target_path)
                sd.play(data, sr)
                if not async_play:
                    sd.wait()
                return True
            except ImportError:
                # Comandos de consola según OS
                if current_os == "Darwin":
                    os.system(f"afplay '{target_path}' {'&' if async_play else ''}")
                else:
                    os.system(f"aplay '{target_path}' {'&' if async_play else ''}")
                return True
    except Exception as e:
        print(f"[play_audio] Advertencia al reproducir audio: {e}")
        return False
    finally:
        # Si fue temporal sincrónico, se puede limpiar
        if temp_file and not async_play and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


def record_voice_wav(filepath: str, duration: float = 3.5, sample_rate: int = 16000) -> AudioSignal:
    """
    Graba una nota de voz corta (duración recomendada: 2 a 5 segundos) y la almacena en WAV.
    Si la librería 'sounddevice' no se encuentra disponible en el entorno o no hay micrófono
    conectado, genera automáticamente una frase sintética de voz acústicamente realista
    (formantes de voz humana en banda vocal 200 Hz - 3.5 kHz) para asegurar que el pipeline
    y los colaboradores puedan trabajar sin bloqueos de hardware.
    
    Args:
        filepath (str): Ruta donde se guardará el archivo WAV grabado.
        duration (float): Duración en segundos (default: 3.5s).
        sample_rate (int): Frecuencia de muestreo (default: 16000 Hz, estándar para voz).
        
    Returns:
        AudioSignal: Señal capturada o sintetizada lista para análisis.
    """
    if duration < 1.0 or duration > 10.0:
        raise ValueError("La duración debe estar comprendida entre 1.0 y 10.0 segundos (recomendado: 2-5s).")

    try:
        import sounddevice as sd
        print(f"\n[Microfono] Iniciando grabacion de {duration:.1f} segundos a {sample_rate} Hz...")
        print(">> Hable ahora (diga una frase corta, ej. 'Universidad Tecnologica de Pereira - Comunicaciones')...")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        print("[Microfono] Grabacion finalizada con exito.")
        samples = recording.flatten()
        
        # Normalizar para aprovechar el rango dinamico
        peak = np.max(np.abs(samples))
        if peak > 1e-4:
            samples = samples / peak * 0.90
            
    except (ImportError, Exception) as exc:
        print(f"\n[Aviso Grabacion] No se pudo acceder a 'sounddevice' o microfono ({exc}).")
        print(">> Generando frase acustica sintetica representativa ('Voz Humana: Comunicaciones Uno')...")
        samples = generate_synthetic_speech_phrase(duration=duration, sample_rate=sample_rate)

    sig = AudioSignal(
        samples=samples,
        sample_rate=sample_rate,
        bit_depth=16,
        duration=duration,
        filename=os.path.abspath(filepath)
    )
    save_wav(filepath, sig, bit_depth=16)
    print(f"[Guardado] Audio almacenado en: {filepath}")
    return sig


def generate_synthetic_speech_phrase(duration: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Genera un modelo acústico sintético de voz humana con tres formantes clásicos
    (F1 = 500 Hz, F2 = 1500 Hz, F3 = 2500 Hz), modulación glotal de tono (Pitch F0 ~ 130 Hz),
    envolvente fonética de 3 sílabas ('Co-mu-ni-ca-cio-nes') y componentes no sonoros (sibilancias).
    Útil para pruebas automatizadas y ambientes CI/CD o colaboradores sin micrófono.
    """
    num_samples = int(duration * sample_rate)
    t = np.linspace(0.0, duration, num_samples, endpoint=False)
    
    # Frecuencia fundamental glotal F0 con inflexión entonacional
    f0 = 125.0 + 15.0 * np.sin(2 * np.pi * 0.8 * t)
    phase_glottal = 2 * np.pi * np.cumsum(f0) / sample_rate
    glottal_source = 0.6 * np.sin(phase_glottal) + 0.3 * np.sin(2 * phase_glottal) + 0.15 * np.sin(3 * phase_glottal)
    
    # Formantes vocales (F1 ~ 550 Hz, F2 ~ 1600 Hz, F3 ~ 2400 Hz) con resonancias
    f1 = 550.0
    f2 = 1600.0
    f3 = 2400.0
    vowel_tract = (
        0.55 * np.sin(2 * np.pi * f1 * t) +
        0.30 * np.sin(2 * np.pi * f2 * t) +
        0.15 * np.sin(2 * np.pi * f3 * t)
    )
    
    # Convolución implícita: modulación de la fuente por el tracto vocal
    voiced = glottal_source * (0.7 + 0.3 * vowel_tract)
    
    # Envolvente silábica (apertura y cierre de boca simulando 5 sílabas)
    envelope = np.zeros_like(t)
    num_syllables = 5
    syllable_duration = duration / num_syllables
    for i in range(num_syllables):
        t_start = i * syllable_duration + 0.05
        t_end = (i + 1) * syllable_duration - 0.05
        mask = (t >= t_start) & (t <= t_end)
        t_local = (t[mask] - t_start) / (t_end - t_start)
        envelope[mask] = np.sin(np.pi * t_local) ** 2

    # Componente fricativo no sonoro (ruido de aire de fonemas sordos e.g. /s/)
    noise = np.random.normal(0, 0.08, num_samples)
    # Filtro paso-altos suave para la sibilancia
    fricative = np.convolve(noise, [0.5, -0.5], mode='same') * envelope
    
    speech = (voiced * envelope) + 0.2 * fricative
    
    # Normalización al 85% de la escala completa
    max_val = np.max(np.abs(speech)) or 1.0
    speech = (speech / max_val * 0.85).astype(np.float32)
    return speech
