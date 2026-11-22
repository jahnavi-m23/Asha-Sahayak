import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  Square,
  Volume2,
  AlertCircle,
  CheckCircle,
  Copy,
  RefreshCw,
  Send,
  Sparkles,
  Info,
  Play,
  Pause,
  Languages
} from 'lucide-react';
import {
  getAudioConstraints,
  createNoiseFilterGraph,
  downsampleTo16kHz,
  floatTo16BitPCM,
  calculateRMS
} from '../utils/audioUtils';

// 10 Indian Languages documented by Gnani AI
// Voices verified and active on Gnani Timbre v2.5
const API_BASE = window.location.origin.includes(':5173') ? 'http://localhost:8000' : '';

const TEN_INDIAN_LANGUAGES = [
  { code: 'kn-IN', name: 'Kannada (ಕನ್ನಡ)', phase2: 'kn', defaultVoice: 'Devika' },
  { code: 'hi-IN', name: 'Hindi (हिन्दी)', phase2: 'hi', defaultVoice: 'Nalini' },
  { code: 'en-IN', name: 'Indian English', phase2: 'en', defaultVoice: 'Kaveri' },
  { code: 'ta-IN', name: 'Tamil (தமிழ்)', phase2: 'ta', defaultVoice: 'Oviya' },
  { code: 'te-IN', name: 'Telugu (తెలుగు)', phase2: 'te', defaultVoice: 'Devika' },
  { code: 'ml-IN', name: 'Malayalam (മലയാളം)', phase2: 'ml', defaultVoice: 'Devika' },
  { code: 'mr-IN', name: 'Marathi (मराठी)', phase2: 'mr', defaultVoice: 'Madhuri' },
  { code: 'bn-IN', name: 'Bengali (বাংলা)', phase2: 'bn', defaultVoice: 'Eishani' },
  { code: 'gu-IN', name: 'Gujarati (ગુજરાતી)', phase2: 'gu', defaultVoice: 'Falguni' },
  { code: 'pa-IN', name: 'Punjabi (ਪੰਜਾਬੀ)', phase2: 'pa', defaultVoice: 'Kartik' }
];

