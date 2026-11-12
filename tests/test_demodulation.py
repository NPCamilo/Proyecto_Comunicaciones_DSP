import os
import tempfile
import unittest
import warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.core.base import AudioSignal, DemodulatedResult
from src.core.audio_io import generate_synthetic_speech_phrase, save_wav, load_wav, play_audio
from src.core.quantization import quantize_signal
from src.modulation.analog_digital_stubs import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator
)
from src.demodulation.demod_stubs import (
    AMDemodulator,
    FMDemodulator,
    DigitalDemodulator,
    DigitalShiftKeyingDemodulator,
    compute_pearson_correlation,
    plot_demodulated_comparison,
    plot_am_demodulation_modes,
    plot_digital_demodulation,
    play_demodulated_audio
)


class TestAMDemodulation(unittest.TestCase):

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
        self.am_modulator = AMModulator(carrier_freq=3000.0, mod_index=0.8, am_type="DSB-FC")
        self.mod_am = self.am_modulator.modulate(self.audio)

    def test_am_demodulator_initialization_validations(self):
        with self.assertRaises(ValueError):
            AMDemodulator(method="invalid_mode")
        with self.assertRaises(ValueError):
            AMDemodulator(cutoff_freq=0.0)
        with self.assertRaises(ValueError):
            AMDemodulator(cutoff_freq=-500.0)
        with self.assertRaises(ValueError):
            AMDemodulator(filter_order=0)
        with self.assertRaises(ValueError):
            AMDemodulator(filter_order=15)

    def test_am_coherent_demodulation_high_fidelity(self):
        demodulator = AMDemodulator(method="coherent", cutoff_freq=3500.0, filter_order=5)
        result = demodulator.demodulate(self.mod_am, reference_audio=self.audio)

        self.assertIsInstance(result, DemodulatedResult)
        self.assertIsInstance(result.recovered_audio, AudioSignal)
        self.assertEqual(result.demodulation_type, "AM-Coherent")
        self.assertEqual(result.recovered_audio.num_samples, self.audio.num_samples)
        self.assertEqual(result.recovered_audio.sample_rate, self.audio.sample_rate)

        self.assertLessEqual(float(np.max(np.abs(result.recovered_audio.samples))), 1.0)
        self.assertAlmostEqual(float(np.mean(result.recovered_audio.samples)), 0.0, places=3)

        r_corr = compute_pearson_correlation(self.audio, result.recovered_audio)
        self.assertGreater(r_corr, 0.85)
        self.assertAlmostEqual(result.metadata["pearson_correlation"], r_corr, places=4)

    def test_am_envelope_hilbert_demodulation_high_fidelity(self):
        demodulator = AMDemodulator(method="envelope", cutoff_freq=3500.0, filter_order=5)
        result = demodulator.demodulate(self.mod_am, reference_audio=self.audio)

        self.assertIsInstance(result, DemodulatedResult)
        self.assertIsInstance(result.recovered_audio, AudioSignal)
        self.assertEqual(result.demodulation_type, "AM-Envelope")
        self.assertEqual(result.recovered_audio.num_samples, self.audio.num_samples)
        self.assertAlmostEqual(float(np.mean(result.recovered_audio.samples)), 0.0, places=3)

        r_corr = compute_pearson_correlation(self.audio, result.recovered_audio)
        self.assertGreater(r_corr, 0.85)

    def test_am_dsb_sc_coherent_vs_envelope_warning(self):
        mod_sc = AMModulator(carrier_freq=3000.0, am_type="DSB-SC").modulate(self.audio)

        coh_res = AMDemodulator(method="coherent", cutoff_freq=3500.0).demodulate(mod_sc)
        r_sc = compute_pearson_correlation(self.audio, coh_res.recovered_audio)
        self.assertGreater(r_sc, 0.85)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            AMDemodulator(method="envelope").demodulate(mod_sc)
            self.assertTrue(any(issubclass(w.category, UserWarning) for w in caught))

    def test_am_resampling_restoration(self):
        audio_low = AudioSignal(
            samples=self.samples[:8000],
            sample_rate=8000,
            bit_depth=16,
            duration=1.0
        )
        mod_high = AMModulator(carrier_freq=3500.0, mod_index=0.8).modulate(audio_low)
        self.assertGreater(mod_high.sampling_rate, 8000)

        demod_res = AMDemodulator(method="coherent", cutoff_freq=3200.0).demodulate(mod_high)
        self.assertEqual(demod_res.recovered_audio.sample_rate, 8000)
        self.assertEqual(demod_res.recovered_audio.num_samples, 8000)
        self.assertGreater(compute_pearson_correlation(audio_low, demod_res.recovered_audio), 0.85)


class TestFMDemodulation(unittest.TestCase):

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

    def test_fm_demodulator_hilbert_discriminator(self):
        mod_fm = FMModulator(carrier_freq=3500.0, freq_dev=1200.0).modulate(self.audio)
        demod_fm = FMDemodulator(cutoff_freq=3200.0, filter_order=5).demodulate(
            mod_fm, reference_audio=self.audio
        )

        self.assertIsInstance(demod_fm, DemodulatedResult)
        self.assertEqual(demod_fm.demodulation_type, "FM-HilbertDiscriminator")
        r_fm = compute_pearson_correlation(self.audio, demod_fm.recovered_audio)
        self.assertGreater(r_fm, 0.85)


