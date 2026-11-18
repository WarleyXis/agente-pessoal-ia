export function measureLevel(analyser: AnalyserNode) {
  const samples = new Float32Array(analyser.fftSize);
  return () => {
    analyser.getFloatTimeDomainData(samples);
    let energy = 0;
    for (const sample of samples) energy += sample * sample;
    return Math.sqrt(energy / samples.length);
  };
}

export function prepareAudio(context: { current: AudioContext | null }) {
  if (!window.AudioContext) return;
  if (!context.current || context.current.state === 'closed') context.current = new AudioContext();
  void context.current.resume().catch(() => {});
}

export async function spokenAudio(text: string, signal: AbortSignal) {
  const response = await fetch('/api/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
    signal,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : 'A voz local está indisponível.');
  }
  return response.arrayBuffer();
}