export default function VoiceRecorder({ onTranscriptComplete }) {
  // State variables
  const [recordingState, setRecordingState] = useState('idle'); // idle | requesting | recording | processing | completed | no_speech | error
  const [selectedLanguage, setSelectedLanguage] = useState('indic-auto');
  const [sttFormat, setSttFormat] = useState('codemix'); // 'codemix' (preserves English medical terms) | 'transcribe' (clean native script)
  const [enableKeyterms, setEnableKeyterms] = useState(true); // Keyterm boosting toggle
  const [keytermDomain, setKeytermDomain] = useState('general'); // general | maternal | vaccination | newborn | vitals
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [finalTranscripts, setFinalTranscripts] = useState([]);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0); // 0 to 100%
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [qualityWarning, setQualityWarning] = useState('');
  const [activeEngine, setActiveEngine] = useState(''); // gnani_prisma_v3 | mock_simulation
  const [isSimulation, setIsSimulation] = useState(false);
  const [micDeviceLabel, setMicDeviceLabel] = useState('');
  const [phase2Payload, setPhase2Payload] = useState(null);
  const [showRawTranscript, setShowRawTranscript] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [handoffSuccess, setHandoffSuccess] = useState(false);
  const [isSendingToPhase2, setIsSendingToPhase2] = useState(false);
  const [phase2Error, setPhase2Error] = useState('');
  const [sentRecordId, setSentRecordId] = useState('');

  // Text-To-Speech (TTS) & Multilingual Translation states - Gnani Timbre v2.5
  const [ttsLanguage, setTtsLanguage] = useState('kn-IN');
  const [translatedText, setTranslatedText] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationEngine, setTranslationEngine] = useState('');
  const [translationUncertain, setTranslationUncertain] = useState(false);
  const [translationWarning, setTranslationWarning] = useState('');
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const [ttsEngine, setTtsEngine] = useState('');
  const [ttsError, setTtsError] = useState('');

  // Refs
  const mediaStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorNodeRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const filterNodesRef = useRef([]);
  const webSocketRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const audioElementRef = useRef(null);
  const chunkCountRef = useRef(0);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecordingResources();
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
    };
  }, []);

  const formatTime = (totalSec) => {
    const mins = Math.floor(totalSec / 60).toString().padStart(2, '0');
    const secs = (totalSec % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const stopRecordingResources = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    if (filterNodesRef.current && filterNodesRef.current.length > 0) {
      filterNodesRef.current.forEach((node) => {
        try {
          node.disconnect();
        } catch (e) {}
      });
      filterNodesRef.current = [];
    }

    if (processorNodeRef.current) {
      processorNodeRef.current.disconnect();
      processorNodeRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    setAudioLevel(0);
  };

  const startRecording = async () => {
    setErrorMessage('');
    setQualityWarning('');
    setFinalTranscripts([]);
    setInterimTranscript('');
    setDetectedLanguage(null);
    setPhase2Payload(null);
    setShowRawTranscript(false);
    setHandoffSuccess(false);
    setTtsError('');
    setIsSimulation(false);
    setRecordingState('requesting');
    chunkCountRef.current = 0;

    // 1. Capture microphone with verified browser constraints
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia(getAudioConstraints());
      mediaStreamRef.current = stream;
      const audioTrack = stream.getAudioTracks()[0];
      const label = audioTrack ? audioTrack.label : 'Default Microphone';
      setMicDeviceLabel(label);
      console.log('[ASHA STT Stage 1 - Mic Permission Granted] Selected Device:', label);
    } catch (err) {
      console.error('[ASHA STT Pipeline] Mic access denied:', err);
      setRecordingState('error');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage(
          'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ / Microphone permission was denied. Please allow microphone access in browser settings.'
        );
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMessage('ಯಾವುದೇ ಮೈಕ್ರೊಫೋನ್ ಪತ್ತೆಯಾಗಿಲ್ಲ / No microphone device found.');
      } else {
        setErrorMessage(`Microphone error: ${err.message || 'Unable to access microphone'}`);
      }
      return;
    }

    // 2. Open WebSocket to Backend with language and transcription format
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${host}:8000/api/voice/stream?language=${encodeURIComponent(selectedLanguage)}&stt_format=${encodeURIComponent(sttFormat)}&enable_keyterms=${enableKeyterms}&domain=${encodeURIComponent(keytermDomain)}`;

    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      webSocketRef.current = ws;
    } catch (wsErr) {
      console.error('[ASHA STT Pipeline] WebSocket initiation error:', wsErr);
      setRecordingState('error');
      setErrorMessage('Failed to connect to Voice Recognition backend server.');
      stopRecordingResources();
      return;
    }

    ws.onopen = () => {
      console.log('[ASHA STT Stage 4 - WebSocket Connected] Connected to backend endpoint:', wsUrl);
      setRecordingState('recording');
      setTimerSeconds(0);
      timerIntervalRef.current = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
      setupAudioPipeline(stream, ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
      } catch (err) {
        console.warn('[ASHA STT Pipeline] Non-JSON message received:', event.data);
      }
    };

    ws.onerror = (err) => {
      console.error('[ASHA STT Pipeline] WebSocket error event:', err);
      setRecordingState('error');
      setErrorMessage('Communication error with Voice Recognition backend server. Check if backend is running on port 8000.');
      stopRecordingResources();
    };

    ws.onclose = (event) => {
      console.log('[ASHA STT Pipeline] WebSocket closed:', event.code, event.reason);
      if (recordingState === 'recording') {
        setRecordingState('idle');
      }
      stopRecordingResources();
    };
  };

  const setupAudioPipeline = (stream, ws) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      let audioContext;
      try {
        audioContext = new AudioCtx({ sampleRate: 16000 });
      } catch (e) {
        audioContext = new AudioCtx();
      }
      audioContextRef.current = audioContext;
      console.log('[ASHA STT Stage 2 - Audio Capture Started] AudioContext sampleRate:', audioContext.sampleRate);

      const sourceNode = audioContext.createMediaStreamSource(stream);
      sourceNodeRef.current = sourceNode;

      // Rural Healthcare Audio Preprocessing:
      // Highpass (85Hz) removes fan/table rumble + Lowpass (7.5kHz) + Dynamics Compressor prevents clipping
      const filterGraph = createNoiseFilterGraph(audioContext, sourceNode);
      filterNodesRef.current = filterGraph.nodes;
      console.log('[ASHA STT Stage 2] Web Audio Preprocessing filter graph connected.');

      // bufferSize 2048 provides balanced latency and frame boundary alignment
      const bufferSize = 2048;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorNodeRef.current = processor;

      processor.onaudioprocess = (audioProcessingEvent) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;

        const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);

        // Calculate RMS for visual feedback
        const rms = calculateRMS(inputData);
        setAudioLevel(Math.min(100, Math.round(rms * 250)));

        // Resample input audio to Gnani's 16000 Hz specification
        const downsampled = downsampleTo16kHz(inputData, audioContext.sampleRate);

        // Convert Float32 samples to 16-bit linear Little-Endian PCM
        const pcmBuffer = floatTo16BitPCM(downsampled);

        chunkCountRef.current += 1;
        if (chunkCountRef.current === 1 || chunkCountRef.current % 50 === 0) {
          console.log(`[ASHA STT Stage 3 - Audio Chunk Generated] Chunk #${chunkCountRef.current}: ${pcmBuffer.byteLength}B, RMS=${rms.toFixed(3)}, level=${Math.round(rms * 250)}%`);
        }

        try {
          ws.send(pcmBuffer);
          if (chunkCountRef.current === 1 || chunkCountRef.current % 50 === 0) {
            console.log(`[ASHA STT Stage 4 - Audio Chunk Sent] Chunk #${chunkCountRef.current} sent over WebSocket`);
          }
        } catch (e) {
          console.error('[ASHA STT Pipeline] Error streaming chunk:', e);
        }
      };

      filterGraph.outputNode.connect(processor);
      processor.connect(audioContext.destination);
    } catch (pipelineErr) {
      console.error('[ASHA STT Pipeline] Web Audio pipeline error:', pipelineErr);
      setRecordingState('error');
      setErrorMessage(`Web Audio Error: ${pipelineErr.message}`);
      stopRecordingResources();
    }
  };

  const handleServerEvent = (data) => {
    if (data.type === 'connected') {
      const engine = data.engine || 'gnani_prisma_v3';
      const sim = Boolean(data.is_mock || data.is_simulation || engine === 'mock_simulation');
      setActiveEngine(engine);
      setIsSimulation(sim);
      console.log(`[ASHA STT Pipeline] Connected to engine: ${engine}, isSimulation: ${sim}`);
    } else if (data.type === 'transcript') {
      // Robust extraction supporting both Gnani's 'text' and standard 'transcript'
      const text = (data.text || data.transcript || '').trim();
      console.log(`[ASHA STT Stage 7 - Transcript Received] is_final=${data.is_final}, lang=${data.detected_language_code || 'n/a'}: "${text}"`);
      
      if (data.detected_language_code) {
        setDetectedLanguage(data.detected_language_code);
      }
      if (data.is_mock || data.is_simulation) {
        setIsSimulation(true);
      }
      if (text) {
        if (data.is_final) {
          setFinalTranscripts((prev) => {
            const next = [...prev, text];
            console.log(`[ASHA STT Stage 8 - Transcript Displayed] Final text updated (${next.length} segments): "${next.join(' ')}"`);
            return next;
          });
          setInterimTranscript('');
        } else {
          setInterimTranscript(text);
          console.log(`[ASHA STT Stage 8 - Transcript Displayed] Interim text updated: "${text}"`);
        }
      }
    } else if (data.type === 'speech_start') {
      console.log(`[ASHA STT Stage 6 - Speech Start] Utterance ID: ${data.utterance_id || 'active'}`);
    } else if (data.type === 'audio_quality_warning') {
      setQualityWarning(data.message);
    } else if (data.type === 'completed') {
      const payload = data.phase2_payload || {};
      setPhase2Payload(payload);
      
      const hasValidText = Boolean((payload.transcript && payload.transcript.trim()) || finalTranscripts.length > 0);
      if (hasValidText) {
        setRecordingState('completed');
        console.log('[ASHA STT Stage 8 - Completed] Recognition successfully completed with text:', payload.transcript);
      } else {
        setRecordingState('no_speech');
        console.log('[ASHA STT Stage 8 - No Speech] Session completed with no speech recognized.');
      }
      
      if (payload.detected_language) {
        setDetectedLanguage(payload.detected_language);
      }
      stopRecordingResources();

      // Automatically translate completed transcript to selected output language
      const completedText = (payload.transcript || finalTranscripts.join(' ') || '').trim();
      if (completedText) {
        fetchTranslation(completedText, ttsLanguage, payload.detected_language);
      }

      if (onTranscriptComplete) {
        onTranscriptComplete(payload);
      }
    } else if (data.type === 'error') {
      console.error('[ASHA STT Pipeline] Server reported error:', data);
      setRecordingState('error');
      setErrorMessage(data.message || 'Speech recognition error occurred on upstream Gnani service.');
      stopRecordingResources();
    }
  };

  const stopRecording = () => {
    setRecordingState('processing');
    console.log('[ASHA STT] Stop recording requested. Sending commit signal to finalize transcription...');
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      webSocketRef.current.send(JSON.stringify({ action: 'stop' }));
    } else {
      stopRecordingResources();
      setRecordingState('idle');
    }
  };

  const handleSendToPhase2 = async () => {
    if (!phase2Payload || isSendingToPhase2) return;
    setIsSendingToPhase2(true);
    setPhase2Error('');
    try {
      let userToken = null;
      let workerId = null;
      try {
        const savedSession = localStorage.getItem('asha_user_session');
        if (savedSession) {
          const user = JSON.parse(savedSession);
          userToken = `token-${user.username}-${user.id}`;
          workerId = user.id;
        }
      } catch (e) {
        // ignore
      }

      const payloadWithMeta = {
        ...phase2Payload,
        worker_id: workerId || phase2Payload.worker_id || null,
        record_id: phase2Payload.record_id || `REC-${Date.now().toString(36).toUpperCase()}`
      };

      const res = await fetch(`${API_BASE}/api/voice/to-phase2`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(userToken ? { 'Authorization': `Bearer ${userToken}` } : {})
        },
        body: JSON.stringify(payloadWithMeta)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setHandoffSuccess(true);
        setSentRecordId(data.record_id || payloadWithMeta.record_id);
        if (onTranscriptComplete) {
          onTranscriptComplete(data.payload || payloadWithMeta, data.report, data.form_type, data.household_data);
        }
      } else {
        setPhase2Error(data.detail || 'Failed to send transcript to Phase 2.');
      }
    } catch (err) {
      console.error('Failed to send to Phase 2 endpoint:', err);
      setPhase2Error(err.message || 'Network error connecting to Phase 2 endpoint.');
    } finally {
      setIsSendingToPhase2(false);
    }
  };

  const handleCopyTranscript = () => {
    const fullText = finalTranscripts.join(' ') || (phase2Payload && phase2Payload.transcript) || '';
    if (fullText) {
      navigator.clipboard.writeText(fullText);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  // Multilingual Translation: translates transcript to selected target language
  const fetchTranslation = async (text, targetLang, srcLang) => {
    if (!text || !text.trim()) return;
    setIsTranslating(true);
    setTtsError('');
    try {
      const source = srcLang || detectedLanguage || selectedLanguage || 'kn-IN';
      if (source === targetLang) {
        setTranslatedText(text.trim());
        setTranslationEngine('passthrough');
        setTranslationUncertain(false);
        setTranslationWarning('');
        setIsTranslating(false);
        return;
      }

      const res = await fetch(`${API_BASE}/api/voice/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          source_language: source,
          target_language: targetLang,
          domain: 'healthcare'
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.translated_text) {
          setTranslatedText(data.translated_text);
          setTranslationEngine(data.engine_used || 'indic-translator');
          setTranslationUncertain(Boolean(data.uncertain));
          setTranslationWarning(data.review_warning || '');
          console.log(`[ASHA Translation] Translated to ${targetLang} via ${data.engine_used}:`, data.translated_text);
        } else {
          setTranslatedText('');
          setTranslationUncertain(true);
          setTranslationWarning(data.error || data.review_warning || 'ಅನುವಾದ ವಿಫಲವಾಗಿದೆ / Translation could not be completed.');
        }
      } else {
        setTranslatedText('');
        setTranslationUncertain(true);
        setTranslationWarning('ಅನುವಾದ ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ / Translation service unavailable.');
      }
    } catch (e) {
      console.warn('Translation request failed:', e);
      setTranslatedText('');
      setTranslationUncertain(true);
      setTranslationWarning('Translation service unavailable. Please check connection.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleTtsLanguageChange = (newTargetLang) => {
    setTtsLanguage(newTargetLang);
    const originalText = (phase2Payload && phase2Payload.transcript) || finalTranscripts.join(' ') || '';
    if (originalText.trim()) {
      fetchTranslation(originalText, newTargetLang, detectedLanguage);
    }
  };

  // Text-To-Speech (TTS) using Gnani Timbre v2.5 with translated text
  const handlePlayTTS = async () => {
    const originalText = (phase2Payload && phase2Payload.transcript) || finalTranscripts.join(' ') || '';
    if (!originalText.trim()) {
      setTtsError('No transcript available to synthesize.');
      return;
    }

    if (ttsPlaying && audioElementRef.current) {
      audioElementRef.current.pause();
      setTtsPlaying(false);
      return;
    }

    setTtsLoading(true);
    setTtsError('');

    try {
      const srcLang = detectedLanguage || (selectedLanguage !== 'indic-auto' ? selectedLanguage : 'kn-IN');
      let textToSpeak = '';

      if (ttsLanguage === srcLang) {
        textToSpeak = originalText.trim();
      } else {
        // Must use translated text for foreign language
        if (translatedText && translatedText.trim() && !translationWarning) {
          textToSpeak = translatedText.trim();
        } else {
          // Attempt translation now
          const transRes = await fetch(`${API_BASE}/api/voice/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: originalText.trim(),
              source_language: srcLang,
              target_language: ttsLanguage
            })
          });
          if (transRes.ok) {
            const transData = await transRes.json();
            if (transData.success && transData.translated_text) {
              textToSpeak = transData.translated_text.trim();
              setTranslatedText(textToSpeak);
              setTranslationEngine(transData.engine_used || 'indic-translator');
            }
          }
        }

        if (!textToSpeak) {
          const targetLangName = TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.name || ttsLanguage;
          throw new Error(`Cannot play audio: Translation into ${targetLangName} is not available. Will not play original text under wrong language voice.`);
        }
      }

      const langConfig = TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage) || TEN_INDIAN_LANGUAGES[0];
      const res = await fetch(`${API_BASE}/api/voice/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          language: ttsLanguage,
          voice: langConfig.defaultVoice,
          speed: 1.0
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `TTS request failed with status ${res.status}`);
      }

      const engineHeader = res.headers.get('X-Engine') || 'gnani_timbre_v2.5';
      setTtsEngine(engineHeader);

      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;

      audio.onplay = () => setTtsPlaying(true);
      audio.onended = () => {
        setTtsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => {
        setTtsPlaying(false);
        setTtsError('Audio playback failed.');
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
    } catch (err) {
      console.error('TTS error:', err);
      setTtsError(`TTS error: ${err.message}`);
    } finally {
      setTtsLoading(false);
    }
  };

  const fullLiveText = finalTranscripts.length > 0 ? finalTranscripts.join(' ') : '';

  return (
    <div style={styles.card}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>ಧ್ವನಿ ದಾಖಲೆ / Voice Field Register</h2>
          <p style={styles.subtitle}>
            ASHA Sahayak – 10 Indian Languages • STT: Prisma v3.0 • TTS: Timbre v2.5
          </p>
        </div>
        <div style={styles.badgeContainer}>
          {activeEngine === 'gnani_prisma_v3' && !isSimulation && (
            <span style={styles.activeEngineBadge}>
              <Sparkles size={14} style={{ marginRight: 4 }} />
              Gnani Prisma v3.0 Live
            </span>
          )}
          {isSimulation && (
            <span style={styles.mockEngineBadge}>
              <Info size={14} style={{ marginRight: 4 }} />
              SIMULATION FALLBACK (Offline Mock)
            </span>
          )}
        </div>
      </div>

      {/* Mic Device Diagnostic Label */}
      {micDeviceLabel && (
        <div style={styles.micInfoBar}>
          <span style={styles.micInfoText}>
            🎤 ಮೈಕ್ರೊಫೋನ್ / Mic: <strong>{micDeviceLabel}</strong>
          </span>
        </div>
      )}

      {/* STT Input Language Selector */}
      <div style={styles.languageSection}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={styles.langLabel}>
            <Languages size={15} style={{ verticalAlign: 'middle', marginRight: 5 }} />
            ಧ್ವನಿ ಇನ್ಪುಟ್ ಭಾಷೆ / Speech Recognition Language (STT):
          </label>
          {detectedLanguage && (
            <span style={styles.detectedBadge}>
              ಗುರುತಿಸಿದ ಭಾಷೆ / Detected: <strong>{detectedLanguage}</strong>
            </span>
          )}
        </div>
        <select
          value={selectedLanguage}
          disabled={recordingState === 'recording' || recordingState === 'processing'}
          onChange={(e) => setSelectedLanguage(e.target.value)}
          style={styles.select}
        >
          <optgroup label="ಸ್ವಯಂಚಾಲಿತ / Automatic & Code-Mixed">
            <option value="indic-auto">✨ Auto-Detect (Indic Auto - 10 Indian Languages)</option>
            <option value="kn-IN,en-IN">Kannada + English (ಮಿಶ್ರ / Code-Mixed)</option>
            <option value="hi-IN,en-IN">Hindi + English (हिंग्लिश / Code-Mixed)</option>
          </optgroup>
          <optgroup label="10 Indian Languages (Gnani Documented)">
            {TEN_INDIAN_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name} ({lang.code})
              </option>
            ))}
          </optgroup>
        </select>

        {/* Transcription Mode Selector (Code-mix vs Clean Native Script) */}
        <div style={{ marginTop: '10px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <label style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>
            ಮೋಡ್ / Mode:
          </label>
          <button
            type="button"
            disabled={recordingState === 'recording' || recordingState === 'processing'}
            onClick={() => setSttFormat('codemix')}
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: sttFormat === 'codemix' ? '700' : '500',
              backgroundColor: sttFormat === 'codemix' ? '#0284c7' : '#f1f5f9',
              color: sttFormat === 'codemix' ? '#ffffff' : '#475569',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            🔀 Code-Mix (ಮಿಶ್ರ - Preserves English Terms)
          </button>
          <button
            type="button"
            disabled={recordingState === 'recording' || recordingState === 'processing'}
            onClick={() => setSttFormat('transcribe')}
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: sttFormat === 'transcribe' ? '700' : '500',
              backgroundColor: sttFormat === 'transcribe' ? '#0284c7' : '#f1f5f9',
              color: sttFormat === 'transcribe' ? '#ffffff' : '#475569',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            📝 Clean Script (ಶುದ್ಧ ಲಿಪಿ)
          </button>
        </div>

        {/* Medical Keyterms Boosting Controls */}
        <div style={{ marginTop: '8px', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>
            ವೈದ್ಯಕೀಯ ಶಬ್ದಕೋಶ / Vocabulary Hints:
          </label>
          <button
            type="button"
            disabled={recordingState === 'recording' || recordingState === 'processing'}
            onClick={() => setEnableKeyterms(!enableKeyterms)}
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: enableKeyterms ? '700' : '500',
              backgroundColor: enableKeyterms ? '#059669' : '#f1f5f9',
              color: enableKeyterms ? '#ffffff' : '#64748b',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            {enableKeyterms ? '✓ Keyterms Prompting ON' : '✕ Keyterms Prompting OFF'}
          </button>
          {enableKeyterms && (
            <select
              value={keytermDomain}
              disabled={recordingState === 'recording' || recordingState === 'processing'}
              onChange={(e) => setKeytermDomain(e.target.value)}
              style={{
                padding: '4px 8px',
                fontSize: '11px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#ffffff',
                color: '#334155',
                cursor: 'pointer'
              }}
            >
              <option value="general">Core Field Vocabulary (20 terms)</option>
              <option value="maternal">Maternal & ANC (ಗರ್ಭಿಣಿ)</option>
              <option value="vaccination">Immunization & Vaccines (ಲಸಿಕೆ)</option>
              <option value="newborn">Newborn & Infant Care (ಶಿಶು)</option>
              <option value="vitals">Vitals & Symptoms (ಬಿಪಿ/ಜ್ವರ)</option>
            </select>
          )}
        </div>
      </div>

      {/* Recording Control Area */}
      <div style={styles.controlsArea}>
        <div style={styles.micButtonContainer}>
          {recordingState === 'recording' ? (
            <button
              onClick={stopRecording}
              style={{ ...styles.bigButton, ...styles.recordActive }}
              className="pulsing-mic"
              title="Stop Recording"
              aria-label="Stop Recording"
            >
              <Square size={36} fill="#ffffff" color="#ffffff" />
            </button>
          ) : (
            <button
              onClick={startRecording}
              disabled={recordingState === 'processing' || recordingState === 'requesting'}
              style={{
                ...styles.bigButton,
                ...styles.recordIdle,
                opacity: recordingState === 'requesting' ? 0.7 : 1
              }}
              title="Start Recording"
              aria-label="Start Recording"
            >
              <Mic size={40} color="#ffffff" />
            </button>
          )}
        </div>

        {/* Status Indicator & Timer */}
        <div style={styles.statusRow}>
          <div style={styles.statusIndicator}>
            <span
              style={{
                ...styles.statusDot,
                backgroundColor:
                  recordingState === 'recording'
                    ? '#ef4444'
                    : recordingState === 'processing'
                    ? '#eab308'
                    : recordingState === 'completed'
                    ? '#22c55e'
                    : recordingState === 'no_speech'
                    ? '#f97316'
                    : '#94a3b8'
              }}
            />
            <span style={styles.statusText}>
              {recordingState === 'idle' && 'ರೆಕಾರ್ಡಿಂಗ್ ಪ್ರಾರಂಭಿಸಲು ಮೈಕ್ ಒತ್ತಿರಿ / Tap mic to start'}
              {recordingState === 'requesting' && 'ಮೈಕ್ರೊಫೋನ್ ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ... / Connecting mic...'}
              {recordingState === 'recording' && 'ಆಲಿಸಲಾಗುತ್ತಿದೆ... / Listening (Speaking now)'}
              {recordingState === 'processing' && 'ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ... / Processing final audio...'}
              {recordingState === 'completed' && 'ಪೂರ್ಣಗೊಂಡಿದೆ / Recognition Completed'}
              {recordingState === 'no_speech' && 'ಧ್ವನಿ ಪತ್ತೆಯಾಗಿಲ್ಲ / No Speech Detected'}
              {recordingState === 'error' && 'ದೋಷ ಸಂಭವಿಸಿದೆ / Error'}
            </span>
          </div>

          <div style={styles.timer}>{formatTime(timerSeconds)}</div>
        </div>

        {/* Live Audio Level Meter */}
        {recordingState === 'recording' && (
          <div style={styles.audioMeterContainer}>
            <Volume2 size={16} color="#64748b" style={{ marginRight: 8 }} />
            <div style={styles.audioMeterTrack}>
              <div
                style={{
                  ...styles.audioMeterFill,
                  width: `${audioLevel}%`,
                  backgroundColor: audioLevel > 75 ? '#ef4444' : audioLevel > 25 ? '#22c55e' : '#3b82f6'
                }}
              />
            </div>
            <span style={styles.audioLevelText}>{audioLevel}%</span>
          </div>
        )}

        {/* Quality or Noise Warning Banner */}
        {qualityWarning && recordingState === 'recording' && (
          <div style={styles.warningAlert}>
            <AlertCircle size={16} color="#b45309" style={{ flexShrink: 0, marginRight: 8 }} />
            <span style={styles.alertText}>{qualityWarning}</span>
          </div>
        )}

        {/* Simulation Notice Banner if in fallback */}
        {isSimulation && (
          <div style={styles.simulationBanner}>
            <Info size={16} color="#b45309" style={{ flexShrink: 0, marginRight: 8 }} />
            <span style={styles.simulationText}>
              ⚠️ <strong>SIMULATION MODE:</strong> Offline fallback active. Real Gnani speech recognition is not connected.
            </span>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div style={styles.errorAlert}>
            <AlertCircle size={18} color="#b91c1c" style={{ flexShrink: 0, marginRight: 8 }} />
            <span style={styles.alertText}>{errorMessage}</span>
          </div>
        )}

        {/* Retry Recording Button when session was silent or errored */}
        {(recordingState === 'no_speech' || recordingState === 'error') && (
          <div style={{ textAlign: 'center', marginTop: 12 }}>
            <button
              onClick={startRecording}
              style={{
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 18px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                boxShadow: '0 2px 6px rgba(2, 132, 199, 0.25)'
              }}
            >
              <RefreshCw size={15} style={{ marginRight: 6 }} />
              ಮತ್ತೆ ಮಾತನಾಡಿ / Retry Recording
            </button>
          </div>
        )}
      </div>

      {/* Live Transcript Display Box */}
      <div style={styles.transcriptBox}>
        <div style={styles.transcriptHeader}>
          <span style={styles.transcriptLabel}>ಪ್ರಸ್ತುತ ಪಠ್ಯ / Live Transcript</span>
          {fullLiveText && (
            <button onClick={handleCopyTranscript} style={styles.iconButton} title="Copy Transcript">
              {isCopied ? <CheckCircle size={16} color="#16a34a" /> : <Copy size={16} color="#475569" />}
              <span style={{ marginLeft: 4 }}>{isCopied ? 'ಪ್ರತಿಯಾಗಿದೆ / Copied' : 'ನಕಲಿಸಿ / Copy'}</span>
            </button>
          )}
        </div>

        <div style={styles.transcriptContent}>
          {fullLiveText || interimTranscript ? (
            <p style={styles.transcriptParagraph}>
              <span style={styles.finalText}>{fullLiveText}</span>
              {interimTranscript && (
                <span style={styles.interimText}> {interimTranscript}</span>
              )}
            </p>
          ) : recordingState === 'completed' ? (
            <p style={{ ...styles.placeholderText, color: '#64748b', fontStyle: 'italic' }}>
              🔇 ಯಾವುದೇ ಧ್ವನಿ ಪತ್ತೆಯಾಗಿಲ್ಲ (ಮೌನ) / No speech detected in recorded audio.
              <br />
              (ದಯವಿಟ್ಟು ಮೈಕ್ರೊಫೋನ್‌ಗೆ ಹತ್ತಿರವಾಗಿ ಮಾತನಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ / Please speak closer to the microphone and try again.)
            </p>
          ) : (
            <p style={styles.placeholderText}>
              ನೀವು ಮಾತನಾಡುವಾಗ ಪಠ್ಯವು ಇಲ್ಲಿ ನೈಜ ಸಮಯದಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತದೆ...
              <br />
              (Spoken text will appear here in real-time as you speak in any of the 10 Indian languages...)
            </p>
          )}
        </div>
      </div>

      {/* Text-To-Speech (TTS) & Multilingual Translation Section - Gnani Timbre v2.5 */}
      {(fullLiveText || (phase2Payload && phase2Payload.transcript)) && (
        <div style={styles.ttsSection}>
          <div style={styles.ttsHeader}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Languages size={18} color="#0284c7" style={{ marginRight: 6 }} />
              <h4 style={styles.ttsTitle}>ಧ್ವನಿ ಅನುವಾದ ಮತ್ತು ಓದಿ / Multilingual Translation & Voice Output</h4>
            </div>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              {translationEngine && (
                <span style={{ fontSize: '11px', fontWeight: '600', backgroundColor: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: '12px' }}>
                  {translationEngine === 'neural-indic-translator' ? '✨ Neural Indic' : '✓ Clinical Fallback'}
                </span>
              )}
              {ttsEngine && (
                <span style={ttsEngine === 'gnani_timbre_v2.5' ? styles.activeEngineBadge : styles.mockEngineBadge}>
                  {ttsEngine === 'gnani_timbre_v2.5' ? 'Timbre v2.5 Live' : 'Mock Fallback'}
                </span>
              )}
            </div>
          </div>

          {/* Input & Output Language Status Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: '500' }}>ಇನ್ಪುಟ್ ಭಾಷೆ / Detected Input Language:</span>
              <span style={{ fontSize: '12px', fontWeight: '700', backgroundColor: '#f1f5f9', color: '#0f172a', padding: '2px 8px', borderRadius: '6px' }}>
                {detectedLanguage ? (TEN_INDIAN_LANGUAGES.find((l) => l.code === detectedLanguage)?.name || detectedLanguage) : 'Kannada (ಕನ್ನಡ)'}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: '500' }}>ಔಟ್‌ಪುಟ್ ಧ್ವನಿ / Active Voice:</span>
              <span style={{ fontSize: '12px', fontWeight: '700', backgroundColor: '#f0fdf4', color: '#166534', padding: '2px 8px', borderRadius: '6px' }}>
                {TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.defaultVoice || 'Devika'} ({TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.name})
              </span>
            </div>
          </div>

          {/* Original Transcript Box (Preserved) */}
          <div style={{ marginBottom: '12px', backgroundColor: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
              ಮೂಲ ಪ್ರತಿ / Original Transcript:
            </div>
            <div style={{ fontSize: '14px', color: '#1e293b', lineHeight: 1.5 }}>
              {fullLiveText || (phase2Payload && phase2Payload.transcript)}
            </div>
          </div>

          {/* Output Language Selector & Action Controls */}
          <div style={styles.ttsControls}>
            <div style={{ flex: 1 }}>
              <label style={styles.ttsLangLabel}>ಔಟ್‌ಪುಟ್ ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ / Select Output Language:</label>
              <select
                value={ttsLanguage}
                onChange={(e) => handleTtsLanguageChange(e.target.value)}
                style={styles.ttsSelect}
              >
                {TEN_INDIAN_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} (ಧ್ವನಿ / Voice: {lang.defaultVoice})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handlePlayTTS}
              disabled={ttsLoading || isTranslating}
              style={{
                ...styles.ttsPlayButton,
                backgroundColor: ttsPlaying ? '#ef4444' : '#0284c7'
              }}
            >
              {ttsLoading ? (
                <span>ಉತ್ಪಾದಿಸಲಾಗುತ್ತಿದೆ... / Generating Audio...</span>
              ) : isTranslating ? (
                <span>ಅನುವಾದಿಸಲಾಗುತ್ತಿದೆ... / Translating...</span>
              ) : ttsPlaying ? (
                <>
                  <Pause size={16} style={{ marginRight: 6 }} />
                  <span>ನಿಲ್ಲಿಸಿ / Stop Voice</span>
                </>
              ) : (
                <>
                  <Volume2 size={16} style={{ marginRight: 6 }} />
                  <span>ಧ್ವನಿ ಆಲಿಸಿ / Listen ({TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.defaultVoice})</span>
                </>
              )}
            </button>
          </div>

          {/* Translated Transcript Box */}
          <div style={{ marginTop: '12px', backgroundColor: '#eff6ff', padding: '12px', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#1d4ed8' }}>
                ಅನುವಾದಿತ ಪ್ರತಿ / Translated Transcript ({TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.name}):
              </span>
              {isTranslating && (
                <span style={{ fontSize: '11px', color: '#2563eb', fontStyle: 'italic' }}>
                  ಅನುವಾದಿಸಲಾಗುತ್ತಿದೆ... / Translating...
                </span>
              )}
            </div>
            <div style={{ fontSize: '15px', color: '#0f172a', fontWeight: '500', lineHeight: 1.6 }}>
              {isTranslating ? (
                <span style={{ color: '#64748b', fontStyle: 'italic' }}>
                  Translating transcript to {TEN_INDIAN_LANGUAGES.find((l) => l.code === ttsLanguage)?.name}...
                </span>
              ) : translatedText ? (
                <span>{translatedText}</span>
              ) : translationWarning ? (
                <span style={{ color: '#dc2626', fontSize: '13px', fontStyle: 'italic' }}>
                  {translationWarning}
                </span>
              ) : (
                <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>
                  {ttsLanguage === (detectedLanguage || selectedLanguage || 'kn-IN') ? (fullLiveText || (phase2Payload && phase2Payload.transcript)) : 'Select Listen to translate and synthesize.'}
                </span>
              )}
            </div>
            {translationUncertain && translationWarning && (
              <div style={{ marginTop: '8px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', padding: '6px 10px', borderRadius: '6px', display: 'flex', alignItems: 'center' }}>
                <AlertCircle size={15} color="#dc2626" style={{ marginRight: 6, flexShrink: 0 }} />
                <span style={{ fontSize: '11px', color: '#b91c1c', fontWeight: '600' }}>
                  ⚠️ ಮಾನವ ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ / Review Required: {translationWarning}
                </span>
              </div>
            )}
          </div>

          {ttsError && (
            <div style={{ ...styles.errorAlert, width: '100%', marginTop: '8px' }}>
              <AlertCircle size={16} color="#b91c1c" style={{ marginRight: 6 }} />
              <span style={styles.alertText}>{ttsError}</span>
            </div>
          )}
        </div>
      )}

      {/* Completed Phase 2 Output Handoff Card */}
      {phase2Payload && (
        <div style={styles.phase2Card}>
          <div style={styles.phase2Header}>
            <CheckCircle size={20} color="#16a34a" style={{ marginRight: 8 }} />
            <h4 style={styles.phase2Title}>Phase 2 Handoff Payload (Common JSON Contract)</h4>
          </div>

          {/* Reviewable Verified Medical Normalizations (Preserves raw transcript separately) */}
          {phase2Payload.corrections_applied && phase2Payload.corrections_applied.length > 0 && (
            <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '12px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#166534' }}>
                  ✓ ವೈದ್ಯಕೀಯ ಪದ ಪ್ರಮಾಣೀಕರಣ / Verified Normalization ({phase2Payload.corrections_applied.length} applied):
                </span>
                {phase2Payload.raw_transcript && (
                  <button
                    type="button"
                    onClick={() => setShowRawTranscript((prev) => !prev)}
                    style={{ background: 'none', border: 'none', color: '#0284c7', fontSize: '11px', fontWeight: '600', cursor: 'pointer', textDecoration: 'underline' }}
                  >
                    {showRawTranscript ? 'ಪ್ರಮಾಣಿತ ಪ್ರತಿ / Standardized' : 'ಮೂಲ ಪ್ರತಿ / Raw ASR'}
                  </button>
                )}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
                {phase2Payload.corrections_applied.map((c, i) => (
                  <span key={i} style={{ backgroundColor: '#ffffff', border: '1px solid #86efac', borderRadius: '4px', padding: '2px 6px', fontSize: '11px', color: '#15803d' }}>
                    <span style={{ textDecoration: 'line-through', opacity: 0.6 }}>{c.original}</span> → <strong>{c.normalized}</strong>
                  </span>
                ))}
              </div>
              {showRawTranscript && phase2Payload.raw_transcript && (
                <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic', marginTop: '4px', backgroundColor: '#ffffff', padding: '6px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <strong>ಮೂಲ ಪ್ರತಿ / Raw ASR Transcript:</strong> "{phase2Payload.raw_transcript}"
                </div>
              )}
            </div>
          )}

          {/* Clinical Markers Badge Row (Measurements, Negations, Vaccines) */}
          {phase2Payload.clinical_markers && phase2Payload.clinical_markers.detected_markers && phase2Payload.clinical_markers.detected_markers.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
              {phase2Payload.clinical_markers.detected_markers.map((marker, idx) => (
                <span key={idx} style={{ backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', borderRadius: '12px', padding: '2px 8px', fontSize: '11px', fontWeight: '600' }}>
                  ✓ {marker}
                </span>
              ))}
            </div>
          )}

          <pre style={styles.jsonPreview}>{JSON.stringify(phase2Payload, null, 2)}</pre>

          {phase2Error && (
            <div style={{ padding: '8px 12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, color: '#dc2626', fontSize: 13, marginBottom: 10 }}>
              ⚠️ {phase2Error}
            </div>
          )}

          {handoffSuccess && sentRecordId && (
            <div style={{ padding: '8px 12px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, color: '#16a34a', fontSize: 13, marginBottom: 10 }}>
              ✅ Transcript successfully saved to database & transferred to Phase 2 (Record ID: <strong>{sentRecordId}</strong>).
            </div>
          )}

          <div style={styles.phase2Actions}>
            <button
              onClick={handleSendToPhase2}
              disabled={isSendingToPhase2 || handoffSuccess}
              style={{
                ...styles.sendButton,
                backgroundColor: handoffSuccess ? '#16a34a' : (isSendingToPhase2 ? '#94a3b8' : '#0284c7'),
                cursor: (isSendingToPhase2 || handoffSuccess) ? 'default' : 'pointer'
              }}
            >
              <Send size={16} style={{ marginRight: 6 }} />
              {isSendingToPhase2
                ? 'Phase 2 ಗೆ ವರ್ಗಾಯಿಸಲಾಗುತ್ತಿದೆ... / Sending...'
                : (handoffSuccess
                  ? 'Phase 2 ಗೆ ಕಳುಹಿಸಲಾಗಿದೆ / Sent to Phase 2!'
                  : 'Phase 2 ಗೆ ಕಳುಹಿಸಿ / Send to Phase 2')}
            </button>

            <button
              onClick={() => {
                setRecordingState('idle');
                setPhase2Payload(null);
                setFinalTranscripts([]);
                setInterimTranscript('');
                setDetectedLanguage(null);
                setTranslatedText('');
                setTranslationEngine('');
                setIsTranslating(false);
                setTranslationUncertain(false);
                setTranslationWarning('');
                setHandoffSuccess(false);
                setPhase2Error('');
                setSentRecordId('');
                if (audioElementRef.current) {
                  audioElementRef.current.pause();
                }
                setTtsPlaying(false);
              }}
              style={styles.resetButton}
            >
              <RefreshCw size={16} style={{ marginRight: 6 }} />
              ಹೊಸ ಭೇಟಿ / New Visit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    maxWidth: '680px',
    margin: '0 auto',
    backgroundColor: '#ffffff',
    borderRadius: '16px',
    boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.08), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
    padding: '24px',
    boxSizing: 'border-box'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '14px',
    borderBottom: '1px solid #f1f5f9',
    paddingBottom: '12px'
  },
  title: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#0f172a',
    margin: 0
  },
  subtitle: {
    fontSize: '12px',
    color: '#64748b',
    marginTop: '4px'
  },
  badgeContainer: {
    display: 'flex',
    alignItems: 'center'
  },
  activeEngineBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    backgroundColor: '#ecfdf5',
    color: '#047857',
    borderRadius: '9999px',
    fontSize: '11px',
    fontWeight: '600',
    border: '1px solid #a7f3d0'
  },
  mockEngineBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    backgroundColor: '#fffbeb',
    color: '#b45309',
    borderRadius: '9999px',
    fontSize: '11px',
    fontWeight: '600',
    border: '1px solid #fde68a'
  },
  micInfoBar: {
    backgroundColor: '#f1f5f9',
    borderRadius: '6px',
    padding: '4px 10px',
    marginBottom: '12px'
  },
  micInfoText: {
    fontSize: '11px',
    color: '#475569'
  },
  languageSection: {
    marginBottom: '18px'
  },
  langLabel: {
    display: 'block',
    fontSize: '13px',
    fontWeight: '600',
    color: '#334155',
    marginBottom: '6px'
  },
  detectedBadge: {
    fontSize: '11px',
    color: '#0369a1',
    backgroundColor: '#e0f2fe',
    padding: '2px 8px',
    borderRadius: '4px'
  },
  select: {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid #cbd5e1',
    backgroundColor: '#f8fafc',
    fontSize: '14px',
    color: '#1e293b',
    outline: 'none',
    cursor: 'pointer'
  },
  controlsArea: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '18px 0',
    backgroundColor: '#f8fafc',
    borderRadius: '12px',
    marginBottom: '18px'
  },
  micButtonContainer: {
    margin: '8px 0'
  },
  bigButton: {
    width: '84px',
    height: '84px',
    borderRadius: '50%',
    border: 'none',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
  },
  recordIdle: {
    backgroundColor: '#0284c7'
  },
  recordActive: {
    backgroundColor: '#ef4444'
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '90%',
    marginTop: '10px'
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center'
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    marginRight: '8px'
  },
  statusText: {
    fontSize: '13px',
    fontWeight: '500',
    color: '#475569'
  },
  timer: {
    fontFamily: 'monospace',
    fontSize: '15px',
    fontWeight: '700',
    color: '#1e293b',
    backgroundColor: '#e2e8f0',
    padding: '2px 8px',
    borderRadius: '6px'
  },
  audioMeterContainer: {
    display: 'flex',
    alignItems: 'center',
    width: '85%',
    marginTop: '10px'
  },
  audioMeterTrack: {
    flex: 1,
    height: '8px',
    backgroundColor: '#e2e8f0',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  audioMeterFill: {
    height: '100%',
    transition: 'width 0.1s ease'
  },
  audioLevelText: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#64748b',
    marginLeft: '8px',
    minWidth: '32px'
  },
  warningAlert: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#fffbeb',
    border: '1px solid #fef3c7',
    borderRadius: '8px',
    padding: '8px 12px',
    marginTop: '10px',
    width: '90%'
  },
  simulationBanner: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#fffbeb',
    border: '1px solid #fde68a',
    borderRadius: '8px',
    padding: '8px 12px',
    marginTop: '10px',
    width: '90%'
  },
  simulationText: {
    fontSize: '11px',
    color: '#92400e',
    lineHeight: '1.4'
  },
  errorAlert: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#fef2f2',
    border: '1px solid #fee2e2',
    borderRadius: '8px',
    padding: '10px 14px',
    marginTop: '10px',
    width: '90%'
  },
  alertText: {
    fontSize: '12px',
    color: '#991b1b',
    lineHeight: '1.4'
  },
  transcriptBox: {
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    overflow: 'hidden',
    marginBottom: '16px'
  },
  transcriptHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f1f5f9',
    padding: '10px 16px',
    borderBottom: '1px solid #e2e8f0'
  },
  transcriptLabel: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#334155'
  },
  iconButton: {
    display: 'inline-flex',
    alignItems: 'center',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: '500',
    color: '#475569',
    padding: '4px 8px',
    borderRadius: '4px'
  },
  transcriptContent: {
    padding: '16px',
    minHeight: '90px',
    backgroundColor: '#ffffff'
  },
  transcriptParagraph: {
    fontSize: '15px',
    lineHeight: '1.6',
    color: '#0f172a',
    margin: 0
  },
  finalText: {
    fontWeight: '500'
  },
  interimText: {
    color: '#64748b',
    fontStyle: 'italic'
  },
  placeholderText: {
    color: '#94a3b8',
    fontSize: '13px',
    textAlign: 'center',
    marginTop: '16px',
    fontStyle: 'italic'
  },
  ttsSection: {
    backgroundColor: '#f0f9ff',
    border: '1px solid #bae6fd',
    borderRadius: '12px',
    padding: '14px 16px',
    marginBottom: '16px'
  },
  ttsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px'
  },
  ttsTitle: {
    fontSize: '13px',
    fontWeight: '700',
    color: '#0369a1',
    margin: 0
  },
  ttsControls: {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-end'
  },
  ttsLangLabel: {
    display: 'block',
    fontSize: '12px',
    fontWeight: '600',
    color: '#075985',
    marginBottom: '4px'
  },
  ttsSelect: {
    width: '100%',
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #7dd3fc',
    backgroundColor: '#ffffff',
    fontSize: '13px',
    color: '#0f172a',
    outline: 'none',
    cursor: 'pointer'
  },
  ttsPlayButton: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '9px 18px',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'background-color 0.2s ease'
  },
  phase2Card: {
    backgroundColor: '#f8fafc',
    border: '1px solid #cbd5e1',
    borderRadius: '12px',
    padding: '16px'
  },
  phase2Header: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '10px'
  },
  phase2Title: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#0f172a',
    margin: 0
  },
  jsonPreview: {
    backgroundColor: '#0f172a',
    color: '#38bdf8',
    padding: '12px',
    borderRadius: '8px',
    fontSize: '12px',
    fontFamily: 'monospace',
    overflowX: 'auto',
    marginBottom: '14px'
  },
  phase2Actions: {
    display: 'flex',
    gap: '10px'
  },
  sendButton: {
    flex: 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 16px',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease'
  },
  resetButton: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 16px',
    backgroundColor: '#ffffff',
    color: '#334155',
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer'
  }
};
