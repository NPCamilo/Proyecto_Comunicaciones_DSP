"""
Módulo de Modulación - Stubs y Guía de Implementación para Colaborador 1 (Fase 2)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I

ESTE MÓDULO CORRESPONDE AL PUNTO 4 DEL PROYECTO:
"4. Modulación:
    - Aplicar una técnica de modulación (AM, FM, ASK, FSK, PSK, QAM, GFSK, MFSK).
    - Mostrar la señal modulada gráficamente.
    - Permitir escuchar el resultado de la señal modulada."
"""

import warnings
from typing import Optional, Tuple, Dict, Any
import numpy as np
import scipy.signal as signal_proc
import matplotlib.pyplot as plt
from ..core.base import AudioSignal, DigitalStream, ModulatedSignal, BaseModulator


class AMModulator(BaseModulator):
    """
    Modulador de Amplitud Analógica (AM Convencional / DSB-FC y DSB-SC).
    
    Ecuación General DSB-FC (Doble Banda Lateral con Portadora Completa):
        s_AM(t) = [A_c + m(t)] * cos(2 * pi * f_c * t)
        
    Donde:
        - m(t) es la señal de mensaje (audio en banda base normalizado).
        - A_c es la amplitud de la portadora.
        - f_c es la frecuencia portadora (Hz).
        - mu = max|m(t)| / A_c es el índice de modulación (profundidad de modulación).
        
    Criterio de No Sobremodulación:
        Para evitar distorsión de la envolvente e inversión de fase:
        mu = max|m(t)| / A_c <= 1.0 (o mod_index <= 1.0)
    """

    def __init__(
        self,
        carrier_freq: float = 3000.0,
        mod_index: Optional[float] = 0.8,
        carrier_amp: Optional[float] = None,
        am_type: str = "DSB-FC",
        target_sample_rate: Optional[int] = None,
        normalize_output: bool = True
    ):
        """
        Inicializa el modulador de amplitud AM.
        
        Args:
            carrier_freq (float): Frecuencia de la portadora fc en Hz (default: 3000 Hz, audible).
            mod_index (Optional[float]): Índice de modulación mu deseado (e.g., 0.8 para 80%).
            carrier_amp (Optional[float]): Amplitud Ac explícita. Si se suministra, calcula mu = peak / Ac.
            am_type (str): Tipo de AM: 'DSB-FC' (convencional con portadora) o 'DSB-SC' (portadora suprimida).
            target_sample_rate (Optional[int]): Tasa de muestreo de simulación. Si es None, garantiza
                                                fs_sim >= 4 * fc para prevenir aliasing numérico.
            normalize_output (bool): Si es True, escala la señal resultante en [-1.0, 1.0] para
                                     evitar saturación auditiva y compatibilidad DAC.
        """
        if carrier_freq <= 0:
            raise ValueError(f"La frecuencia portadora carrier_freq debe ser > 0 (recibido: {carrier_freq}).")
            
        if mod_index is not None and mod_index <= 0:
            raise ValueError(f"El índice de modulación mod_index debe ser > 0 (recibido: {mod_index}).")
            
        if carrier_amp is not None and carrier_amp <= 0:
            raise ValueError(f"La amplitud de portadora carrier_amp debe ser > 0 (recibido: {carrier_amp}).")

        if am_type.upper() not in ("DSB-FC", "DSB-SC"):
            raise ValueError(f"Tipo am_type '{am_type}' no soportado. Use 'DSB-FC' o 'DSB-SC'.")

        self.carrier_freq = float(carrier_freq)
        self.mod_index = float(mod_index) if mod_index is not None else None
        self.carrier_amp = float(carrier_amp) if carrier_amp is not None else None
        self.am_type = am_type.upper()
        self.target_sample_rate = target_sample_rate
        self.normalize_output = normalize_output

    def check_overmodulation(self, audio: AudioSignal) -> Tuple[bool, float, float]:
        """
        Evalúa si la combinación de la señal de mensaje y la configuración de portadora
        generará sobremodulación (mu > 1.0).
        
        Args:
            audio (AudioSignal): Señal de entrada.
            
        Returns:
            Tuple[bool, float, float]: (is_overmodulated, mu_calculado, Ac_calculado)
        """
        peak_m = float(np.max(np.abs(audio.samples)))
        if peak_m < 1e-9:
            peak_m = 1.0

        if self.carrier_amp is not None:
            ac = self.carrier_amp
            mu = peak_m / ac
        elif self.mod_index is not None:
            mu = self.mod_index
            ac = peak_m / mu
        else:
            mu = 0.8
            ac = peak_m / mu

        is_over = bool(mu > 1.0001)
        return is_over, float(mu), float(ac)

    def modulate(self, audio: AudioSignal, **kwargs) -> ModulatedSignal:
        """
        Ejecuta la modulación de amplitud sobre la señal de audio banda base.
        
        Args:
            audio (AudioSignal): Señal de entrada normalizada.
            **kwargs: Parámetros opcionales para sobreescribir configuración de instancia:
                      - 'carrier_freq': float
                      - 'mod_index': float
                      - 'carrier_amp': float
                      - 'am_type': str ('DSB-FC' o 'DSB-SC')
                      - 'target_sample_rate': int
                      
        Returns:
            ModulatedSignal: Objeto con la señal pasabanda modulada, portadora y metadatos.
        """
        if not isinstance(audio, AudioSignal):
            raise TypeError(f"Se esperaba una instancia de AudioSignal, recibido: {type(audio)}")

        fc = float(kwargs.get("carrier_freq", self.carrier_freq))
        am_type = str(kwargs.get("am_type", self.am_type)).upper()
        target_fs = kwargs.get("target_sample_rate", self.target_sample_rate)

        m = audio.samples
        fs_orig = audio.sample_rate

        # 1. Asegurar tasa de muestreo adecuada para evitar aliasing en portadora (fs >= 4 * fc)
        min_required_fs = int(np.ceil(4 * fc))
        if target_fs is not None:
            fs_sim = int(target_fs)
        elif fs_orig < min_required_fs:
            fs_sim = max(min_required_fs, 32000)
        else:
            fs_sim = fs_orig

        # Remuestrear si la simulación requiere mayor frecuencia
        if fs_sim != fs_orig:
            new_num_samples = int(round(len(m) * fs_sim / fs_orig))
            m_sim = signal_proc.resample(m, new_num_samples).astype(np.float32)
            t_sim = np.linspace(0.0, len(m) / fs_orig, new_num_samples, endpoint=False, dtype=np.float32)
            resampled = True
        else:
            m_sim = m
            t_sim = audio.time_vector
            resampled = False

        # 2. Análisis de amplitud pico y cálculo de Ac e índice mu
        peak_m = float(np.max(np.abs(m_sim)))
        if peak_m < 1e-9:
            peak_m = 1.0  # Evitar división por cero en señales silenciosas

        override_amp = kwargs.get("carrier_amp", self.carrier_amp)
        override_idx = kwargs.get("mod_index", self.mod_index)

        if override_amp is not None:
            ac = float(override_amp)
            mu = float(peak_m / ac)
        elif override_idx is not None:
            mu = float(override_idx)
            ac = float(peak_m / mu)
        else:
            mu = 0.8
            ac = float(peak_m / mu)

        # 3. Verificación rigurosa del criterio de sobremodulación (mu <= 1.0)
        is_overmodulated = bool(mu > 1.0001 and am_type == "DSB-FC")
        if is_overmodulated:
            warnings.warn(
                f"[AMModulator] Alerta de Sobremodulación: mu = {mu:.3f} > 1.0 (Ac = {ac:.3f}, V_peak = {peak_m:.3f}). "
                f"La envolvente [Ac + m(t)] cruzará por cero generando inversión de fase "
                f"y distorsión no lineal al demodular por envolvente.",
                UserWarning,
                stacklevel=2
            )

        # 4. Generación de la onda portadora y modulación
        carrier = np.cos(2 * np.pi * fc * t_sim).astype(np.float32)

        if am_type == "DSB-FC":
            # AM Convencional: s(t) = [Ac + m(t)] * cos(2*pi*fc*t)
            envelope = ac + m_sim
            s_am = envelope * carrier
            p_carrier = float(0.5 * (ac ** 2))
            p_message = float(np.mean(m_sim ** 2))
            p_sidebands = float(0.5 * p_message)
            total_power = p_carrier + p_sidebands
            efficiency = float((p_sidebands / total_power) * 100.0) if total_power > 0 else 0.0
            env_min = float(np.min(envelope))
            env_max = float(np.max(envelope))
        else:
            # AM DSB-SC (Portadora Suprimida): s(t) = m(t) * cos(2*pi*fc*t)
            envelope = np.abs(m_sim)
            s_am = m_sim * carrier
            ac = 0.0
            p_carrier = 0.0
            p_sidebands = float(0.5 * np.mean(m_sim ** 2))
            total_power = p_sidebands
            efficiency = 100.0
            mu = float("inf")
            is_overmodulated = False
            env_min = float(np.min(m_sim))
            env_max = float(np.max(m_sim))

        # 5. Normalización para reproducción y compatibilidad de rango
        if self.normalize_output:
            max_val = float(np.max(np.abs(s_am)))
            if max_val > 1e-9:
                s_am_out = (s_am / max_val * 0.95).astype(np.float32)
            else:
                s_am_out = s_am.astype(np.float32)
        else:
            s_am_out = s_am.astype(np.float32)

        metadata: Dict[str, Any] = {
            "am_type": f"AM-{am_type}",
            "carrier_freq": fc,
            "carrier_amplitude": ac,
            "mod_index": mu,
            "is_overmodulated": is_overmodulated,
            "peak_message_amplitude": peak_m,
            "envelope_min": env_min,
            "envelope_max": env_max,
            "efficiency_percent": efficiency,
            "carrier_power": p_carrier,
            "sideband_power": p_sidebands,
            "total_power": total_power,
            "resampled": resampled,
            "original_sample_rate": fs_orig,
            "simulation_sample_rate": fs_sim,
        }

        return ModulatedSignal(
            samples=s_am_out,
            carrier_freq=fc,
            sampling_rate=fs_sim,
            modulation_type=f"AM-{am_type}",
            is_digital=False,
            metadata=metadata
        )


