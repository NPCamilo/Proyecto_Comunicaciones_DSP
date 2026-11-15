export interface ProjectMeta {
  title: string;
  subtitle: string;
  institution: string;
  course: string;
  author: string;
  version: string;
}

export interface Fase1AudioData {
  duration_s: number;
  sample_rate_hz: number;
  num_samples: number;
  peak_amplitude: number;
  rms_voltage: number;
  crest_factor: number;
  dynamic_range_db: number;
  f_max_effective_hz: number;
  nyquist_min_rate_hz: number;
  nyquist_margin_hz: number;
  nyquist_satisfied: boolean;
  nyquist_verdict: string;
}

export interface Fase1SamplingData {
  downsampled_rate_hz: number;
  downsampled_samples: number;
  bits_per_sample: number;
  quantization_levels: number;
  step_size_delta: number;
  sqnr_empirical_db: number;
  sqnr_theoretical_db: number;
  total_bytes: number;
  first_64_bits: string;
  first_bytes_hex: string;
}

export interface Fase2ModulationData {
  am: {
    carrier_freq_hz: number;
    modulation_index_mu: number;
    carrier_power_w: number;
    sideband_power_w: number;
    efficiency_percent: number;
  };
  fm: {
    carrier_freq_hz: number;
    freq_deviation_hz: number;
    beta: number;
    regime: string;
    carson_bw_hz: number;
    inst_freq_min_hz: number;
    inst_freq_max_hz: number;
  };
  fsk: {
    scheme: string;
    f0_hz: number;
    f1_hz: number;
    bit_rate_bps: number;
    samples_per_symbol: number;
    total_bits_modulated: number;
  };
}

export interface Fase3DemodulationData {
  am_coherent: {
    pearson_corr: number;
    snr_db: number;
  };
  am_envelope: {
    pearson_corr: number;
    snr_db: number;
  };
  fm_discriminator: {
    pearson_corr: number;
    snr_db: number;
  };
  fsk_digital: {
    total_bits: number;
    bit_errors: number;
    ber: number;
    ber_display: string;
  };
}

export interface FidelityMetricItem {
  method: string;
  output_rate_hz: number;
  mse: number;
  snr_db: number;
  psnr_db: number;
  pearson_corr: number;
  spectral_distortion_db: number;
}

export interface Fase45Data {
  dac_sinc: FidelityMetricItem;
  dac_zoh: FidelityMetricItem;
}

export interface DemoAssets {
  wav_original: string;
  wav_mod_am: string;
  wav_mod_fm: string;
  wav_mod_fsk: string;
  wav_demod_am_coherent: string;
  wav_demod_am_envelope: string;
  wav_demod_fm: string;
  wav_reconstructed_sinc: string;
  fig_time_spectrum: string;
  fig_nqs: string;
  fig_quantization: string;
  fig_mod_am: string;
  fig_mod_fm: string;
  fig_mod_fsk: string;
  fig_spectrum_translation: string;
  fig_demod_am: string;
  fig_am_modes: string;
  fig_demod_fsk: string;
  fig_fidelity_comparison: string;
  bin_stream: string;
  json_metadata: string;
}

export interface DemoData {
  project: ProjectMeta;
  fase1: {
    audio: Fase1AudioData;
    sampling_pcm: Fase1SamplingData;
  };
  fase2: Fase2ModulationData;
  fase3: Fase3DemodulationData;
  fase4_5: Fase45Data;
  assets: DemoAssets;
}

export interface LiveAudioProcessResponse {
  success: boolean;
  message: string;
  duration_s: number;
  sample_rate_hz: number;
  f_max_hz: number;
  nyquist_satisfied: boolean;
  pcm_rate_hz: number;
  pcm_bits: number;
  sqnr_db: number;
  modulation_applied: boolean;
  modulation_type: string;
  demodulation_type: string;
  carrier_freq_hz: number;
  snr_db: number;
  psnr_db: number;
  pearson_corr: number;
  mse: number;
  audio_original_b64?: string;
  audio_modulated_b64?: string;
  audio_demodulated_b64?: string;
  audio_reconstructed_b64?: string;
  waveform_original: number[];
  waveform_reconstructed: number[];
}
