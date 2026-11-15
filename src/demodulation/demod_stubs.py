import os
import warnings
from typing import Optional, Tuple, Dict, Any, Union
import numpy as np
import scipy.signal as signal_proc
import matplotlib.pyplot as plt

from ..core.base import (
    AudioSignal,
    DigitalStream,
    ModulatedSignal,
    DemodulatedResult,
    BaseDemodulator
)


def compute_pearson_correlation(sig_a: Union[AudioSignal, np.ndarray],
                                sig_b: Union[AudioSignal, np.ndarray]) -> float:
    x = sig_a.samples if isinstance(sig_a, AudioSignal) else np.asarray(sig_a, dtype=np.float64)
    y = sig_b.samples if isinstance(sig_b, AudioSignal) else np.asarray(sig_b, dtype=np.float64)

    if len(x) != len(y) and len(x) > 0 and len(y) > 0:
        y = signal_proc.resample(y, len(x))

    min_len = min(len(x), len(y))
    if min_len < 2:
        return 0.0

    x = x[:min_len].astype(np.float64)
    y = y[:min_len].astype(np.float64)

    vx = x - np.mean(x)
    vy = y - np.mean(y)
    denom = float(np.sqrt(np.sum(vx ** 2) * np.sum(vy ** 2)))
    if denom < 1e-12:
        return 0.0

    return float(np.clip(np.sum(vx * vy) / denom, -1.0, 1.0))


