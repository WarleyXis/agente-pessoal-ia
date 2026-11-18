import { useEffect, useRef, useState } from 'react';
import { measureLevel } from './audio';

interface Recording {
  recorder: MediaRecorder;
  stream: MediaStream;
  timer: number;
  meter: number;
  cancelled: boolean;
  source?: MediaStreamAudioSourceNode;
  analyser?: AnalyserNode;
}

function release(recording: Recording) {
  window.clearTimeout(recording.timer);
  window.cancelAnimationFrame(recording.meter);
  recording.source?.disconnect();
  recording.analyser?.disconnect();
  recording.stream.getTracks().forEach((track) => track.stop());
}

export function Microphone({ disabled, audioContext, onAudio, onError, onState, onLevel }: {
  disabled: boolean;
  audioContext: () => AudioContext | null;
  onAudio: (audio: Blob) => void;
  onError: (message: string) => void;
  onState: (recording: boolean) => void;
  onLevel: (level: number) => void;
}) {
  const current = useRef<Recording | null>(null);
  const active = useRef(true);
  const [state, setState] = useState<'idle' | 'requesting' | 'recording'>('idle');

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      const recording = current.current;
      if (recording) {
        recording.cancelled = true;
        if (recording.recorder.state !== 'inactive') recording.recorder.stop();
        release(recording);
      }
    };
  }, []);

  async function start() {
    setState('requesting');
    onState(true);
    let stream: MediaStream | undefined;
    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        throw new Error('O navegador não oferece gravação de áudio neste endereço.');
      }
      let context: AudioContext | null = null;
      try { context = audioContext(); } catch { /* Manual stop remains available. */ }
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      if (!active.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      const mimeType = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4']
        .find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      const chunks: Blob[] = [];
      const recording: Recording = { recorder, stream, timer: 0, meter: 0, cancelled: false };
      current.current = recording;
      recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
      recorder.onstop = () => {
        release(recording);
        current.current = null;
        if (!active.current) return;
        onLevel(0);
        setState('idle');
        onState(false);
        if (!recording.cancelled && chunks.length) onAudio(new Blob(chunks, { type: recorder.mimeType || chunks[0].type }));
        else if (!recording.cancelled) onError('A gravação terminou sem áudio. Tente novamente.');
      };
      recorder.onerror = () => {
        recording.cancelled = true;
        if (active.current) onError('O navegador encontrou um erro ao gravar.');
        if (recorder.state !== 'inactive') recorder.stop();
      };
      recorder.start();
      if (context) {
        try {
          recording.source = context.createMediaStreamSource(stream);
          recording.analyser = context.createAnalyser();
          recording.source.connect(recording.analyser);
          const measure = measureLevel(recording.analyser);
          const startTime = performance.now();
          let lastVoice = 0;
          let voiceFrames = 0;
          const sample = (now: number) => {
            if (recorder.state === 'inactive') return;
            const level = measure();
            onLevel(Math.min(1, level * 8));
            voiceFrames = level >= 0.018 ? voiceFrames + 1 : 0;
            if (voiceFrames >= 3) lastVoice = now;

            if (lastVoice && now - lastVoice > 850) {
              recorder.stop();
              return;
            }
            if (!lastVoice && now - startTime > 8000 && context.state === 'running') {
              recording.cancelled = true;
              onError('Não ouvi nenhuma fala. Clique em Falar e tente novamente.');
              recorder.stop();
              return;
            }
            recording.meter = window.requestAnimationFrame(sample);
          };
          recording.meter = window.requestAnimationFrame(sample);
        } catch {
          recording.source?.disconnect();
          recording.analyser?.disconnect();
        }
      }
      recording.timer = window.setTimeout(() => {
        if (recorder.state !== 'inactive') recorder.stop();
      }, 30000);
      setState('recording');
    } catch (failure) {
      stream?.getTracks().forEach((track) => track.stop());
      current.current = null;
      if (active.current) {
        setState('idle');
        onState(false);
        onError(failure instanceof Error ? failure.message : 'Microfone indisponível.');
      }
    }
  }

  function stop(cancelled: boolean) {
    const recording = current.current;
    if (!recording || recording.recorder.state === 'inactive') return;
    recording.cancelled = cancelled;
    recording.recorder.stop();
    recording.stream.getTracks().forEach((track) => track.stop());
  }

  return state === 'recording' ? <>
    <button className="voice-button" type="button" onClick={() => stop(false)}>Enviar fala</button>
    <button type="button" onClick={() => stop(true)}>Cancelar</button>
  </> : <button className="voice-button" type="button" disabled={disabled || state === 'requesting'} onClick={() => void start()}>
    {state === 'requesting' ? 'Ativando microfone…' : 'Falar com o Atlas'}
  </button>;
}
