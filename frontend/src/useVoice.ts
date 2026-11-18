import { useCallback, useEffect, useRef, useState } from 'react';
import { measureLevel, prepareAudio, spokenAudio } from './audio';

export function useVoice(onError: (message: string) => void) {
  const context = useRef<AudioContext | null>(null);
  const level = useRef(0);
  const session = useRef<AbortController | null>(null);
  const source = useRef<AudioBufferSourceNode | null>(null);
  const [speaking, setSpeaking] = useState(false);

  const stop = useCallback(() => {
    session.current?.abort();
    session.current = null;
    source.current?.stop();
    source.current = null;
    window.speechSynthesis?.cancel();
    level.current = 0;
    setSpeaking(false);
  }, []);

  useEffect(() => () => {
    session.current?.abort();
    source.current?.stop();
    window.speechSynthesis?.cancel();
    void context.current?.close().catch(() => {});
  }, []);

  function prepare() {
    try { prepareAudio(context); } catch { return null; }
    return context.current;
  }

  async function play(text: string) {
    stop();
    if (!text.trim()) return;
    const run = new AbortController();
    session.current = run;
    setSpeaking(true);
    const finish = () => {
      if (session.current === run) {
        source.current = null;
        session.current = null;
        level.current = 0;
        setSpeaking(false);
      }
    };
    try {
      const audio = context.current;
      if (!audio || audio.state !== 'running') throw new Error('Áudio indisponível.');
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
      sample();
    } catch {
      if (run.signal.aborted) return;
      const engine = window.speechSynthesis;
      const voice = engine?.getVoices().find((item) => item.localService && /^pt[-_]?br$/i.test(item.lang));
      if (!voice || typeof SpeechSynthesisUtterance === 'undefined') {
        finish();
        onError('Voz em português do Brasil indisponível. Instale uma voz pt-BR no Windows ou leia a resposta no painel.');
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text.slice(0, 3000));
      utterance.lang = 'pt-BR';
      utterance.voice = voice;
      let lastBoundary = 0;
      let frame = 0;
      const pulse = (now: number) => {
        level.current = 0.13 + Math.max(0, 1 - (now - lastBoundary) / 230) * 0.5;
        frame = window.requestAnimationFrame(pulse);
      };
      utterance.onstart = () => {
        if (!run.signal.aborted) pulse(performance.now());
      };
      utterance.onboundary = () => { lastBoundary = performance.now(); };
      utterance.onend = () => { window.cancelAnimationFrame(frame); finish(); };
      utterance.onerror = () => {
        window.cancelAnimationFrame(frame);
        if (run.signal.aborted) return;
        finish();
        onError('A resposta apareceu no painel, mas o navegador não conseguiu reproduzir a voz.');
      };
      run.signal.addEventListener('abort', () => window.cancelAnimationFrame(frame), { once: true });
      engine.speak(utterance);
    }
  }

  function setLevel(value: number) { level.current = value; }

  return { level, setLevel, speaking, prepare, play, stop };
}