class AMDemodulator(BaseDemodulator):
    VALID_METHODS = ("coherent", "envelope")

    def __init__(
        self,
        method: str = "coherent",
        cutoff_freq: float = 3500.0,
        filter_order: int = 5,
        phase_offset: float = 0.0,
        post_filter_envelope: bool = True,
        restore_original_rate: bool = True,
        normalize_output: bool = True
    ):
        method_clean = method.strip().lower()
        if method_clean not in self.VALID_METHODS:
            raise ValueError(f"Metodo '{method}' no valido. Opciones: {self.VALID_METHODS}.")
        if cutoff_freq <= 0:
            raise ValueError("cutoff_freq debe ser mayor a 0.")
        if filter_order < 1 or filter_order > 12:
            raise ValueError("filter_order debe estar entre 1 y 12.")

        self.method = method_clean
        self.cutoff_freq = float(cutoff_freq)
        self.filter_order = int(filter_order)
        self.phase_offset = float(phase_offset)
        self.post_filter_envelope = bool(post_filter_envelope)
        self.restore_original_rate = bool(restore_original_rate)
        self.normalize_output = bool(normalize_output)

    def _design_lowpass_filter(self, fs: int, cutoff_hz: float, order: int) -> Tuple[np.ndarray, np.ndarray, float]:
        nyq = 0.5 * fs
        effective_cutoff = min(float(cutoff_hz), 0.95 * nyq)
        normal_cutoff = effective_cutoff / nyq
        b, a = signal_proc.butter(order, normal_cutoff, btype="low", analog=False)
        return b, a, effective_cutoff

    def demodulate(self, modulated: ModulatedSignal, **kwargs) -> DemodulatedResult:
        if not isinstance(modulated, ModulatedSignal):
            raise TypeError(f"Se esperaba ModulatedSignal, se recibio: {type(modulated)}")

        method = str(kwargs.get("method", self.method)).strip().lower()
        if method not in self.VALID_METHODS:
            raise ValueError(f"Metodo '{method}' no soportado.")

        cutoff = float(kwargs.get("cutoff_freq", self.cutoff_freq))
        order = int(kwargs.get("filter_order", self.filter_order))
        phi = float(kwargs.get("phase_offset", self.phase_offset))
        reference_audio: Optional[AudioSignal] = kwargs.get("reference_audio", None)

        if cutoff <= 0:
            raise ValueError("cutoff_freq debe ser mayor a 0.")
        if order < 1 or order > 12:
            raise ValueError("filter_order debe estar entre 1 y 12.")

        fs = modulated.sampling_rate
        fc = modulated.carrier_freq
        t = modulated.time_vector
        s = np.asarray(modulated.samples, dtype=np.float64)

        if len(s) == 0:
            raise ValueError("La senal modulada no contiene muestras.")

        safe_cutoff = min(cutoff, 0.95 * fc) if fc > 0 else cutoff
        b, a, effective_cutoff = self._design_lowpass_filter(fs, safe_cutoff, order)

        am_subtype = modulated.metadata.get("am_type", modulated.modulation_type)
        is_overmodulated = bool(modulated.metadata.get("is_overmodulated", False))

        if method == "envelope":
            if "DSB-SC" in str(am_subtype).upper():
                warnings.warn(
                    "Deteccion de envolvente sobre AM-DSB-SC (sin portadora) produce distorsion.",
                    UserWarning,
                    stacklevel=2
                )
            if is_overmodulated:
                warnings.warn(
                    "Senal AM con sobremodulacion (mu > 1.0) detectada en receptor de envolvente.",
                    UserWarning,
                    stacklevel=2
                )

            analytic_signal = signal_proc.hilbert(s)
            envelope = np.abs(analytic_signal)
            dc_level = float(np.mean(envelope))
            demod_raw = envelope - dc_level

            if self.post_filter_envelope and len(demod_raw) > 3 * max(len(a), len(b)):
                demod_filtered = signal_proc.filtfilt(b, a, demod_raw)
                demod_audio = demod_filtered - np.mean(demod_filtered)
            else:
                demod_audio = demod_raw
        else:
            local_oscillator = np.cos(2.0 * np.pi * fc * t + phi)
            mixed = 2.0 * s * local_oscillator

            if len(mixed) > 3 * max(len(a), len(b)):
                filtered = signal_proc.filtfilt(b, a, mixed)
            else:
                filtered = signal_proc.lfilter(b, a, mixed)

            dc_level = float(np.mean(filtered))
            demod_audio = filtered - dc_level

        target_fs = kwargs.get("target_sample_rate", None)
        if target_fs is None and self.restore_original_rate:
            orig_fs = modulated.metadata.get("original_sample_rate", None)
            if orig_fs is not None and int(orig_fs) > 0 and int(orig_fs) != fs:
                target_fs = int(orig_fs)

        if target_fs is not None and int(target_fs) != fs:
            out_fs = int(target_fs)
            target_len = int(round(len(demod_audio) * out_fs / fs))
            if target_len > 0:
                demod_audio = signal_proc.resample(demod_audio, target_len)
                demod_audio = demod_audio - np.mean(demod_audio)
        else:
            out_fs = fs

        if self.normalize_output:
            peak = float(np.max(np.abs(demod_audio)))
            if peak > 1e-9:
                demod_audio = (demod_audio / peak) * 0.90

        demod_samples = demod_audio.astype(np.float32)

        pearson_r = None
        if reference_audio is not None:
            pearson_r = compute_pearson_correlation(reference_audio, demod_samples)

        rec_metadata: Dict[str, Any] = {
            "demod_method": method,
            "carrier_freq": fc,
            "cutoff_freq_hz": effective_cutoff,
            "filter_order": order,
            "phase_offset_rad": phi,
            "dc_removed": dc_level,
            "source_modulation": modulated.modulation_type,
            "rms_amplitude": float(np.sqrt(np.mean(demod_samples ** 2))),
            "peak_amplitude": float(np.max(np.abs(demod_samples))),
        }
        if pearson_r is not None:
            rec_metadata["pearson_correlation"] = pearson_r

        recovered = AudioSignal(
            samples=demod_samples,
            sample_rate=out_fs,
            bit_depth=16,
            duration=float(len(demod_samples) / out_fs),
            metadata=rec_metadata
        )

        return DemodulatedResult(
            recovered_audio=recovered,
            demodulation_type=f"AM-{method.capitalize()}",
            detected_bits=None,
            bit_error_rate=None,
            metadata={
                "method": method,
                "cutoff_freq": effective_cutoff,
                "filter_order": order,
                "carrier_freq": fc,
                "sampling_rate": out_fs,
                "pearson_correlation": pearson_r,
            }
        )


