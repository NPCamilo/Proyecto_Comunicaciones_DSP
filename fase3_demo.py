import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.audio_io import load_wav, record_voice_wav, save_wav
from src.core.quantization import quantize_signal, load_digital_stream
from src.modulation.analog_digital_stubs import (
    AMModulator,
    FMModulator,
    DigitalShiftKeyingModulator
)
from src.demodulation.demod_stubs import (
    AMDemodulator,
    FMDemodulator,
    DigitalDemodulator,
    compute_pearson_correlation,
    plot_demodulated_comparison,
    plot_am_demodulation_modes,
    plot_digital_demodulation,
    play_demodulated_audio
)


def run_phase3_pipeline(
    audio_path: str = None,
    mode: str = "all",
    carrier_am: float = 3000.0,
    cutoff_freq: float = 3500.0,
    filter_order: int = 5,
    play: bool = False,
    output_dir: str = "audio_data"
):
    os.makedirs(output_dir, exist_ok=True)

    orig_wav = audio_path or os.path.join(output_dir, "voz_original.wav")
    if os.path.exists(orig_wav):
        audio = load_wav(orig_wav)
    else:
        audio = record_voice_wav(orig_wav, duration=3.0, sample_rate=16000)

    bin_base = os.path.join(output_dir, "trama_digital_8bits")
    if os.path.exists(f"{bin_base}.bin"):
        stream = load_digital_stream(bin_base)
    else:
        stream = quantize_signal(audio, bits_per_sample=8)

    mode_lower = mode.lower()
    selected_for_play = None

    if mode_lower in ("all", "am", "coherent", "envelope"):
        am_mod = AMModulator(carrier_freq=carrier_am, mod_index=0.8, am_type="DSB-FC").modulate(audio)

        coh_demod = AMDemodulator(
            method="coherent",
            cutoff_freq=cutoff_freq,
            filter_order=filter_order
        )
        res_coh = coh_demod.demodulate(am_mod, reference_audio=audio)
        r_coh = compute_pearson_correlation(audio, res_coh.recovered_audio)

        env_demod = AMDemodulator(
            method="envelope",
            cutoff_freq=cutoff_freq,
            filter_order=filter_order
        )
        res_env = env_demod.demodulate(am_mod, reference_audio=audio)
        r_env = compute_pearson_correlation(audio, res_env.recovered_audio)

        print(f"AM Coherente - Correlacion Pearson: {r_coh:.4f}")
        print(f"AM Envolvente - Correlacion Pearson: {r_env:.4f}")

        plot_coh_path = os.path.join(output_dir, "08_demodulacion_am_coherente.png")
        plot_demodulated_comparison(audio, res_coh, save_path=plot_coh_path, show=False)

        plot_modes_path = os.path.join(output_dir, "09_comparativa_modos_am_coherente_vs_envolvente.png")
        plot_am_demodulation_modes(audio, res_coh, res_env, zoom_ms=35.0, save_path=plot_modes_path, show=False)

        wav_coh_path = os.path.join(output_dir, "demodulada_am_coherente.wav")
        wav_env_path = os.path.join(output_dir, "demodulada_am_envolvente.wav")
        save_wav(wav_coh_path, res_coh.recovered_audio, bit_depth=16)
        save_wav(wav_env_path, res_env.recovered_audio, bit_depth=16)

        selected_for_play = res_env if mode_lower == "envelope" else res_coh

    if mode_lower in ("all", "fm"):
        fm_mod = FMModulator(carrier_freq=3500.0, freq_dev=1200.0).modulate(audio)
        fm_demod = FMDemodulator(cutoff_freq=cutoff_freq, filter_order=filter_order)
        res_fm = fm_demod.demodulate(fm_mod, reference_audio=audio)
        r_fm = compute_pearson_correlation(audio, res_fm.recovered_audio)

        print(f"FM Discriminador Hilbert - Correlacion Pearson: {r_fm:.4f}")
        wav_fm_path = os.path.join(output_dir, "demodulada_fm.wav")
        save_wav(wav_fm_path, res_fm.recovered_audio, bit_depth=16)

        if mode_lower == "fm":
            selected_for_play = res_fm

    if mode_lower in ("all", "digital", "fsk", "ask"):
        sample_bits = stream.bitstream[:1200]

        mod_fsk = DigitalShiftKeyingModulator(
            mod_type="FSK",
            carrier_freq=2500.0,
            f0=1800.0,
            f1=3200.0,
            samples_per_symbol=16,
            continuous_phase=True
        ).modulate(sample_bits)

        dig_demod = DigitalDemodulator(mod_type="AUTO")
        res_fsk = dig_demod.demodulate(mod_fsk, reference_bits=sample_bits)

        mod_ask = DigitalShiftKeyingModulator(
            mod_type="ASK",
            carrier_freq=2500.0,
            samples_per_symbol=16,
            a0=0.0,
            a1=1.0
        ).modulate(sample_bits)
        res_ask = dig_demod.demodulate(mod_ask, reference_bits=sample_bits)

        print(f"FSK Digital - Bits: {res_fsk.metadata['total_bits']} | BER: {res_fsk.bit_error_rate:.6f}")
        print(f"ASK Digital - Bits: {res_ask.metadata['total_bits']} | BER: {res_ask.bit_error_rate:.6f}")

        plot_dig_path = os.path.join(output_dir, "10_demodulacion_digital_fsk_correlacion.png")
        plot_digital_demodulation(
            modulated=mod_fsk,
            demod_result=res_fsk,
            original_bits=sample_bits,
            max_bits=24,
            save_path=plot_dig_path,
            show=False
        )

    if play and selected_for_play is not None:
        play_demodulated_audio(selected_for_play, async_play=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecucion Fase 3 - Demodulacion DSP")
    parser.add_argument("--audio", type=str, default=None, help="Ruta a archivo WAV original")
    parser.add_argument("--mode", type=str, default="all",
                        choices=["all", "am", "coherent", "envelope", "fm", "digital", "fsk", "ask"])
    parser.add_argument("--carrier_am", type=float, default=3000.0)
    parser.add_argument("--cutoff", type=float, default=3500.0)
    parser.add_argument("--order", type=int, default=5)
    parser.add_argument("--play", action="store_true")
    parser.add_argument("--outdir", type=str, default="audio_data")
    args = parser.parse_args()

    run_phase3_pipeline(
        audio_path=args.audio,
        mode=args.mode,
        carrier_am=args.carrier_am,
        cutoff_freq=args.cutoff,
        filter_order=args.order,
        play=args.play,
        output_dir=args.outdir
    )
