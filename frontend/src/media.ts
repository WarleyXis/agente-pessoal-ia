export async function uploadMedia<T>(path: string, blob: Blob): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': blob.type },
    body: blob,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : 'Falha no processamento da mídia.');
  }
  return response.json();
}

export async function captureWindow(): Promise<Blob> {
  const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
  const video = document.createElement('video');
  try {
    const track = stream.getVideoTracks()[0];
    if (!track || !['window', 'browser'].includes(track.getSettings().displaySurface ?? '')) {
      throw new Error('Selecione uma janela ou uma aba no compartilhamento.');
    }
    video.muted = true;
    video.srcObject = stream;
    await video.play();
    if (!video.videoWidth || !video.videoHeight) throw new Error('A janela selecionada não forneceu imagem.');
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 1280 / video.videoWidth, 720 / video.videoHeight);
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    const context = canvas.getContext('2d');
    if (!context) throw new Error('O navegador não conseguiu capturar a janela.');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('Não foi possível criar a captura.')), 'image/png');
    });
  } finally {
    video.srcObject = null;
    stream.getTracks().forEach((track) => track.stop());
  }
}