class FMDemodulator(BaseDemodulator):
    def __init__(
        self,
        cutoff_freq: float = 3500.0,
        filter_order: int = 5,
        restore_original_rate: bool = True,
        normalize_output: bool = True
    ):
        if cutoff_freq <= 0:
            raise ValueError("cutoff_freq debe ser mayor a 0.")
        if filter_order < 1 or filter_order > 12:
            raise ValueError("filter_order debe estar entre 1 y 12.")

        self.cutoff_freq = float(cutoff_freq)
        self.filter_order = int(filter_order)
        self.restore_original_rate = bool(restore_original_rate)
        self.normalize_output = bool(normalize_output)

    def demodulate(self, modulated: ModulatedSignal, **kwargs) -> DemodulatedResult:
        if not isinstance(modulated, ModulatedSignal):
            raise TypeError(f"Se esperaba ModulatedSignal, se recibio: {type(modulated)}")

        cutoff = float(kwargs.get("cutoff_freq", self.cutoff_freq))
        order = int(kwargs.get("filter_order", self.filter_order))
        reference_audio: Optional[AudioSignal] = kwargs.get("reference_audio", None)

        fs = modulated.sampling_rate
        fc = modulated.carrier_freq
        s = np.asarray(modulated.samples, dtype=np.float64)

        if len(s) == 0:
            raise ValueError("La senal FM modulada esta vacia.")

        analytic = signal_proc.hilbert(s)
        inst_phase = np.unwrap(np.angle(analytic))
        inst_freq = np.gradient(inst_phase, 1.0 / fs) / (2.0 * np.pi)

        kf = float(modulated.metadata.get("freq_sensitivity_kf", 1.0))
        demod_raw = (inst_freq - fc) / (kf if kf > 0 else 1.0)

        if len(demod_raw) > 20:
            demod_raw[:5] = demod_raw[5]
            demod_raw[-5:] = demod_raw[-6]

        nyq = 0.5 * fs
        w_meta = modulated.metadata.get("message_bandwidth_w_hz", None)
        target_cut = float(w_meta) * 1.15 if (w_meta is not None and w_meta > 500) else cutoff
        effective_cutoff = min(target_cut, cutoff, 0.95 * nyq)
        b, a = signal_proc.butter(order, effective_cutoff / nyq, btype="low", analog=False)

        if len(demod_raw) > 3 * max(len(a), len(b)):
            filtered = signal_proc.filtfilt(b, a, demod_raw)
        else:
            filtered = signal_proc.lfilter(b, a, demod_raw)

        demod_audio = filtered - np.mean(filtered)

        target_fs = kwargs.get("target_sample_rate", None)
        if target_fs is None and self.restore_original_rate:
            orig_fs = modulated.metadata.get("original_sample_rate", None)
            if orig_fs is not None and int(orig_fs) > 0 and int(orig_fs) != fs:
                target_fs = int(orig_fs)

        if target_fs is not None and int(target_fs) != fs:
            out_fs = int(target_fs)
            target_len = int(round(len(demod_audio) * out_fs / fs))
            if target_len > 0:
                demod_audio = signal_proc.resample(demod_audio, target_len)
                demod_audio = demod_audio - np.mean(demod_audio)
        else:
            out_fs = fs

        if self.normalize_output:
            peak = float(np.max(np.abs(demod_audio)))
            if peak > 1e-9:
                demod_audio = (demod_audio / peak) * 0.90

        demod_samples = demod_audio.astype(np.float32)
        pearson_r = compute_pearson_correlation(reference_audio, demod_samples) if reference_audio is not None else None

        recovered = AudioSignal(
            samples=demod_samples,
            sample_rate=out_fs,
            bit_depth=16,
            duration=float(len(demod_samples) / out_fs),
            metadata={
                "demod_method": "fm_hilbert_discriminator",
                "carrier_freq": fc,
                "cutoff_freq_hz": effective_cutoff,
                "filter_order": order,
                "source_modulation": modulated.modulation_type,
                "pearson_correlation": pearson_r,
            }
        )

        return DemodulatedResult(
            recovered_audio=recovered,
            demodulation_type="FM-HilbertDiscriminator",
            detected_bits=None,
            bit_error_rate=None,
            metadata={
                "method": "hilbert_discriminator",
                "cutoff_freq": effective_cutoff,
                "filter_order": order,
                "carrier_freq": fc,
                "sampling_rate": out_fs,
                "pearson_correlation": pearson_r,
            }
        )


