"""
Suite de Pruebas Unitarias para el Módulo de Modulación (Fase 2)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import os
import tempfile
import unittest
import warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.core.base import AudioSignal, DigitalStream, ModulatedSignal
from src.core.audio_io import generate_synthetic_speech_phrase
from src.core.quantization import quantize_signal
from src.modulation.analog_digital_stubs import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator,
    plot_modulated_signal,
    plot_modulation_spectrum_translation
)


class TestAMModulation(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 1.0
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )

    def test_initialization_validations(self):
        """Verifica que el constructor valide correctamente los argumentos físicos."""
        # Frecuencia no positiva
        with self.assertRaises(ValueError):
            AMModulator(carrier_freq=0.0)
        with self.assertRaises(ValueError):
            AMModulator(carrier_freq=-1000.0)

        # mod_index no positivo
        with self.assertRaises(ValueError):
            AMModulator(mod_index=0.0)
        with self.assertRaises(ValueError):
            AMModulator(mod_index=-0.5)

        # carrier_amp no positivo
        with self.assertRaises(ValueError):
            AMModulator(carrier_amp=0.0)

        # Tipo AM inválido
        with self.assertRaises(ValueError):
            AMModulator(am_type="INVALID_TYPE")

    def test_standard_am_dsb_fc(self):
        """Verifica la modulación AM-DSB-FC estándar con mu <= 1.0 (sin sobremodulación)."""
        modulator = AMModulator(carrier_freq=3000.0, mod_index=0.8, am_type="DSB-FC")
        
        # Verificar método check_overmodulation
        is_over, mu, ac = modulator.check_overmodulation(self.audio)
        self.assertFalse(is_over)
        self.assertAlmostEqual(mu, 0.8, places=3)
        self.assertGreater(ac, 0.0)

        # Ejecutar modulación
        mod_sig = modulator.modulate(self.audio)
        self.assertIsInstance(mod_sig, ModulatedSignal)
        self.assertEqual(mod_sig.modulation_type, "AM-DSB-FC")
        self.assertFalse(mod_sig.is_digital)
        self.assertEqual(mod_sig.carrier_freq, 3000.0)

        # Comprobar límites de amplitud
        self.assertLessEqual(np.max(np.abs(mod_sig.samples)), 1.0)
        
        # Metadatos
        meta = mod_sig.metadata
        self.assertFalse(meta["is_overmodulated"])
        self.assertAlmostEqual(meta["mod_index"], 0.8, places=2)
        self.assertGreater(meta["efficiency_percent"], 0.0)
        self.assertGreater(meta["carrier_power"], 0.0)
        self.assertGreater(meta["sideband_power"], 0.0)

    def test_overmodulation_detection(self):
        """Verifica la detección y alerta ante sobremodulación (mu > 1.0)."""
        modulator = AMModulator(carrier_freq=3000.0, mod_index=1.5, am_type="DSB-FC")
        
        is_over, mu, _ = modulator.check_overmodulation(self.audio)
        self.assertTrue(is_over)
        self.assertGreater(mu, 1.0)

        # Verificar que se emita la advertencia de sobremodulación
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            mod_sig = modulator.modulate(self.audio)
            
            self.assertTrue(any(issubclass(w.category, UserWarning) for w in caught_warnings))
            self.assertTrue(any("Sobremodulación" in str(w.message) for w in caught_warnings))

        self.assertTrue(mod_sig.metadata["is_overmodulated"])
        self.assertAlmostEqual(mod_sig.metadata["mod_index"], 1.5, places=2)

    def test_am_dsb_sc(self):
        """Verifica la modulación AM-DSB-SC (Portadora Suprimida)."""
        modulator = AMModulator(carrier_freq=3000.0, am_type="DSB-SC")
        mod_sig = modulator.modulate(self.audio)

        self.assertEqual(mod_sig.modulation_type, "AM-DSB-SC")
        self.assertEqual(mod_sig.metadata["carrier_power"], 0.0)
        self.assertEqual(mod_sig.metadata["efficiency_percent"], 100.0)
        self.assertFalse(mod_sig.metadata["is_overmodulated"])

    def test_resampling_when_carrier_frequency_high(self):
        """Verifica que el modulador remuestree automáticamente si fs < 4 * fc para evitar aliasing."""
        # Audio a 8000 Hz con portadora a 3500 Hz (requiere fs >= 14000 Hz)
        audio_low = AudioSignal(
            samples=self.samples[:8000],
            sample_rate=8000,
            bit_depth=16,
            duration=1.0
        )
        modulator = AMModulator(carrier_freq=3500.0)
        mod_sig = modulator.modulate(audio_low)

        self.assertTrue(mod_sig.metadata["resampled"])
        self.assertGreaterEqual(mod_sig.sampling_rate, 4 * 3500.0)
        self.assertAlmostEqual(mod_sig.duration, audio_low.duration, places=2)


class TestFMModulation(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 1.0
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )

    def test_fm_initialization_validations(self):
        """Verifica validación de parámetros en FMModulator."""
        with self.assertRaises(ValueError):
            FMModulator(carrier_freq=0.0)
        with self.assertRaises(ValueError):
            FMModulator(carrier_amp=-1.0)
        with self.assertRaises(ValueError):
            FMModulator(freq_dev=-500.0)
        with self.assertRaises(ValueError):
            FMModulator(mod_index_beta=0.0)
        with self.assertRaises(ValueError):
            FMModulator(kf=-100.0)

    def test_nbfm_modulation(self):
        """Verifica modulación FM en banda angosta (NBFM, beta < 0.5)."""
        modulator = FMModulator(carrier_freq=3000.0, freq_dev=300.0, audio_bandwidth=2500.0)
        mod_sig = modulator.modulate(self.audio)

        self.assertIsInstance(mod_sig, ModulatedSignal)
        self.assertEqual(mod_sig.modulation_type, "FM-NBFM")
        self.assertEqual(mod_sig.metadata["fm_regime"], "NBFM")
        self.assertLess(mod_sig.metadata["modulation_index_beta"], 0.5)
        
        # Amplitud normalizada
        self.assertLessEqual(np.max(np.abs(mod_sig.samples)), 1.0)
        
        # Desviación y Carson
        self.assertAlmostEqual(mod_sig.metadata["freq_deviation_hz"], 300.0, places=1)
        expected_carson = 2.0 * (300.0 + 2500.0)
        self.assertAlmostEqual(mod_sig.metadata["bandwidth_carson_hz"], expected_carson, places=1)

    def test_wbfm_modulation(self):
        """Verifica modulación FM en banda ancha (WBFM, beta >= 0.5)."""
        modulator = FMModulator(carrier_freq=4000.0, freq_dev=3000.0, audio_bandwidth=1500.0)
        mod_sig = modulator.modulate(self.audio)

        self.assertEqual(mod_sig.modulation_type, "FM-WBFM")
        self.assertEqual(mod_sig.metadata["fm_regime"], "WBFM")
        self.assertGreaterEqual(mod_sig.metadata["modulation_index_beta"], 1.0)
        self.assertAlmostEqual(mod_sig.metadata["freq_deviation_hz"], 3000.0, places=1)

    def test_instantaneous_frequency_calculation(self):
        """Verifica la función auxiliar get_instantaneous_frequency."""
        modulator = FMModulator(carrier_freq=3000.0, freq_dev=1000.0)
        t, f_inst = modulator.get_instantaneous_frequency(self.audio)

        self.assertEqual(len(t), len(self.audio.samples))
        self.assertEqual(len(f_inst), len(self.audio.samples))
        # f_inst debe oscilar alrededor de fc (3000 Hz) con rango aproximado [2000, 4000]
        self.assertAlmostEqual(float(np.mean(f_inst)), 3000.0, delta=200.0)
        self.assertGreaterEqual(float(np.min(f_inst)), 1900.0)
        self.assertLessEqual(float(np.max(f_inst)), 4100.0)

    def test_fm_overdeviation_warning(self):
        """Verifica advertencia cuando delta_f >= fc (riesgo de frecuencias instantáneas negativas)."""
        modulator = FMModulator(carrier_freq=1000.0, freq_dev=1200.0)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mod_sig = modulator.modulate(self.audio)
            self.assertTrue(any(issubclass(w.category, UserWarning) for w in caught))
            self.assertTrue(any("Delta_f" in str(w.message) for w in caught))

    def test_fm_resampling_anti_aliasing(self):
        """Verifica remuestreo automático cuando la tasa original es menor que la requerida por Carson."""
        # Audio con fs baja (8 kHz) y señal FM con fc=3500 y delta_f=1000
        audio_low = AudioSignal(
            samples=self.samples[:8000],
            sample_rate=8000,
            bit_depth=16,
            duration=1.0
        )
        modulator = FMModulator(carrier_freq=3500.0, freq_dev=1000.0)
        mod_sig = modulator.modulate(audio_low)

        self.assertTrue(mod_sig.metadata["resampled"])
        self.assertGreaterEqual(mod_sig.sampling_rate, 4 * 3500.0)


class TestDigitalModulation(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 1.0
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        # DigitalStream real a 4 bits
        self.stream = quantize_signal(self.audio, bits_per_sample=4)
        self.short_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.uint8)

    def test_digital_initialization_validations(self):
        """Verifica validación de parámetros en DigitalShiftKeyingModulator."""
        with self.assertRaises(ValueError):
            DigitalShiftKeyingModulator(mod_type="UNKNOWN")
        with self.assertRaises(ValueError):
            DigitalShiftKeyingModulator(carrier_freq=0.0)
        with self.assertRaises(ValueError):
            DigitalShiftKeyingModulator(samples_per_symbol=1)
        with self.assertRaises(ValueError):
            DigitalShiftKeyingModulator(a1=0.0)
        with self.assertRaises(ValueError):
            DigitalShiftKeyingModulator(a0=-0.5)

    def test_ask_ook_modulation(self):
        """Verifica modulación ASK (OOK: A1=1.0, A0=0.0)."""
        modulator = DigitalShiftKeyingModulator(
            mod_type="ASK",
            carrier_freq=2000.0,
            samples_per_symbol=16,
            a0=0.0,
            a1=1.0
        )
        mod_sig = modulator.modulate(self.short_bits)

        self.assertIsInstance(mod_sig, ModulatedSignal)
        self.assertTrue(mod_sig.is_digital)
        self.assertEqual(mod_sig.modulation_type, "Digital-ASK")
        self.assertEqual(len(mod_sig.samples), len(self.short_bits) * 16)
        
        # En los intervalos de bit 0 (índices 16..32, 64..80, 80..96, 112..128),
        # la amplitud debe ser prácticamente 0 en OOK
        sps = 16
        bit0_chunk = mod_sig.samples[1 * sps : 2 * sps]
        self.assertAlmostEqual(float(np.max(np.abs(bit0_chunk))), 0.0, places=5)

        # En intervalos de bit 1, debe haber oscilación de portadora
        bit1_chunk = mod_sig.samples[0 * sps : 1 * sps]
        self.assertGreater(float(np.max(np.abs(bit1_chunk))), 0.5)

    def test_fsk_modulation(self):
        """Verifica modulación FSK binaria (f1=2500 Hz para bit 1, f0=1500 Hz para bit 0)."""
        modulator = DigitalShiftKeyingModulator(
            mod_type="FSK",
            carrier_freq=2000.0,
            f0=1500.0,
            f1=2500.0,
            samples_per_symbol=32,
            continuous_phase=True
        )
        mod_sig = modulator.modulate(self.short_bits)

        self.assertTrue(mod_sig.is_digital)
        self.assertEqual(mod_sig.modulation_type, "Digital-FSK")
        self.assertEqual(mod_sig.metadata["f0_hz"], 1500.0)
        self.assertEqual(mod_sig.metadata["f1_hz"], 2500.0)
        self.assertTrue(mod_sig.metadata["continuous_phase"])

        # La envolvente en FSK debe ser constante (|s(t)| > 0 en todo momento)
        self.assertGreater(float(np.mean(mod_sig.samples ** 2)), 0.1)

    def test_bpsk_modulation(self):
        """Verifica modulación BPSK (inversión de fase de 180° entre bit 1 y bit 0)."""
        sps = 32
        modulator = DigitalShiftKeyingModulator(
            mod_type="BPSK",
            carrier_freq=2000.0,
            samples_per_symbol=sps
        )
        bits_two = np.array([1, 0], dtype=np.uint8)
        mod_sig = modulator.modulate(bits_two)

        self.assertEqual(mod_sig.modulation_type, "Digital-BPSK")
        
        # El bloque de bit 0 (fase pi) debe ser el opuesto exacto del bloque de bit 1 (fase 0)
        chunk1 = mod_sig.samples[:sps]
        chunk0 = mod_sig.samples[sps : 2 * sps]
        
        # chunk0 ≈ -chunk1
        diff = np.max(np.abs(chunk0 + chunk1))
        self.assertLess(diff, 1e-4)

    def test_modulation_from_digital_stream(self):
        """Verifica modulación directa a partir de una instancia DigitalStream de Fase 1."""
        modulator = DigitalShiftKeyingModulator(
            mod_type="FSK",
            samples_per_symbol=16
        )
        mod_sig = modulator.modulate(self.stream)

        expected_samples = len(self.stream.bitstream) * 16
        self.assertEqual(len(mod_sig.samples), expected_samples)
        self.assertEqual(mod_sig.metadata["total_bits"], len(self.stream.bitstream))
        self.assertTrue(mod_sig.is_digital)

    def test_invalid_bitstream_inputs(self):
        """Verifica rechazo de entradas inválidas o corruptas."""
        modulator = DigitalShiftKeyingModulator(mod_type="ASK")

        # Flujo vacío
        with self.assertRaises(ValueError):
            modulator.modulate(np.array([], dtype=np.uint8))

        # Bits no binarios (e.g. valores 2 o -1)
        with self.assertRaises(ValueError):
            modulator.modulate(np.array([1, 0, 2, 0]))

        # Tipo incompatible (e.g. string)
        with self.assertRaises(TypeError):
            modulator.modulate("101010")


class TestModulationPlotting(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 1.0
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        self.am_mod = AMModulator(carrier_freq=3000.0, mod_index=0.8).modulate(self.audio)
        self.fm_mod = FMModulator(carrier_freq=3000.0, freq_dev=1000.0).modulate(self.audio)
        self.bits = np.array([1, 0, 1, 1, 0, 1, 0, 0], dtype=np.uint8)
        self.dig_mod = DigitalShiftKeyingModulator(mod_type="FSK", carrier_freq=2000.0).modulate(self.bits)

    def tearDown(self):
        plt.close('all')

    def test_plot_modulated_signal_am(self):
        """Verifica la generación y exportación del gráfico de señal AM (tiempo y FFT)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_am_test.png")
            fig = plot_modulated_signal(
                self.am_mod,
                base_signal=self.audio,
                zoom_ms=10.0,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_plot_modulated_signal_fm(self):
        """Verifica la generación y exportación del gráfico de señal FM con regla de Carson."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_fm_test.png")
            fig = plot_modulated_signal(
                self.fm_mod,
                zoom_ms=8.0,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_plot_modulated_signal_digital_fsk(self):
        """Verifica la generación gráfica para modulación digital FSK con frecuencias f0 y f1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_fsk_test.png")
            fig = plot_modulated_signal(
                self.dig_mod,
                zoom_ms=15.0,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_plot_modulation_spectrum_translation(self):
        """Verifica la gráfica comparativa de traslación espectral (banda base vs pasabanda)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_translation_test.png")
            fig = plot_modulation_spectrum_translation(
                base_signal=self.audio,
                modulated=self.am_mod,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)


if __name__ == '__main__':
    unittest.main()
