"""
Suite de Pruebas Unitarias para el Módulo de Modulación (Fase 2)
Universidad Tecnológica de Pereira (UTP) - Comunicaciones I
"""

import unittest
import warnings
import numpy as np

from src.core.base import AudioSignal, ModulatedSignal
from src.core.audio_io import generate_synthetic_speech_phrase
from src.modulation.analog_digital_stubs import AMModulator


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


if __name__ == '__main__':
    unittest.main()