class DigitalDemodulator(BaseDemodulator):
    VALID_SCHEMES = ("AUTO", "ASK", "FSK", "BPSK")

    def __init__(
        self,
        mod_type: str = "AUTO",
        samples_per_symbol: Optional[int] = None,
        carrier_freq: Optional[float] = None,
        f0: Optional[float] = None,
        f1: Optional[float] = None,
        threshold: Optional[float] = None,
        detection_mode: str = "coherent"
    ):
        scheme_up = mod_type.strip().upper()
        if scheme_up not in self.VALID_SCHEMES:
            raise ValueError(f"Esquema digital '{mod_type}' no valido. Opciones: {self.VALID_SCHEMES}.")
        if samples_per_symbol is not None and samples_per_symbol < 2:
            raise ValueError("samples_per_symbol debe ser >= 2.")
        if carrier_freq is not None and carrier_freq <= 0:
            raise ValueError("carrier_freq debe ser mayor a 0.")
        if detection_mode.strip().lower() not in ("coherent", "noncoherent"):
            raise ValueError("detection_mode debe ser 'coherent' o 'noncoherent'.")

        self.mod_type = scheme_up
        self.samples_per_symbol = int(samples_per_symbol) if samples_per_symbol is not None else None
        self.carrier_freq = float(carrier_freq) if carrier_freq is not None else None
        self.f0 = float(f0) if f0 is not None else None
        self.f1 = float(f1) if f1 is not None else None
        self.threshold = float(threshold) if threshold is not None else None
        self.detection_mode = detection_mode.strip().lower()

    def _resolve_scheme(self, modulated: ModulatedSignal, override_type: Optional[str]) -> str:
        if override_type is not None and override_type.strip().upper() != "AUTO":
            return override_type.strip().upper()
        if self.mod_type != "AUTO":
            return self.mod_type

        meta_type = str(modulated.metadata.get("digital_modulation_type", "")).upper()
        if meta_type in ("ASK", "FSK", "BPSK"):
            return meta_type

        mod_str = modulated.modulation_type.upper()
        for candidate in ("ASK", "FSK", "BPSK"):
            if candidate in mod_str:
                return candidate

        raise ValueError(f"No se pudo determinar el esquema digital desde '{modulated.modulation_type}'.")

    def demodulate(self, modulated: ModulatedSignal, **kwargs) -> DemodulatedResult:
        if not isinstance(modulated, ModulatedSignal):
            raise TypeError(f"Se esperaba ModulatedSignal, se recibio: {type(modulated)}")

        scheme = self._resolve_scheme(modulated, kwargs.get("mod_type", None))
        fs = modulated.sampling_rate
        fc = float(kwargs.get("carrier_freq", self.carrier_freq or modulated.carrier_freq))

        sps = kwargs.get("samples_per_symbol", self.samples_per_symbol)
        if sps is None:
            sps = modulated.metadata.get("samples_per_symbol", 16)
        sps = int(sps)
        if sps < 2:
            raise ValueError(f"samples_per_symbol invalido: {sps}")

        s = np.asarray(modulated.samples, dtype=np.float64)
        num_symbols = len(s) // sps
        if num_symbols == 0:
            raise ValueError("La longitud de la senal es menor a un periodo de simbolo.")

        usable_len = num_symbols * sps
        s_mat = s[:usable_len].reshape(num_symbols, sps)
        t_mat = modulated.time_vector[:usable_len].reshape(num_symbols, sps)
        t_local = np.arange(sps, dtype=np.float64) / fs

        user_threshold = kwargs.get("threshold", self.threshold)
        mode = str(kwargs.get("detection_mode", self.detection_mode)).strip().lower()

        if scheme == "ASK":
            a0 = float(modulated.metadata.get("a0", 0.0))
            a1 = float(modulated.metadata.get("a1", 1.0))

            if mode == "noncoherent":
                ic = (2.0 / sps) * np.sum(s_mat * np.cos(2.0 * np.pi * fc * t_mat), axis=1)
                qc = (2.0 / sps) * np.sum(s_mat * np.sin(2.0 * np.pi * fc * t_mat), axis=1)
                decision_metrics = np.sqrt(ic ** 2 + qc ** 2)
            else:
                carrier_ref = np.cos(2.0 * np.pi * fc * t_mat)
                decision_metrics = (2.0 / sps) * np.sum(s_mat * carrier_ref, axis=1)

            if user_threshold is not None:
                threshold_val = float(user_threshold)
            else:
                peak_sig = float(np.max(np.abs(s)))
                if peak_sig > 1e-4 and a1 > 0:
                    threshold_val = peak_sig * ((a0 + a1) / (2.0 * a1))
                else:
                    threshold_val = 0.5 * (a0 + a1)

            detected_bits = (decision_metrics >= threshold_val).astype(np.uint8)

        elif scheme == "FSK":
            f0 = float(kwargs.get("f0", self.f0 or modulated.metadata.get("f0_hz", max(100.0, fc - 500.0))))
            f1 = float(kwargs.get("f1", self.f1 or modulated.metadata.get("f1_hz", fc + 500.0)))

            cos_f1 = np.cos(2.0 * np.pi * f1 * t_local)
            sin_f1 = np.sin(2.0 * np.pi * f1 * t_local)
            cos_f0 = np.cos(2.0 * np.pi * f0 * t_local)
            sin_f0 = np.sin(2.0 * np.pi * f0 * t_local)

            i1 = (2.0 / sps) * np.sum(s_mat * cos_f1, axis=1)
            q1 = (2.0 / sps) * np.sum(s_mat * sin_f1, axis=1)
            i0 = (2.0 / sps) * np.sum(s_mat * cos_f0, axis=1)
            q0 = (2.0 / sps) * np.sum(s_mat * sin_f0, axis=1)

            energy_f1 = np.sqrt(i1 ** 2 + q1 ** 2)
            energy_f0 = np.sqrt(i0 ** 2 + q0 ** 2)
            decision_metrics = energy_f1 - energy_f0

            threshold_val = float(user_threshold) if user_threshold is not None else 0.0
            detected_bits = (decision_metrics >= threshold_val).astype(np.uint8)

        elif scheme == "BPSK":
            carrier_ref = np.cos(2.0 * np.pi * fc * t_mat)
            decision_metrics = (2.0 / sps) * np.sum(s_mat * carrier_ref, axis=1)
            threshold_val = float(user_threshold) if user_threshold is not None else 0.0
            detected_bits = (decision_metrics >= threshold_val).astype(np.uint8)

        else:
            raise ValueError(f"Esquema '{scheme}' no soportado.")

        ref_stream: Optional[DigitalStream] = kwargs.get("reference_stream", None)
        ref_bits = kwargs.get("reference_bits", None)
        if ref_bits is None and ref_stream is not None:
            ref_bits = ref_stream.bitstream

        ber: Optional[float] = None
        bit_errors: Optional[int] = None
        if ref_bits is not None:
            ref_arr = np.asarray(ref_bits, dtype=np.uint8).flatten()
            cmp_len = min(len(ref_arr), len(detected_bits))
            if cmp_len > 0:
                bit_errors = int(np.sum(detected_bits[:cmp_len] != ref_arr[:cmp_len]))
                ber = float(bit_errors / cmp_len)

        bits_per_sample = kwargs.get("bits_per_sample", None)
        if bits_per_sample is None and ref_stream is not None:
            bits_per_sample = ref_stream.bits_per_sample

        if bits_per_sample is not None and int(bits_per_sample) > 0 and len(detected_bits) >= int(bits_per_sample):
            bps = int(bits_per_sample)
            v_min = float(kwargs.get("v_min", ref_stream.v_min if ref_stream is not None else -1.0))
            v_max = float(kwargs.get("v_max", ref_stream.v_max if ref_stream is not None else 1.0))
            pcm_fs = int(kwargs.get("pcm_sample_rate", ref_stream.sample_rate if ref_stream is not None else 16000))

            num_pcm_samples = len(detected_bits) // bps
            reshaped_bits = detected_bits[:num_pcm_samples * bps].reshape(num_pcm_samples, bps)
            powers = 1 << np.arange(bps - 1, -1, -1, dtype=np.int32)
            levels = np.dot(reshaped_bits, powers)
            step_size = (v_max - v_min) / (2 ** bps - 1)
            pcm_samples = (v_min + levels.astype(np.float32) * step_size).astype(np.float32)

            recovered_audio = AudioSignal(
                samples=pcm_samples,
                sample_rate=pcm_fs,
                bit_depth=16,
                duration=float(len(pcm_samples) / pcm_fs),
                metadata={
                    "demod_method": f"Digital-{scheme}-PCM",
                    "bits_per_sample": bps,
                    "total_bits_detected": len(detected_bits),
                    "bit_error_rate": ber,
                }
            )
        else:
            nrz_waveform = np.repeat(np.where(detected_bits == 1, 0.9, -0.9).astype(np.float32), sps)
            recovered_audio = AudioSignal(
                samples=nrz_waveform,
                sample_rate=fs,
                bit_depth=16,
                duration=float(len(nrz_waveform) / fs),
                metadata={
                    "demod_method": f"Digital-{scheme}-NRZ",
                    "samples_per_symbol": sps,
                    "total_bits_detected": len(detected_bits),
                    "bit_error_rate": ber,
                }
            )

        return DemodulatedResult(
            recovered_audio=recovered_audio,
            demodulation_type=f"Digital-{scheme}",
            detected_bits=detected_bits,
            bit_error_rate=ber,
            metadata={
                "digital_scheme": scheme,
                "samples_per_symbol": sps,
                "carrier_freq": fc,
                "threshold": threshold_val,
                "total_bits": len(detected_bits),
                "bit_errors": bit_errors,
                "bit_error_rate": ber,
                "decision_metrics": decision_metrics.astype(np.float32),
                "first_16_detected": "".join(str(b) for b in detected_bits[:16]),
            }
        )


