import { useEffect, useRef, useState } from 'react';

interface Recording {
  recorder: MediaRecorder;
  stream: MediaStream;
  timer: number;
  cancelled: boolean;
}

export function Microphone({ disabled, onAudio, onError, onState }: {
  disabled: boolean;
  onAudio: (audio: Blob) => void;
  onError: (message: string) => void;
  onState: (recording: boolean) => void;
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
        window.clearTimeout(recording.timer);
        recording.stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  async function start() {
    setState('requesting');
    let stream: MediaStream | undefined;
    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        throw new Error('O navegador não oferece gravação de áudio neste endereço.');
      }
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!active.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      const recording = { recorder, stream, timer: 0, cancelled: false };
      current.current = recording;
      recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
      recorder.onstop = () => {
        window.clearTimeout(recording.timer);
        recording.stream.getTracks().forEach((track) => track.stop());
        current.current = null;
        if (!active.current) return;
        setState('idle');
        onState(false);
        if (!recording.cancelled && chunks.length) onAudio(new Blob(chunks, { type: recorder.mimeType || chunks[0].type }));
      };
      recorder.onerror = () => {
        recording.cancelled = true;
        if (active.current) onError('O navegador encontrou um erro ao gravar.');
      };
      recorder.start();
      recording.timer = window.setTimeout(() => {
        if (recorder.state !== 'inactive') recorder.stop();
      }, 30000);
      setState('recording');
      onState(true);
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
    if (!recording) return;
    recording.cancelled = cancelled;
    if (recording.recorder.state !== 'inactive') recording.recorder.stop();
    recording.stream.getTracks().forEach((track) => track.stop());
  }

  return state === 'recording' ? <>
    <button onClick={() => stop(false)}>Transcrever gravação</button>
    <button onClick={() => stop(true)}>Cancelar gravação</button>
  </> : <button disabled={disabled || state === 'requesting'} onClick={() => void start()}>
    {state === 'requesting' ? 'Abrindo microfone…' : 'Microfone'}
  </button>;
}
