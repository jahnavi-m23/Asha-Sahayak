/**
 * Audio processing utilities for Gnani Prisma v3.0 compatibility.
 * Official Specification: Raw 16-bit PCM, 16000 Hz, Single Channel (Mono), Little-Endian.
 * Recommended chunk size: 512 samples (1024 bytes) or 1024 samples (2048 bytes).
 *
 * Rural Healthcare Audio Preprocessing:
 * - Browser constraint feature checking (noiseSuppression, echoCancellation, autoGainControl)
 * - Hardware rumble / fan hum rejection filter (Highpass at 85 Hz)
 * - High-frequency hiss & aliasing rejection filter (Lowpass at 7500 Hz)
 * - Dynamic range compressor for voice leveling and anti-clipping
 */

export const TARGET_SAMPLE_RATE = 16000;
export const GNANI_RECOMMENDED_CHUNK_SAMPLES = 512; // 512 samples = 1024 bytes at 16-bit (32ms)

/**
 * Returns audio constraints, verifying browser support before applying each feature.
 */
export function getAudioConstraints() {
  const supported =
    navigator.mediaDevices && typeof navigator.mediaDevices.getSupportedConstraints === 'function'
      ? navigator.mediaDevices.getSupportedConstraints()
      : {};

  const constraints = {
    channelCount: 1,
    sampleRate: { ideal: TARGET_SAMPLE_RATE }
  };

  if (supported.noiseSuppression) {
    constraints.noiseSuppression = true;
  }
  if (supported.echoCancellation) {
    constraints.echoCancellation = true;
  }
  if (supported.autoGainControl) {
    constraints.autoGainControl = true;
  }

  return { audio: constraints };
}

/**
 * Creates an in-browser Web Audio preprocessing filter graph:
 * 1. High-Pass Filter (85 Hz, Q=0.707): Strips HVAC fan hum, table vibrations, traffic rumble
 * 2. Low-Pass Filter (7500 Hz, Q=0.707): Strips high-frequency electrical hiss while keeping fricatives
 * 3. Dynamics Compressor: Prevents mic clipping when close; boosts quiet speech in noisy backgrounds
 *
 * Chain: sourceNode -> highpassFilter -> lowpassFilter -> compressor -> output
 */
export function createNoiseFilterGraph(audioContext, sourceNode) {
  try {
    // 1. Highpass filter (cuts low-frequency wind, desk bumps, and ceiling fan rumbling below 85 Hz)
    const highpass = audioContext.createBiquadFilter();
    highpass.type = 'highpass';
    highpass.frequency.setValueAtTime(85, audioContext.currentTime);
    highpass.Q.setValueAtTime(0.707, audioContext.currentTime);

    // 2. Lowpass filter (cuts ultrasonic noise and RF hiss above 7.5 kHz while preserving human consonants)
    const lowpass = audioContext.createBiquadFilter();
    lowpass.type = 'lowpass';
    lowpass.frequency.setValueAtTime(7500, audioContext.currentTime);
    lowpass.Q.setValueAtTime(0.707, audioContext.currentTime);

    // 3. Dynamics Compressor (levels speech volume, tames plosives, and boosts whispered/quiet speech)
    const compressor = audioContext.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-24, audioContext.currentTime); // dB
    compressor.knee.setValueAtTime(12, audioContext.currentTime);       // dB
    compressor.ratio.setValueAtTime(4, audioContext.currentTime);        // 4:1 compression
    compressor.attack.setValueAtTime(0.003, audioContext.currentTime);   // 3ms
    compressor.release.setValueAtTime(0.25, audioContext.currentTime);   // 250ms

    // Wire up the pipeline
    sourceNode.connect(highpass);
    highpass.connect(lowpass);
    lowpass.connect(compressor);

    return {
      outputNode: compressor,
      nodes: [highpass, lowpass, compressor]
    };
  } catch (err) {
    console.warn('[AudioFilter] Web Audio filter graph initialization fallback to direct source:', err);
    return {
      outputNode: sourceNode,
      nodes: []
    };
  }
}

/**
 * Resamples a Float32Array from inputSampleRate down to TARGET_SAMPLE_RATE (16kHz)
 * using linear interpolation.
 * Does not assume the browser hardware matches 16kHz.
 */
export function downsampleTo16kHz(inputBuffer, inputSampleRate) {
  if (inputSampleRate === TARGET_SAMPLE_RATE) {
    return inputBuffer;
  }
  if (!inputSampleRate || inputSampleRate < TARGET_SAMPLE_RATE) {
    return inputBuffer;
  }

  const sampleRatio = inputSampleRate / TARGET_SAMPLE_RATE;
  const newLength = Math.round(inputBuffer.length / sampleRatio);
  const result = new Float32Array(newLength);

  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRatio);
    let accum = 0;
    let count = 0;

    for (let i = offsetBuffer; i < nextOffsetBuffer && i < inputBuffer.length; i++) {
      accum += inputBuffer[i];
      count++;
    }

    result[offsetResult] = count > 0 ? accum / count : 0;
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }

  return result;
}

/**
 * Converts Float32 audio samples (-1.0 to 1.0) to 16-bit Signed Integer PCM
 * (Int16Array, Little-Endian).
 */
export function floatTo16BitPCM(floatSamples) {
  const buffer = new ArrayBuffer(floatSamples.length * 2);
  const view = new DataView(buffer);

  for (let i = 0; i < floatSamples.length; i++) {
    let s = Math.max(-1, Math.min(1, floatSamples[i]));
    const pcm = s < 0 ? s * 0x8000 : s * 0x7fff;
    view.setInt16(i * 2, pcm, true); // true for Little-Endian
  }

  return buffer;
}

/**
 * Calculates Root Mean Square (RMS) volume level (0 to 1) for UI visual meters
 * and low-volume / silence detection.
 */
export function calculateRMS(samples) {
  if (!samples || samples.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < samples.length; i++) {
    sum += samples[i] * samples[i];
  }
  return Math.sqrt(sum / samples.length);
}