DigitalShiftKeyingDemodulator = DigitalDemodulator


def plot_demodulated_comparison(
    original: AudioSignal,
    demodulated: Union[AudioSignal, DemodulatedResult],
    zoom_ms: Optional[float] = None,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    demod_sig = demodulated.recovered_audio if isinstance(demodulated, DemodulatedResult) else demodulated
    if not isinstance(original, AudioSignal) or not isinstance(demod_sig, AudioSignal):
        raise TypeError("Se esperaban instancias de AudioSignal o DemodulatedResult.")

    x_orig = original.samples
    y_demod = demod_sig.samples
    if len(y_demod) != len(x_orig) and len(x_orig) > 0 and len(y_demod) > 0:
        y_aligned = signal_proc.resample(y_demod, len(x_orig)).astype(np.float32)
    else:
        y_aligned = y_demod

    min_len = min(len(x_orig), len(y_aligned))
    t = original.time_vector[:min_len]
    x = x_orig[:min_len]
    y = y_aligned[:min_len]

    peak_x = float(np.max(np.abs(x))) or 1.0
    peak_y = float(np.max(np.abs(y))) or 1.0
    y_scaled = y * (peak_x / peak_y)

    corr_r = compute_pearson_correlation(x, y_scaled)
    mse_val = float(np.mean((x - y_scaled) ** 2))
    method_label = demod_sig.metadata.get("demod_method", "Demodulador")
    fc_val = demod_sig.metadata.get("carrier_freq", None)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9', labelsize=9)
        ax.grid(True, color='#30363d', linestyle='--', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    ax1.plot(t, x, color='#58a6ff', linewidth=1.2, alpha=0.9, label="Audio Original m(t)")
    ax1.plot(t, y_scaled, color='#3fb950', linewidth=1.0, linestyle='--', alpha=0.88,
             label=f"Audio Demodulado m_rec(t) ({method_label})")
    ax1.plot(t, x - y_scaled, color='#f85149', linewidth=0.75, alpha=0.55,
             label=f"Error e(t) (MSE = {mse_val:.5f})")

    ax1.set_title(
        f"Comparacion Temporal: Original vs Demodulada ({method_label}) | Correlacion r = {corr_r:.4f}",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax1.set_xlabel("Tiempo [segundos]", color='#c9d1d9', fontsize=9)
    ax1.set_ylabel("Amplitud Normalizada", color='#c9d1d9', fontsize=9)
    if zoom_ms is not None and zoom_ms > 0:
        ax1.set_xlim(0, min(t[-1] if len(t) > 0 else 1.0, zoom_ms * 1e-3))
    else:
        ax1.set_xlim(0, t[-1] if len(t) > 0 else 1.0)
    ax1.set_ylim(-1.08, 1.08)
    ax1.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    fs = original.sample_rate
    win = np.hanning(min_len)
    freqs = np.fft.rfftfreq(min_len, d=1.0 / fs)
    fft_x = np.abs(np.fft.rfft(x * win))
    fft_y = np.abs(np.fft.rfft(y_scaled * win))

    db_x = 20.0 * np.log10(np.clip(fft_x / (np.max(fft_x) + 1e-12), 1e-5, 1.0))
    db_y = 20.0 * np.log10(np.clip(fft_y / (np.max(fft_y) + 1e-12), 1e-5, 1.0))

    ax2.plot(freqs, db_x, color='#58a6ff', linewidth=1.1, alpha=0.85, label="Espectro Original |M(f)|")
    ax2.plot(freqs, db_y, color='#3fb950', linewidth=1.0, linestyle='--', alpha=0.85,
             label="Espectro Demodulado |M_rec(f)|")

    cutoff_hz = demod_sig.metadata.get("cutoff_freq_hz", None)
    if cutoff_hz is not None and cutoff_hz > 0:
        ax2.axvline(cutoff_hz, color='#d29922', linestyle='-.', linewidth=1.3,
                    label=f"Corte Filtro Butterworth ({cutoff_hz:,.0f} Hz)")

    if fc_val is not None and fc_val > 0 and fc_val < fs / 2.0:
        ax2.axvline(fc_val, color='#f85149', linestyle=':', linewidth=1.2,
                    label=f"Portadora ({fc_val:,.0f} Hz)")

    ax2.set_title(
        "Espectro en Banda Base y Filtrado Paso-Bajo",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax2.set_xlabel("Frecuencia [Hz]", color='#c9d1d9', fontsize=9)
    ax2.set_ylabel("Magnitud [dBFS]", color='#c9d1d9', fontsize=9)
    ax2.set_xlim(0, fs / 2.0)
    ax2.set_ylim(-75, 5)
    ax2.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')

    if show:
        plt.show()

    return fig


def plot_am_demodulation_modes(
    original: AudioSignal,
    coherent_result: Union[AudioSignal, DemodulatedResult],
    envelope_result: Union[AudioSignal, DemodulatedResult],
    zoom_ms: float = 35.0,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    sig_coh = coherent_result.recovered_audio if isinstance(coherent_result, DemodulatedResult) else coherent_result
    sig_env = envelope_result.recovered_audio if isinstance(envelope_result, DemodulatedResult) else envelope_result

    min_len = min(len(original.samples), len(sig_coh.samples), len(sig_env.samples))
    t = original.time_vector[:min_len]
    x = original.samples[:min_len]
    peak_x = float(np.max(np.abs(x))) or 1.0

    y_coh = sig_coh.samples[:min_len] * (peak_x / (float(np.max(np.abs(sig_coh.samples[:min_len]))) or 1.0))
    y_env = sig_env.samples[:min_len] * (peak_x / (float(np.max(np.abs(sig_env.samples[:min_len]))) or 1.0))

    r_coh = compute_pearson_correlation(x, y_coh)
    r_env = compute_pearson_correlation(x, y_env)

    fig, (ax_full, ax_zoom) = plt.subplots(2, 1, figsize=(11, 7.5), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax_full, ax_zoom):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9', labelsize=9)
        ax.grid(True, color='#30363d', linestyle='--', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    ax_full.plot(t, x, color='#58a6ff', linewidth=1.2, label="Original m(t)")
    ax_full.plot(t, y_coh, color='#3fb950', linewidth=1.0, linestyle='--',
                 label=f"AM Coherente (r = {r_coh:.4f})")
    ax_full.plot(t, y_env, color='#f0883e', linewidth=1.0, linestyle=':',
                 label=f"AM Envolvente Hilbert (r = {r_env:.4f})")
    ax_full.set_title(
        f"Demodulacion AM: Coherente (r={r_coh:.4f}) vs Envolvente (r={r_env:.4f})",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax_full.set_xlabel("Tiempo [segundos]", color='#c9d1d9', fontsize=9)
    ax_full.set_ylabel("Amplitud", color='#c9d1d9', fontsize=9)
    ax_full.set_xlim(0, t[-1] if len(t) > 0 else 1.0)
    ax_full.set_ylim(-1.08, 1.08)
    ax_full.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    t_center = 0.25 * (t[-1] if len(t) > 0 else 1.0)
    t_span = zoom_ms * 1e-3
    mask = (t >= t_center) & (t <= t_center + t_span)
    if not np.any(mask):
        mask = slice(0, min(min_len, int(zoom_ms * 1e-3 * original.sample_rate)))

    t_ms = t[mask] * 1000.0
    ax_zoom.plot(t_ms, x[mask], color='#58a6ff', linewidth=1.5, label="Original m(t)")
    ax_zoom.plot(t_ms, y_coh[mask], color='#3fb950', linewidth=1.2, linestyle='--',
                 label="Recuperada Coherente")
    ax_zoom.plot(t_ms, y_env[mask], color='#f0883e', linewidth=1.2, linestyle=':',
                 label="Recuperada Envolvente")
    ax_zoom.set_title(
        f"Detalle Temporal ({zoom_ms:.1f} ms)",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=8
    )
    ax_zoom.set_xlabel("Tiempo [milisegundos]", color='#c9d1d9', fontsize=9)
    ax_zoom.set_ylabel("Amplitud", color='#c9d1d9', fontsize=9)
    ax_zoom.set_ylim(-1.08, 1.08)
    ax_zoom.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')

    if show:
        plt.show()

    return fig


def plot_digital_demodulation(
    modulated: ModulatedSignal,
    demod_result: DemodulatedResult,
    original_bits: Optional[np.ndarray] = None,
    max_bits: int = 24,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    if demod_result.detected_bits is None:
        raise ValueError("DemodulatedResult no contiene detected_bits.")

    sps = int(demod_result.metadata.get("samples_per_symbol", 16))
    scheme = demod_result.metadata.get("digital_scheme", modulated.modulation_type)
    thresh = float(demod_result.metadata.get("threshold", 0.0))
    metrics = demod_result.metadata.get("decision_metrics", None)
    det_bits = demod_result.detected_bits

    num_plot_bits = min(max_bits, len(det_bits))
    num_plot_samples = num_plot_bits * sps
    t_ms = modulated.time_vector[:num_plot_samples] * 1000.0
    s_seg = modulated.samples[:num_plot_samples]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 8.5), constrained_layout=True)
    fig.patch.set_facecolor('#0d1117')

    for ax in (ax1, ax2, ax3):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9', labelsize=9)
        ax.grid(True, color='#30363d', linestyle='--', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    ax1.plot(t_ms, s_seg, color='#58a6ff', linewidth=1.0,
             label=f"Senal Recibida ({modulated.modulation_type}, sps={sps})")
    tb_ms = (sps / modulated.sampling_rate) * 1000.0
    for k in range(num_plot_bits + 1):
        ax1.axvline(k * tb_ms, color='#30363d', linestyle=':', linewidth=0.6)
    ax1.set_title(
        f"Senal Digital Pasabanda ({scheme} | {num_plot_bits} simbolos)",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=6
    )
    ax1.set_xlabel("Tiempo [milisegundos]", color='#c9d1d9', fontsize=9)
    ax1.set_ylabel("Amplitud", color='#c9d1d9', fontsize=9)
    ax1.set_xlim(0, num_plot_bits * tb_ms)
    ax1.set_ylim(-1.1, 1.1)
    ax1.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    bit_indices = np.arange(num_plot_bits)
    if metrics is not None:
        m_seg = metrics[:num_plot_bits]
    else:
        m_seg = det_bits[:num_plot_bits].astype(np.float32)

    colors = ['#3fb950' if b == 1 else '#f0883e' for b in det_bits[:num_plot_bits]]
    ax2.bar(bit_indices, m_seg, width=0.55, color=colors, alpha=0.85, edgecolor='#f0f6fc', linewidth=0.5,
            label="Correlacion por Simbolo r[k]")
    ax2.axhline(thresh, color='#f85149', linestyle='--', linewidth=1.5,
                label=f"Umbral ({thresh:.3f})")
    ax2.set_title(
        "Correlador por Simbolo y Umbral de Decision",
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=6
    )
    ax2.set_xlabel("Indice de Simbolo [k]", color='#c9d1d9', fontsize=9)
    ax2.set_ylabel("Correlacion r[k]", color='#c9d1d9', fontsize=9)
    ax2.set_xlim(-0.8, num_plot_bits - 0.2)
    ax2.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    ax3.step(bit_indices, det_bits[:num_plot_bits], where='mid', color='#3fb950', linewidth=2.0,
             marker='o', markersize=5, label="Bits Detectados")
    if original_bits is not None:
        orig_seg = np.asarray(original_bits, dtype=np.uint8).flatten()[:num_plot_bits]
        ax3.step(bit_indices, orig_seg, where='mid', color='#58a6ff', linewidth=1.3,
                 linestyle='--', marker='x', markersize=6, label="Bits Originales")

    ber_val = demod_result.bit_error_rate
    ber_str = f"BER = {ber_val:.6f}" if ber_val is not None else ""
    ax3.set_title(
        f"Secuencia de Bits Recuperada {ber_str}".strip(),
        color='#f0f6fc', fontsize=11, fontweight='bold', pad=6
    )
    ax3.set_xlabel("Indice de Bit [k]", color='#c9d1d9', fontsize=9)
    ax3.set_ylabel("Bit", color='#c9d1d9', fontsize=9)
    ax3.set_yticks([0, 1])
    ax3.set_ylim(-0.25, 1.35)
    ax3.set_xlim(-0.8, num_plot_bits - 0.2)
    ax3.legend(facecolor='#21262d', edgecolor='#30363d', labelcolor='#f0f6fc', loc='upper right', fontsize=8)

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')

    if show:
        plt.show()

    return fig


def play_demodulated_audio(
    demodulated: Union[DemodulatedResult, AudioSignal],
    async_play: bool = False
) -> bool:
    from ..core.audio_io import play_audio

    if isinstance(demodulated, DemodulatedResult):
        target_audio = demodulated.recovered_audio
    elif isinstance(demodulated, AudioSignal):
        target_audio = demodulated
    else:
        raise TypeError(f"Tipo no valido para reproduccion: {type(demodulated)}")

    return play_audio(target_audio, async_play=async_play)
