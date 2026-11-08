"""
Base DSP Module - Contratos, Tipos de Datos e Interfaces Abstractas
Proyecto: Cadena Integral de Comunicaciones: Audio DSP, Muestreo, Modulación, Demodulación y Reconstrucción
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class AudioSignal:
    """
    Contenedor estándar inmutable para señales de audio normalizadas en banda base.
    
    Atributos:
        samples (np.ndarray): Muestras de audio normalizadas en rango [-1.0, 1.0], 1D (mono).
        sample_rate (int): Frecuencia de muestreo (Hz), e.g., 44100, 16000, 8000.
        bit_depth (int): Profundidad de bits original (e.g., 16 bits PCM).
        duration (float): Duración en segundos.
        filename (Optional[str]): Ruta del archivo fuente si aplica.
        metadata (Dict[str, Any]): Metadatos de análisis (RMS, Vpico, f_max, etc.).
    """
    samples: np.ndarray
    sample_rate: int
    bit_depth: int = 16
    duration: float = 0.0
    filename: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Asegurar tipo de dato flotante y dimensión 1D
        self.samples = np.asarray(self.samples, dtype=np.float32)
        if self.samples.ndim > 1:
            self.samples = np.mean(self.samples, axis=1)  # Mezclar a mono si es multicanal
        
        # Calcular duración automáticamente si no se suministra
        if self.duration <= 0.0 and self.sample_rate > 0:
            self.duration = float(len(self.samples) / self.sample_rate)

    @property
    def num_samples(self) -> int:
        return len(self.samples)

    @property
    def time_vector(self) -> np.ndarray:
        """Retorna el vector temporal continuo equivalente en segundos."""
        return np.linspace(0.0, self.duration, self.num_samples, endpoint=False)


@dataclass
class DigitalStream:
    """
    Representación digital cuantizada (trama binaria y símbolos discretos) de la señal muestreada.
    Base de entrada para modulación digital (ASK, FSK, PSK, QAM).
    """
    bitstream: np.ndarray             # Array 1D de enteros uint8 (0s y 1s)
    quantized_levels: np.ndarray      # Índices discretos enteros [0, 2^b - 1]
    reconstructed_levels: np.ndarray  # Niveles analógicos cuantizados x_q[n]
    bits_per_sample: int              # Resolución 'b' (e.g., 8 bits = 1 Byte, 4 bits, etc.)
    sample_rate: int                  # Frecuencia de muestreo fs usada en la digitalización
    v_min: float                      # Voltaje/amplitud mínima de escala [-1.0]
    v_max: float                      # Voltaje/amplitud máxima de escala [+1.0]
    sqnr_db: float                    # Relación Señal a Ruido de Cuantización medida (dB)
    sqnr_theoretical_db: float        # SQNR teórica (6.02b + 1.76 dB)

    @property
    def total_bits(self) -> int:
        return len(self.bitstream)

    @property
    def total_bytes(self) -> int:
        return int(np.ceil(self.total_bits / 8))

    def to_bytes(self) -> bytes:
        """Empaqueta el array de bits (0s y 1s) en un objeto bytes estándar de Python."""
        # Rellenar con ceros al final si no es múltiplo de 8
        padded_length = int(np.ceil(len(self.bitstream) / 8.0) * 8)
        padded_bits = np.pad(self.bitstream, (0, padded_length - len(self.bitstream)), 'constant')
        byte_chunks = padded_bits.reshape(-1, 8)
        powers_of_two = 1 << np.arange(7, -1, -1, dtype=np.uint8)
        packed_bytes = np.dot(byte_chunks, powers_of_two).astype(np.uint8)
        return packed_bytes.tobytes()

    @staticmethod
    def from_bytes(raw_bytes: bytes, total_bits: int, bits_per_sample: int,
                   sample_rate: int, v_min: float, v_max: float) -> "DigitalStream":
        """Reconstruye un DigitalStream a partir de bytes empaquetados."""
        byte_arr = np.frombuffer(raw_bytes, dtype=np.uint8)
        bits = np.unpackbits(byte_arr)[:total_bits]
        
        # Reconstruir niveles
        num_samples = total_bits // bits_per_sample
        reshaped = bits[:num_samples * bits_per_sample].reshape(num_samples, bits_per_sample)
        powers = 1 << np.arange(bits_per_sample - 1, -1, -1, dtype=np.int32)
        levels = np.dot(reshaped, powers)
        
        step_size = (v_max - v_min) / (2**bits_per_sample - 1)
        recon = v_min + levels.astype(np.float32) * step_size
        
        return DigitalStream(
            bitstream=bits,
            quantized_levels=levels,
            reconstructed_levels=recon,
            bits_per_sample=bits_per_sample,
            sample_rate=sample_rate,
            v_min=v_min,
            v_max=v_max,
            sqnr_db=0.0,
            sqnr_theoretical_db=6.02 * bits_per_sample + 1.76
        )


@dataclass
class ModulatedSignal:
    """
    Contenedor estándar para señales pasabanda moduladas (Analógicas o Digitales).
    """
    samples: np.ndarray               # Muestras moduladas a frecuencia de portadora
    carrier_freq: float               # Frecuencia de portadora fc (Hz)
    sampling_rate: int                # Frecuencia de muestreo de simulación (debe cumplir fs_mod >= 4*fc)
    modulation_type: str              # E.g., 'AM', 'FM', 'ASK', 'FSK', 'BPSK', 'QAM'
    is_digital: bool                  # True si proviene de bits, False si es analógica
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sampling_rate

    @property
    def time_vector(self) -> np.ndarray:
        return np.linspace(0.0, self.duration, len(self.samples), endpoint=False)


@dataclass
class DemodulatedResult:
    """
    Resultado del proceso de demodulación, que entrega la señal analógica recuperada
    o los bits detectados.
    """
    recovered_audio: AudioSignal
    demodulation_type: str
    detected_bits: Optional[np.ndarray] = None
    bit_error_rate: Optional[float] = None  # BER si se compara con bitstream original
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """
    Métricas objetivas de fidelidad entre la señal original y la reconstruida.
    """
    mse: float                        # Error Cuadrático Medio (Mean Squared Error)
    snr_db: float                     # Relación Señal a Ruido (dB)
    psnr_db: float                    # Peak Signal-to-Noise Ratio (dB)
    pearson_corr: float               # Coeficiente de correlación de Pearson [-1.0, 1.0]
    spectral_distortion_db: float     # Distorsión espectral logarítmica promedio


# =====================================================================
# Interfaces Abstractas para Fases de Colaboración
# =====================================================================

class BaseModulator(ABC):
    """Interfaz abstracta que debe implementar el Colaborador 1 en la Fase 2."""
    
    @abstractmethod
    def modulate(self, input_data: Any, carrier_freq: float, **kwargs) -> ModulatedSignal:
        """
        Modula una señal de audio (analógica) o un DigitalStream (digital).
        """
        pass


class BaseDemodulator(ABC):
    """Interfaz abstracta que debe implementar el Colaborador 2 en la Fase 3."""
    
    @abstractmethod
    def demodulate(self, modulated_signal: ModulatedSignal, **kwargs) -> DemodulatedResult:
        """
        Demodula la señal pasabanda recuperando el audio original y/o bitstream.
        """
        pass


class BaseReconstructor(ABC):
    """Interfaz abstracta que debe implementar el Colaborador 3 en la Fase 4."""
    
    @abstractmethod
    def reconstruct(self, samples: np.ndarray, target_rate: int, **kwargs) -> AudioSignal:
        """
        Aplica interpolación Sinc (Whittaker-Shannon) o ZOH con filtrado analógico.
        """
        pass

    @abstractmethod
    def evaluate_fidelity(self, original: AudioSignal, reconstructed: AudioSignal) -> PerformanceMetrics:
        """
        Calcula MSE, SNR, PSNR, correlación de Pearson y distorsión espectral.
        """
        pass
