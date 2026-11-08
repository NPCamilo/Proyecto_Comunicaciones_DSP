"""
Suite de Pruebas Unitarias Automatizadas para Fase 1 (Adquisición, Análisis y Digitalización)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import os
import tempfile
import unittest
import numpy as np

from src.core.base import AudioSignal, DigitalStream
from src.core.audio_io import load_wav, save_wav, generate_synthetic_speech_phrase
from src.core.analyzer import analyze_signal_properties, compute_spectrum, estimate_max_frequency
from src.core.quantization import (
    simulate_sampling_nqs,
    quantize_signal,
    save_digital_stream,
    load_digital_stream
)


class TestFase1DSP(unittest.TestCase):
    
    def setUp(self):
        self.sample_rate = 16000
        self.duration = 2.0
        self.test_samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.signal = AudioSignal(
            samples=self.test_samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )

    def test_audio_signal_creation(self):
        """Verifica la inicialización, dimensiones y normalización de AudioSignal."""
        self.assertEqual(self.signal.num_samples, int(self.duration * self.sample_rate))
        self.assertAlmostEqual(self.signal.duration, self.duration, places=2)
        self.assertTrue(np.all(self.signal.samples >= -1.0))
        self.assertTrue(np.all(self.signal.samples <= 1.0))
        self.assertEqual(len(self.signal.time_vector), self.signal.num_samples)

    def test_save_and_load_wav(self):
        """Verifica que el flujo de exportar y cargar WAV conserve la señal con fidelidad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "test_audio.wav")
            save_wav(wav_path, self.signal, bit_depth=16)
            self.assertTrue(os.path.exists(wav_path))

            loaded = load_wav(wav_path)
            self.assertEqual(loaded.sample_rate, self.signal.sample_rate)
            self.assertEqual(loaded.num_samples, self.signal.num_samples)
            # La diferencia por cuantización a int16 debe ser minúscula (< 1/32767)
            diff = np.max(np.abs(loaded.samples - self.signal.samples))
            self.assertLess(diff, 1e-3)

    def test_spectral_analysis_and_nyquist(self):
        """Valida el cálculo de la FFT, estimación de f_max y criterio de Nyquist."""
        props = analyze_signal_properties(self.signal, energy_percent=0.99)
        self.assertEqual(props["sample_rate_hz"], self.sample_rate)
        self.assertGreater(props["peak_amplitude"], 0.0)
        self.assertGreater(props["rms_amplitude"], 0.0)
        
        # Para voz sintetizada con formantes hasta 2.5 kHz, f_max debe estar acotada
        f_max = props["f_max_effective_hz"]
        self.assertGreater(f_max, 300.0)
        self.assertLess(f_max, self.sample_rate / 2.0)
        
        # fs (16 kHz) debe satisfacer cómodamente Nyquist para voz
        self.assertTrue(props["nyquist_satisfied"])
        self.assertGreater(props["nyquist_margin_hz"], 0.0)

    def test_quantization_resolutions_and_sqnr(self):
        """
        Verifica la cuantización en múltiples resoluciones (4, 8 y 16 bits),
        constatando que el SQNR crezca conforme aumentan los bits.
        """
        stream_4 = quantize_signal(self.signal, bits_per_sample=4)
        stream_8 = quantize_signal(self.signal, bits_per_sample=8)   # 1 Byte
        stream_16 = quantize_signal(self.signal, bits_per_sample=16) # 2 Bytes

        # El número total de bits debe ser N * b
        n = self.signal.num_samples
        self.assertEqual(stream_4.total_bits, n * 4)
        self.assertEqual(stream_8.total_bits, n * 8)
        self.assertEqual(stream_16.total_bits, n * 16)

        # Verificar progresión monotónica del SQNR experimental
        self.assertGreater(stream_8.sqnr_db, stream_4.sqnr_db)
        self.assertGreater(stream_16.sqnr_db, stream_8.sqnr_db)

        # Verificar que el error no supere el semi-intervalo +/- Delta/2
        delta_8 = (stream_8.v_max - stream_8.v_min) / (2**8 - 1)
        err_8 = np.abs(self.signal.samples - stream_8.reconstructed_levels)
        self.assertLessEqual(np.max(err_8), delta_8 + 1e-5)

    def test_digital_stream_serialization(self):
        """Verifica el empaquetado binario y reconstrucción bit a bit (resolución por Byte)."""
        stream = quantize_signal(self.signal, bits_per_sample=8)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = os.path.join(tmpdir, "test_digital_stream")
            bin_path, meta_path = save_digital_stream(stream, base_path)
            
            self.assertTrue(os.path.exists(bin_path))
            self.assertTrue(os.path.exists(meta_path))

            loaded_stream = load_digital_stream(base_path)
            self.assertEqual(loaded_stream.total_bits, stream.total_bits)
            self.assertEqual(loaded_stream.bits_per_sample, stream.bits_per_sample)
            np.testing.assert_array_equal(loaded_stream.bitstream, stream.bitstream)
            np.testing.assert_array_equal(loaded_stream.quantized_levels, stream.quantized_levels)

    def test_sampling_nqs_decimation(self):
        """Verifica la simulación de submuestreo NQS."""
        t_sub, x_sub, fs_sub = simulate_sampling_nqs(self.signal, downsample_factor=2)
        self.assertEqual(fs_sub, self.sample_rate // 2)
        self.assertEqual(len(x_sub), len(self.signal.samples) // 2)
        self.assertEqual(len(t_sub), len(x_sub))


if __name__ == '__main__':
    unittest.main()