class FMModulator(BaseModulator):
    """
    Modulador de Frecuencia Analógica (FM de Banda Angosta y Banda Ancha).
    
    Ecuación General de FM:
        s_FM(t) = A_c * cos(theta(t))
        theta(t) = 2 * pi * f_c * t + 2 * pi * k_f * integral_0^t m(tau) dtau
        
    Donde:
        - m(t) es la señal de audio en banda base normalizada.
        - A_c es la amplitud de la portadora.
        - f_c es la frecuencia de la portadora (Hz).
        - k_f es la constante de desviación/sensibilidad en frecuencia (Hz / Voltio).
        - Desviación de frecuencia de cresta: Delta_f = k_f * max|m(t)| (Hz).
        - Frecuencia instantánea: f_i(t) = f_c + k_f * m(t).
        - Índice de modulación beta: beta = Delta_f / W, donde W es el ancho de banda del mensaje.
        - Ancho de banda por Regla de Carson: B_FM = 2 * (Delta_f + W) = 2 * W * (beta + 1).
    """

    def __init__(
        self,
        carrier_freq: float = 3000.0,
        freq_dev: Optional[float] = 1000.0,
        mod_index_beta: Optional[float] = None,
        kf: Optional[float] = None,
        carrier_amp: float = 1.0,
        audio_bandwidth: Optional[float] = None,
        target_sample_rate: Optional[int] = None,
        normalize_output: bool = True
    ):
        """
        Inicializa el modulador de frecuencia FM.
        
        Args:
            carrier_freq (float): Frecuencia portadora central fc en Hz (default: 3000 Hz).
            freq_dev (Optional[float]): Desviación máxima de frecuencia Delta_f en Hz (default: 1000 Hz).
            mod_index_beta (Optional[float]): Índice de modulación beta deseado. Si se suministra,
                                             Delta_f = beta * W.
            kf (Optional[float]): Sensibilidad de frecuencia k_f en Hz/V. Si se suministra,
                                  Delta_f = k_f * max|m(t)|.
            carrier_amp (float): Amplitud de portadora Ac (default: 1.0).
            audio_bandwidth (Optional[float]): Ancho de banda de mensaje W en Hz. Si es None,
                                               se estima a partir del espectro del audio.
            target_sample_rate (Optional[int]): Frecuencia de muestreo de simulación. Si es None,
                                                se calcula automáticamente para satisfacer la Regla
                                                de Carson y evitar aliasing espectral.
            normalize_output (bool): Normaliza la amplitud a [-1.0, 1.0] para reproducción DAC.
        """
        if carrier_freq <= 0:
            raise ValueError(f"carrier_freq debe ser > 0 (recibido: {carrier_freq}).")
        if carrier_amp <= 0:
            raise ValueError(f"carrier_amp debe ser > 0 (recibido: {carrier_amp}).")
        if freq_dev is not None and freq_dev <= 0:
            raise ValueError(f"freq_dev debe ser > 0 (recibido: {freq_dev}).")
        if mod_index_beta is not None and mod_index_beta <= 0:
            raise ValueError(f"mod_index_beta debe ser > 0 (recibido: {mod_index_beta}).")
        if kf is not None and kf <= 0:
            raise ValueError(f"kf debe ser > 0 (recibido: {kf}).")

        self.carrier_freq = float(carrier_freq)
        self.freq_dev = float(freq_dev) if freq_dev is not None else None
        self.mod_index_beta = float(mod_index_beta) if mod_index_beta is not None else None
        self.kf = float(kf) if kf is not None else None
        self.carrier_amp = float(carrier_amp)
        self.audio_bandwidth = float(audio_bandwidth) if audio_bandwidth is not None else None
        self.target_sample_rate = target_sample_rate
        self.normalize_output = normalize_output

    def get_instantaneous_frequency(self, audio: AudioSignal, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula el vector temporal y la frecuencia instantánea f_i(t) = f_c + k_f * m(t).
        
        Args:
            audio (AudioSignal): Señal de mensaje.
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (tiempo [s], frecuencia instantánea [Hz])
        """
        fc = float(kwargs.get("carrier_freq", self.carrier_freq))
        m = audio.samples
        peak_m = float(np.max(np.abs(m))) or 1.0

        if self.kf is not None:
            kf = self.kf
        elif self.freq_dev is not None:
            kf = self.freq_dev / peak_m
        elif self.mod_index_beta is not None:
            w = self.audio_bandwidth or 3000.0
            kf = (self.mod_index_beta * w) / peak_m
        else:
            kf = 1000.0 / peak_m

        f_inst = fc + kf * m
        return audio.time_vector, f_inst

    def modulate(self, audio: AudioSignal, **kwargs) -> ModulatedSignal:
        """
        Ejecuta la modulación de frecuencia (FM) sobre la señal de audio banda base.
        
        Args:
            audio (AudioSignal): Señal de entrada de audio normalizada.
            **kwargs: Parámetros opcionales para sobreescribir la configuración:
                      - 'carrier_freq': float
                      - 'freq_dev': float
                      - 'mod_index_beta': float
                      - 'kf': float
                      - 'carrier_amp': float
                      - 'target_sample_rate': int
                      
        Returns:
            ModulatedSignal: Objeto con la señal FM pasabanda y metadatos de modulación.
        """
        if not isinstance(audio, AudioSignal):
            raise TypeError(f"Se esperaba una instancia de AudioSignal, recibido: {type(audio)}")

        fc = float(kwargs.get("carrier_freq", self.carrier_freq))
        ac = float(kwargs.get("carrier_amp", self.carrier_amp))
        target_fs = kwargs.get("target_sample_rate", self.target_sample_rate)

        m = audio.samples
        fs_orig = audio.sample_rate
        peak_m = float(np.max(np.abs(m)))
        if peak_m < 1e-9:
            peak_m = 1.0

        # 1. Determinar ancho de banda de mensaje W (f_max efectivo)
        w = kwargs.get("audio_bandwidth", self.audio_bandwidth)
        if w is None:
            w = audio.metadata.get("f_max_effective_hz", None)
            if w is None or w <= 0:
                from ..core.analyzer import compute_spectrum, estimate_max_frequency
                freqs, mag_lin, _ = compute_spectrum(audio)
                w = estimate_max_frequency(freqs, mag_lin, energy_threshold=0.99)
                if w < 100.0:
                    w = 3000.0
        w = float(w)

        # 2. Determinar constante de sensibilidad kf y desviación Delta_f
        override_beta = kwargs.get("mod_index_beta", self.mod_index_beta)
        override_dev = kwargs.get("freq_dev", self.freq_dev)
        override_kf = kwargs.get("kf", self.kf)

        if override_beta is not None:
            beta = float(override_beta)
            delta_f = beta * w
            kf = delta_f / peak_m
        elif override_dev is not None:
            delta_f = float(override_dev)
            kf = delta_f / peak_m
            beta = delta_f / w if w > 0 else 1.0
        elif override_kf is not None:
            kf = float(override_kf)
            delta_f = kf * peak_m
            beta = delta_f / w if w > 0 else 1.0
        else:
            delta_f = 1000.0
            kf = delta_f / peak_m
            beta = delta_f / w if w > 0 else 1.0

        # Advertencia si la desviación de frecuencia causa frecuencias instantáneas negativas
        if delta_f >= fc:
            warnings.warn(
                f"[FMModulator] Advertencia: Delta_f ({delta_f:.1f} Hz) >= fc ({fc:.1f} Hz). "
                f"La frecuencia instantánea mínima será negativa ({fc - delta_f:.1f} Hz), "
                f"lo cual puede inducir aliasing espectral por inversión de fase en banda base.",
                UserWarning,
                stacklevel=2
            )

        # 3. Ancho de banda de Carson y tasa de simulación mínima anti-aliasing
        # B_Carson = 2 * (Delta_f + W)
        carson_bw = 2.0 * (delta_f + w)
        max_freq_component = fc + delta_f + w
        min_required_fs = int(np.ceil(max(4.0 * fc, 2.0 * max_freq_component)))

        if target_fs is not None:
            fs_sim = int(target_fs)
        elif fs_orig < min_required_fs:
            fs_sim = max(min_required_fs, 32000)
        else:
            fs_sim = fs_orig

        # Remuestrear si la simulación requiere mayor resolución
        if fs_sim != fs_orig:
            new_num_samples = int(round(len(m) * fs_sim / fs_orig))
            m_sim = signal_proc.resample(m, new_num_samples).astype(np.float32)
            t_sim = np.linspace(0.0, len(m) / fs_orig, new_num_samples, endpoint=False, dtype=np.float32)
            resampled = True
        else:
            m_sim = m
            t_sim = audio.time_vector
            resampled = False

        # 4. Integración temporal de la señal de mensaje: integral_0^t m(tau) dtau
        # Se emplea la regla del trapecio acumulativa para alta precisión
        try:
            from scipy.integrate import cumulative_trapezoid
            integral_m = cumulative_trapezoid(m_sim, dx=1.0 / fs_sim, initial=0.0).astype(np.float32)
        except ImportError:
            integral_m = (np.cumsum(m_sim) / fs_sim).astype(np.float32)

        # 5. Generación de fase instantánea y modulación FM
        # theta(t) = 2*pi*fc*t + 2*pi*kf*integral_m(t)
        phase_carrier = 2.0 * np.pi * fc * t_sim
        phase_modulation = 2.0 * np.pi * kf * integral_m
        theta = phase_carrier + phase_modulation

        s_fm = ac * np.cos(theta).astype(np.float32)

        # 6. Frecuencia instantánea resultante
        f_inst = fc + kf * m_sim
        min_f_inst = float(np.min(f_inst))
        max_f_inst = float(np.max(f_inst))

        # Clasificación entre banda angosta y banda ancha
        fm_regime = "NBFM" if beta < 0.5 else "WBFM"

        # 7. Normalización para reproducción y salida
        if self.normalize_output:
            max_val = float(np.max(np.abs(s_fm)))
            if max_val > 1e-9:
                s_fm_out = (s_fm / max_val * 0.95).astype(np.float32)
            else:
                s_fm_out = s_fm.astype(np.float32)
        else:
            s_fm_out = s_fm.astype(np.float32)

        metadata: Dict[str, Any] = {
            "modulation_type": f"FM-{fm_regime}",
            "carrier_freq": fc,
            "carrier_amplitude": ac,
            "freq_deviation_hz": float(delta_f),
            "freq_sensitivity_kf": float(kf),
            "modulation_index_beta": float(beta),
            "message_bandwidth_w_hz": float(w),
            "bandwidth_carson_hz": float(carson_bw),
            "fm_regime": fm_regime,
            "min_instantaneous_freq": min_f_inst,
            "max_instantaneous_freq": max_f_inst,
            "resampled": resampled,
            "original_sample_rate": fs_orig,
            "simulation_sample_rate": fs_sim,
        }

        return ModulatedSignal(
            samples=s_fm_out,
            carrier_freq=fc,
            sampling_rate=fs_sim,
            modulation_type=f"FM-{fm_regime}",
            is_digital=False,
            metadata=metadata
        )


class DigitalShiftKeyingModulator(BaseModulator):
    """
    Modulador Digital por Desplazamiento (ASK / FSK / BPSK).
    Opera directamente sobre el DigitalStream generado en la Fase 1 o sobre un array de bits.
    
    Técnicas implementadas:
      1. ASK (Amplitude Shift Keying / OOK):
         - Bit = 1: s_1(t) = A_1 * cos(2 * pi * f_c * t)
         - Bit = 0: s_0(t) = A_0 * cos(2 * pi * f_c * t) (e.g., A_0 = 0 en OOK)
         
      2. FSK (Binary Frequency Shift Keying - BFSK):
         - Bit = 1: s_1(t) = A_1 * cos(2 * pi * f_1 * t + phi)
         - Bit = 0: s_0(t) = A_0 * cos(2 * pi * f_0 * t + phi)
         Soporta fase continua (CPFSK) para evitar saltos abruptos y mejorar el espectro.
         
      3. BPSK (Binary Phase Shift Keying):
         - Bit = 1: s_1(t) = A * cos(2 * pi * f_c * t)
         - Bit = 0: s_0(t) = A * cos(2 * pi * f_c * t + pi) = -A * cos(2 * pi * f_c * t)
    """

    def __init__(
        self,
        mod_type: str = "ASK",
        carrier_freq: float = 2000.0,
        samples_per_symbol: int = 16,
        sampling_rate: Optional[int] = None,
        bit_rate: Optional[float] = None,
        f0: Optional[float] = None,
        f1: Optional[float] = None,
        a0: float = 0.0,
        a1: float = 1.0,
        continuous_phase: bool = True,
        normalize_output: bool = True
    ):
        """
        Inicializa el modulador digital pasabanda.
        
        Args:
            mod_type (str): 'ASK', 'FSK' o 'BPSK' (case-insensitive).
            carrier_freq (float): Frecuencia de portadora principal fc en Hz (default: 2000 Hz).
            samples_per_symbol (int): Número de muestras discretas por bit/símbolo (default: 16).
            sampling_rate (Optional[int]): Frecuencia de muestreo de simulación fs. Si es None,
                                           se calcula automáticamente como max(32000, 4 * f_max).
            bit_rate (Optional[float]): Tasa binaria Rb en bits/segundo. Si se define, ajusta fs o samples_per_symbol.
            f0 (Optional[float]): Frecuencia para bit 0 en FSK (default: fc - 500 Hz).
            f1 (Optional[float]): Frecuencia para bit 1 en FSK (default: fc + 500 Hz).
            a0 (float): Amplitud de portadora para bit 0 (default: 0.0 para OOK en ASK; 1.0 en FSK).
            a1 (float): Amplitud de portadora para bit 1 (default: 1.0).
            continuous_phase (bool): Si es True en FSK, genera fase continua (CPFSK).
            normalize_output (bool): Escala la señal a [-1.0, 1.0] para compatibilidad DAC/audio.
        """
        valid_types = ("ASK", "FSK", "BPSK")
        mod_upper = mod_type.upper()
        if mod_upper not in valid_types:
            raise ValueError(f"Tipo de modulación digital '{mod_type}' no válido. Use {valid_types}.")

        if carrier_freq <= 0:
            raise ValueError(f"carrier_freq debe ser > 0 (recibido: {carrier_freq}).")
        if samples_per_symbol < 2:
            raise ValueError(f"samples_per_symbol debe ser >= 2 (recibido: {samples_per_symbol}).")
        if a1 <= 0:
            raise ValueError(f"La amplitud a1 debe ser > 0 (recibido: {a1}).")
        if a0 < 0:
            raise ValueError(f"La amplitud a0 no puede ser negativa (recibido: {a0}).")

        self.mod_type = mod_upper
        self.carrier_freq = float(carrier_freq)
        self.samples_per_symbol = int(samples_per_symbol)
        self.bit_rate = float(bit_rate) if bit_rate is not None else None
        self.sampling_rate = int(sampling_rate) if sampling_rate is not None else None
        self.continuous_phase = continuous_phase
        self.normalize_output = normalize_output
        self.a0 = float(a0) if mod_upper == "ASK" else (float(a0) if a0 > 0 else 1.0)
        self.a1 = float(a1)

        # Frecuencias para FSK
        if mod_upper == "FSK":
            self.f0 = float(f0) if f0 is not None else max(100.0, self.carrier_freq - 500.0)
            self.f1 = float(f1) if f1 is not None else self.carrier_freq + 500.0
            if self.f0 <= 0 or self.f1 <= 0:
                raise ValueError(f"Las frecuencias FSK f0 y f1 deben ser > 0 (f0={self.f0}, f1={self.f1}).")
            if self.f0 == self.f1:
                warnings.warn(
                    f"[DigitalModulator] f0 ({self.f0} Hz) es igual a f1 ({self.f1} Hz). "
                    "No habrá discriminación frecuencial en FSK.",
                    UserWarning
                )
        else:
            self.f0 = self.carrier_freq
            self.f1 = self.carrier_freq

    def modulate(self, input_data: Any, **kwargs) -> ModulatedSignal:
        """
        Ejecuta la modulación pasabanda digital sobre un DigitalStream o un vector de bits.
        
        Args:
            input_data (Any): Instancia de DigitalStream o ndarray/list con bits binarios (0s y 1s).
            **kwargs: Sobreescrituras opcionales de configuración:
                      - 'mod_type': str
                      - 'carrier_freq': float
                      - 'samples_per_symbol': int
                      - 'f0': float, 'f1': float
                      - 'a0': float, 'a1': float
                      - 'continuous_phase': bool
                      
        Returns:
            ModulatedSignal: Señal modulada pasabanda digital con metadatos.
        """
        # 1. Extraer el bitstream
        if isinstance(input_data, DigitalStream):
            bits = np.asarray(input_data.bitstream, dtype=np.uint8)
        elif isinstance(input_data, (np.ndarray, list, tuple)):
            bits = np.asarray(input_data, dtype=np.uint8).flatten()
        else:
            raise TypeError(
                f"Entrada no soportada: {type(input_data)}. Se esperaba DigitalStream o array de bits binarios."
            )

        if len(bits) == 0:
            raise ValueError("El flujo de bits está vacío. Se requiere al menos un bit.")

        if not np.all((bits == 0) | (bits == 1)):
            raise ValueError("El flujo de bits solo debe contener valores binarios {0, 1}.")

        # 2. Parámetros de simulación y frecuencias
        mod_type = str(kwargs.get("mod_type", self.mod_type)).upper()
        fc = float(kwargs.get("carrier_freq", self.carrier_freq))
        sps = int(kwargs.get("samples_per_symbol", self.samples_per_symbol))
        a0 = float(kwargs.get("a0", self.a0))
        a1 = float(kwargs.get("a1", self.a1))
        cont_phase = bool(kwargs.get("continuous_phase", self.continuous_phase))

        if mod_type == "FSK":
            f0 = float(kwargs.get("f0", self.f0))
            f1 = float(kwargs.get("f1", self.f1))
            max_freq = max(f0, f1, fc)
        else:
            f0 = fc
            f1 = fc
            max_freq = fc

        # 3. Determinar frecuencia de muestreo de simulación fs
        # Asegurar Nyquist: fs >= 4 * max_freq
        min_fs = int(np.ceil(4.0 * max_freq))
        fs_override = kwargs.get("sampling_rate", self.sampling_rate)
        bit_rate_override = kwargs.get("bit_rate", self.bit_rate)

        if fs_override is not None:
            fs = int(fs_override)
        elif bit_rate_override is not None:
            fs = int(round(bit_rate_override * sps))
            if fs < min_fs:
                fs = max(min_fs, 32000)
                sps = max(2, int(round(fs / bit_rate_override)))
        else:
            fs = max(32000, min_fs)

        # Duración de símbolo y tasa de bits efectiva
        bit_rate = fs / sps
        symbol_duration = sps / fs
        num_bits = len(bits)
        total_samples = num_bits * sps
        t = np.arange(total_samples, dtype=np.float32) / fs

        # 4. Modulación vectorial eficiente
        bit_waveform = np.repeat(bits, sps)

        if mod_type == "ASK":
            # ASK: Bit 1 -> A1 * cos(2*pi*fc*t), Bit 0 -> A0 * cos(2*pi*fc*t)
            amp_waveform = np.where(bit_waveform == 1, a1, a0).astype(np.float32)
            carrier = np.cos(2.0 * np.pi * fc * t).astype(np.float32)
            s_mod = amp_waveform * carrier

        elif mod_type == "FSK":
            # FSK: Bit 1 -> A1 * cos(2*pi*f1*t), Bit 0 -> A0 * cos(2*pi*f0*t)
            freq_waveform = np.where(bit_waveform == 1, f1, f0).astype(np.float32)
            amp_waveform = np.where(bit_waveform == 1, a1, a0).astype(np.float32)
            
            if cont_phase:
                # Fase continua (CPFSK): theta(t) = 2*pi * integral f(tau) dtau
                phase = (2.0 * np.pi * np.cumsum(freq_waveform) / fs).astype(np.float32)
                s_mod = amp_waveform * np.cos(phase).astype(np.float32)
            else:
                # Fase discontinua con base de tiempo local por símbolo
                t_local = np.tile(np.arange(sps, dtype=np.float32) / fs, num_bits)
                s_mod = amp_waveform * np.cos(2.0 * np.pi * freq_waveform * t_local).astype(np.float32)

        elif mod_type == "BPSK":
            # BPSK: Bit 1 -> phase = 0, Bit 0 -> phase = pi
            phase_offset = np.where(bit_waveform == 1, 0.0, np.pi).astype(np.float32)
            carrier_phase = 2.0 * np.pi * fc * t + phase_offset
            s_mod = a1 * np.cos(carrier_phase).astype(np.float32)

        else:
            raise ValueError(f"Esquema de modulación '{mod_type}' no implementado.")

        # 5. Normalización para reproducción y salida
        if self.normalize_output:
            peak = float(np.max(np.abs(s_mod)))
            if peak > 1e-9:
                s_mod_out = (s_mod / peak * 0.95).astype(np.float32)
            else:
                s_mod_out = s_mod.astype(np.float32)
        else:
            s_mod_out = s_mod.astype(np.float32)

        metadata: Dict[str, Any] = {
            "digital_modulation_type": mod_type,
            "total_bits": num_bits,
            "samples_per_symbol": sps,
            "bit_rate_bps": float(bit_rate),
            "symbol_duration_ms": float(symbol_duration * 1000.0),
            "carrier_freq": fc,
            "f0_hz": f0 if mod_type == "FSK" else fc,
            "f1_hz": f1 if mod_type == "FSK" else fc,
            "a0": a0,
            "a1": a1,
            "continuous_phase": cont_phase if mod_type == "FSK" else False,
            "average_power": float(np.mean(s_mod_out ** 2)),
            "first_16_bits": "".join(str(b) for b in bits[:16]),
        }

        return ModulatedSignal(
            samples=s_mod_out,
            carrier_freq=fc,
            sampling_rate=fs,
            modulation_type=f"Digital-{mod_type}",
            is_digital=True,
            metadata=metadata
        )


def plot_modulated_signal(modulated: ModulatedSignal, zoom_ms: float = 10.0,
                          save_path: Optional[str] = None, show: bool = False) -> plt.Figure:
    """
    Grafica la señal modulada en tiempo (con zoom para ver oscilaciones de portadora)
    y en frecuencia (mostrando los lóbulos laterales de modulación).
    """
    fs = modulated.sampling_rate
    samples = modulated.samples
    t = modulated.time_vector
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')
    
    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, color='#30363d', linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    # Zoom temporal
    num_zoom = min(int(zoom_ms * 1e-3 * fs), len(samples))
    ax1.plot(t[:num_zoom] * 1000.0, samples[:num_zoom], color='#79c0ff', linewidth=1.1)
    ax1.set_title(f"Señal Modulada {modulated.modulation_type} - Zoom Temporal ({zoom_ms} ms)",
                  color='#f0f6fc', fontsize=11, fontweight='bold')
    ax1.set_xlabel("Tiempo [ms]", color='#c9d1d9')
    ax1.set_ylabel("Amplitud", color='#c9d1d9')

    # Espectro
    fft_vals = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
    freqs = np.fft.rfftfreq(len(samples), d=1.0 / fs)
    fft_db = 20 * np.log10(np.clip(fft_vals / (np.max(fft_vals) + 1e-12), 1e-6, 1.0))
    ax2.plot(freqs, fft_db, color='#d2a8ff', linewidth=1.0)
    ax2.axvline(modulated.carrier_freq, color='#f85149', linestyle='--',
                label=f'Portadora fc = {modulated.carrier_freq:.1f} Hz')
    ax2.set_title(f"Densidad Espectral de la Señal Modulada {modulated.modulation_type}",
                  color='#f0f6fc', fontsize=11, fontweight='bold')
    ax2.set_xlabel("Frecuencia [Hz]", color='#c9d1d9')
    ax2.set_ylabel("Magnitud [dBFS]", color='#c9d1d9')
    ax2.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc')

    if save_path:
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    if show:
        plt.show()

    return fig
