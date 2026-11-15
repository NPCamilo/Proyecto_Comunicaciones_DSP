"""
Suite de Pruebas Unitarias Automatizadas para Fase 4 (Reconstrucción y Métricas)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import os
import tempfile
import unittest
import numpy as np

from src.core.base import AudioSignal, DemodulatedResult
from src.core.audio_io import load_wav
from src.core.quantization import quantize_signal
from src.reconstruction.metrics_stubs import AudioReconstructor


class TestFase4ReconstructionDSP(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 0.5
        t = np.arange(int(self.duration * self.sample_rate)) / self.sample_rate
        self.samples = (0.8 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
        self.signal = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        self.stream = quantize_signal(self.signal, bits_per_sample=8)

    def test_zoh_filtered_reconstruction(self):
        """Verifica la reconstrucción ZOH con filtro Butterworth paso-bajo."""
        reconstructor = AudioReconstructor(method="zoh_filtered")
        reconstructed = reconstructor.reconstruct_from_quantized(self.stream)

        self.assertIsInstance(reconstructed, AudioSignal)
        self.assertEqual(reconstructed.sample_rate, self.sample_rate)
        self.assertEqual(reconstructed.num_samples, self.signal.num_samples)
        self.assertTrue(np.all(np.isfinite(reconstructed.samples)))
        self.assertLessEqual(np.max(np.abs(reconstructed.samples)), 0.96)

        metrics = reconstructor.evaluate_fidelity(self.signal, reconstructed)
        self.assertGreater(metrics.pearson_corr, 0.5)
        self.assertGreater(metrics.snr_db, 0.0)

    def test_zoh_hold_preserves_levels(self):
        """Verifica que el ZOH puro mantenga los niveles cuantizados en cada muestra."""
        reconstructor = AudioReconstructor(method="zoh")
        reconstructed = reconstructor.reconstruct_from_quantized(self.stream)

        levels = self.stream.reconstructed_levels.astype(np.float32)
        expected = levels / (np.max(np.abs(levels)) or 1.0) * 0.95
        np.testing.assert_allclose(reconstructed.samples, expected, atol=1e-5)

    def test_sinc_interpolation_quality(self):
        """Valida la interpolación Whittaker-Shannon mediante sobremuestreo 4x."""
        fs = 4000
        f0 = 300.0
        t = np.arange(int(0.2 * fs)) / fs
        x = (0.9 * np.sin(2 * np.pi * f0 * t)).astype(np.float32)

        reconstructor = AudioReconstructor(method="sinc", sinc_half_width=32)
        target_rate = 4 * fs
        reconstructed = reconstructor.reconstruct(x, target_rate, input_rate=fs)

        self.assertEqual(reconstructed.sample_rate, target_rate)
        self.assertEqual(reconstructed.num_samples, int(np.floor(len(x) * target_rate / fs)))

        t_out = np.arange(reconstructed.num_samples) / target_rate
        ideal = 0.9 * np.sin(2 * np.pi * f0 * t_out)

        margin = 96
        error = np.abs(reconstructed.samples[margin:-margin] - ideal[margin:-margin])
        self.assertLess(float(np.max(error)), 0.02)

    def test_sinc_same_rate_identity(self):
        """A la misma tasa, la interpolación Sinc debe reproducir las muestras originales."""
        reconstructor = AudioReconstructor(method="sinc")
        reconstructed = reconstructor.reconstruct(
            self.samples, self.sample_rate, input_rate=self.sample_rate
        )
        np.testing.assert_allclose(reconstructed.samples, self.samples, atol=1e-5)

    def test_reconstruct_from_demodulated_result(self):
        """Verifica la reconstrucción a partir de un DemodulatedResult de Fase 3."""
        recovered = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        result = DemodulatedResult(
            recovered_audio=recovered,
            demodulation_type="AM-Coherent",
            metadata={"carrier_freq": 5000.0}
        )

        reconstructor = AudioReconstructor(method="sinc")
        reconstructed = reconstructor.reconstruct_from_demodulated(result)

        self.assertIsInstance(reconstructed, AudioSignal)
        self.assertEqual(reconstructed.sample_rate, self.sample_rate)
        self.assertEqual(reconstructed.num_samples, recovered.num_samples)
        self.assertEqual(reconstructed.metadata.get("demodulation_type"), "AM-Coherent")

    def test_fidelity_metrics(self):
        """Comprueba MSE, SNR, PSNR, Pearson y distorsión espectral real."""
        reconstructor = AudioReconstructor()

        perfect = reconstructor.evaluate_fidelity(self.signal, self.signal)
        self.assertAlmostEqual(perfect.mse, 0.0, places=10)
        self.assertGreater(perfect.snr_db, 90.0)
        self.assertAlmostEqual(perfect.pearson_corr, 1.0, places=6)
        self.assertLess(perfect.spectral_distortion_db, 1e-6)

        rng = np.random.default_rng(42)
        noisy_samples = self.signal.samples + 0.05 * rng.normal(size=self.signal.num_samples)
        noisy = AudioSignal(
            samples=noisy_samples.astype(np.float32),
            sample_rate=self.sample_rate,
            bit_depth=16
        )
        degraded = reconstructor.evaluate_fidelity(self.signal, noisy)

        self.assertGreater(degraded.mse, perfect.mse)
        self.assertLess(degraded.snr_db, perfect.snr_db)
        self.assertLess(degraded.pearson_corr, perfect.pearson_corr)
        self.assertGreater(degraded.spectral_distortion_db, 0.0)
        self.assertTrue(np.isfinite(degraded.spectral_distortion_db))
        self.assertTrue(np.isfinite(degraded.psnr_db))

    def test_export_reconstructed_wav(self):
        """Verifica la exportación del audio reconstruido y su lectura posterior."""
        reconstructor = AudioReconstructor(method="zoh")
        reconstructed = reconstructor.reconstruct_from_quantized(self.stream)

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "audio_reconstruido.wav")
            saved_path = reconstructor.export_reconstructed_wav(
                reconstructed, filepath=wav_path, play=False
            )

            self.assertTrue(os.path.exists(saved_path))

            loaded = load_wav(saved_path)
            self.assertEqual(loaded.sample_rate, reconstructed.sample_rate)
            self.assertEqual(loaded.num_samples, reconstructed.num_samples)
            diff = np.max(np.abs(loaded.samples - reconstructed.samples))
            self.assertLess(diff, 1e-3)


if __name__ == '__main__':
    unittest.main()