class TestDigitalDemodulation(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 0.5
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        self.stream = quantize_signal(self.audio, bits_per_sample=8)
        self.test_bits = self.stream.bitstream[:640]

    def test_digital_demodulator_validations(self):
        with self.assertRaises(ValueError):
            DigitalDemodulator(mod_type="INVALID")
        with self.assertRaises(ValueError):
            DigitalDemodulator(samples_per_symbol=1)
        with self.assertRaises(ValueError):
            DigitalDemodulator(carrier_freq=-100.0)
        with self.assertRaises(ValueError):
            DigitalDemodulator(detection_mode="unknown_mode")

    def test_ask_demodulation_coherent_and_noncoherent(self):
        mod_ask = DigitalShiftKeyingModulator(
            mod_type="ASK",
            carrier_freq=2500.0,
            samples_per_symbol=16,
            a0=0.0,
            a1=1.0
        ).modulate(self.test_bits)

        for mode in ("coherent", "noncoherent"):
            demod = DigitalDemodulator(mod_type="ASK", detection_mode=mode)
            res = demod.demodulate(mod_ask, reference_bits=self.test_bits)

            self.assertIsInstance(res, DemodulatedResult)
            self.assertIsNotNone(res.detected_bits)
            self.assertEqual(len(res.detected_bits), len(self.test_bits))
            self.assertEqual(res.bit_error_rate, 0.0)
            np.testing.assert_array_equal(res.detected_bits, self.test_bits)

    def test_fsk_demodulation_continuous_and_discontinuous_phase(self):
        for cont_phase in (True, False):
            mod_fsk = DigitalShiftKeyingModulator(
                mod_type="FSK",
                carrier_freq=2500.0,
                f0=1800.0,
                f1=3200.0,
                samples_per_symbol=16,
                continuous_phase=cont_phase
            ).modulate(self.test_bits)

            demod = DigitalShiftKeyingDemodulator(mod_type="AUTO")
            res = demod.demodulate(mod_fsk, reference_bits=self.test_bits)

            self.assertEqual(res.demodulation_type, "Digital-FSK")
            self.assertEqual(res.bit_error_rate, 0.0)
            self.assertEqual(res.metadata["bit_errors"], 0)
            np.testing.assert_array_equal(res.detected_bits, self.test_bits)

    def test_bpsk_demodulation_zero_ber(self):
        mod_bpsk = DigitalShiftKeyingModulator(
            mod_type="BPSK",
            carrier_freq=2000.0,
            samples_per_symbol=16
        ).modulate(self.test_bits)

        demod = DigitalDemodulator(mod_type="BPSK")
        res = demod.demodulate(mod_bpsk, reference_bits=self.test_bits)

        self.assertEqual(res.demodulation_type, "Digital-BPSK")
        self.assertEqual(res.bit_error_rate, 0.0)
        np.testing.assert_array_equal(res.detected_bits, self.test_bits)

    def test_digital_stream_full_pcm_audio_recovery(self):
        short_audio = AudioSignal(
            samples=self.samples[:4000],
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=0.25
        )
        short_stream = quantize_signal(short_audio, bits_per_sample=8)
        mod_fsk_full = DigitalShiftKeyingModulator(
            mod_type="FSK",
            carrier_freq=2500.0,
            f0=1800.0,
            f1=3200.0,
            samples_per_symbol=16
        ).modulate(short_stream)

        demod = DigitalDemodulator()
        res = demod.demodulate(mod_fsk_full, reference_stream=short_stream)

        self.assertEqual(res.bit_error_rate, 0.0)
        np.testing.assert_array_equal(res.detected_bits, short_stream.bitstream)
        self.assertEqual(res.recovered_audio.num_samples, short_audio.num_samples)

        r_pcm = compute_pearson_correlation(short_audio, res.recovered_audio)
        self.assertGreater(r_pcm, 0.99)


class TestDemodulationVisualizationAndAudio(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.duration = 0.8
        self.samples = generate_synthetic_speech_phrase(duration=self.duration, sample_rate=self.sample_rate)
        self.audio = AudioSignal(
            samples=self.samples,
            sample_rate=self.sample_rate,
            bit_depth=16,
            duration=self.duration
        )
        self.mod_am = AMModulator(carrier_freq=3000.0, mod_index=0.8).modulate(self.audio)
        self.res_coh = AMDemodulator(method="coherent", cutoff_freq=3500.0).demodulate(self.mod_am)
        self.res_env = AMDemodulator(method="envelope", cutoff_freq=3500.0).demodulate(self.mod_am)

        self.bits = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0], dtype=np.uint8)
        self.mod_fsk = DigitalShiftKeyingModulator(mod_type="FSK", carrier_freq=2500.0).modulate(self.bits)
        self.res_fsk = DigitalDemodulator().demodulate(self.mod_fsk, reference_bits=self.bits)

    def tearDown(self):
        plt.close('all')

    def test_plot_demodulated_comparison(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_demod_comp.png")
            fig = plot_demodulated_comparison(
                original=self.audio,
                demodulated=self.res_coh,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_plot_am_demodulation_modes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_am_modes.png")
            fig = plot_am_demodulation_modes(
                original=self.audio,
                coherent_result=self.res_coh,
                envelope_result=self.res_env,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 2)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_plot_digital_demodulation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "plot_dig_demod.png")
            fig = plot_digital_demodulation(
                modulated=self.mod_fsk,
                demod_result=self.res_fsk,
                original_bits=self.bits,
                save_path=save_path,
                show=False
            )
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.axes), 3)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

    def test_play_demodulated_audio_and_wav_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "demodulada_am.wav")
            saved = save_wav(wav_path, self.res_coh.recovered_audio, bit_depth=16)
            self.assertTrue(os.path.exists(saved))

            reloaded = load_wav(saved)
            self.assertEqual(reloaded.num_samples, self.audio.num_samples)

        ok1 = play_demodulated_audio(self.res_coh, async_play=True)
        self.assertIsInstance(ok1, bool)
        ok2 = play_audio(self.res_coh.recovered_audio, async_play=True)
        self.assertIsInstance(ok2, bool)


if __name__ == "__main__":
    unittest.main()
