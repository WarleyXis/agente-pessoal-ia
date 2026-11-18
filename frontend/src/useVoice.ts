import { useCallback, useEffect, useRef, useState } from 'react';
import { measureLevel, prepareAudio, spokenAudio } from './audio';

export function useVoice(onError: (message: string) => void) {
  const context = useRef<AudioContext | null>(null);
  const level = useRef(0);
  const session = useRef<AbortController | null>(null);
  const source = useRef<AudioBufferSourceNode | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [preparing, setPreparing] = useState(false);

  const stop = useCallback(() => {
    session.current?.abort();
    session.current = null;
    source.current?.stop();
    source.current = null;
    level.current = 0;
    setSpeaking(false);
    setPreparing(false);
  }, []);

  useEffect(() => () => {
    session.current?.abort();
    source.current?.stop();
    void context.current?.close().catch(() => {});
  }, []);

  function prepare() {
    try { prepareAudio(context); } catch { return null; }
    return context.current;
  }

  async function play(text: string, onStarted?: (elapsed: number) => void) {
    stop();
    if (!text.trim()) return;
    const started = performance.now();
    const run = new AbortController();
    session.current = run;
    setPreparing(true);
    const finish = () => {
      if (session.current === run) {
        source.current = null;
        session.current = null;
        level.current = 0;
        setSpeaking(false);
        setPreparing(false);
      }
    };
    try {
      const audio = context.current;
      if (!audio || audio.state !== 'running') throw new Error('Áudio indisponível nesta janela. Clique em Falar com o Atlas e tente novamente.');
      // Keep the complete reply on screen and limit the spoken excerpt.
      const wav = await spokenAudio(text.slice(0, 3000), run.signal);
      const buffer = await audio.decodeAudioData(wav);
      if (run.signal.aborted) return;
      const player = audio.createBufferSource();
      const analyser = audio.createAnalyser();
      const measure = measureLevel(analyser);
      let frame = 0;
      const sample = () => {
        level.current = Math.min(1, measure() * 4);
        frame = window.requestAnimationFrame(sample);
      };
      player.buffer = buffer;
      player.connect(analyser);
      analyser.connect(audio.destination);
      player.onended = () => {
        window.cancelAnimationFrame(frame);
        player.disconnect();
        analyser.disconnect();
        finish();
      };
      player.start();
      source.current = player;
      setPreparing(false);
      setSpeaking(true);
      onStarted?.(performance.now() - started);
      sample();
    } catch (error) {
      if (run.signal.aborted) return;
      finish();
      onError(error instanceof Error ? error.message : 'A resposta apareceu no painel, mas não pôde ser reproduzida.');
    }
  }

  function setLevel(value: number) { level.current = value; }

  return { level, setLevel, speaking, preparing, prepare, play, stop };
}
