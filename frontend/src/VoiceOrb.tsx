import { useEffect, useRef, type RefObject } from 'react';

type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'approval';

const goldenAngle = Math.PI * (3 - Math.sqrt(5));
const points = Array.from({ length: 1160 }, (_, index) => {
  const y = 1 - 2 * (index + 0.5) / 1160;
  const ring = Math.sqrt(1 - y * y);
  return { x: ring * Math.cos(index * goldenAngle), y, z: ring * Math.sin(index * goldenAngle) };
});

const colors: Record<VoiceState, [number, number, number]> = {
  idle: [83, 195, 254],
  listening: [75, 250, 222],
  thinking: [139, 157, 255],
  speaking: [93, 238, 255],
  approval: [255, 194, 124],
};

export function VoiceOrb({ state, level }: { state: VoiceState; level: RefObject<number> }) {
  const stage = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const mode = useRef(state);

  useEffect(() => { mode.current = state; }, [state]);

  useEffect(() => {
    const surface = stage.current;
    const output = canvas.current;
    const pen = output?.getContext('2d');
    if (!surface || !output || !pen) return;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let width = 0;
    let height = 0;
    let targetX = 0;
    let targetY = 0;
    let tiltX = 0;
    let tiltY = 0;
    let energy = 0;
    let frame = 0;

    function resize() {
      const box = output!.getBoundingClientRect();
      const density = Math.min(window.devicePixelRatio || 1, 2);
      width = box.width;
      height = box.height;
      output!.width = Math.round(width * density);
      output!.height = Math.round(height * density);
      pen!.setTransform(density, 0, 0, density, 0, 0);
    }

    const observer = new ResizeObserver(resize);
    observer.observe(output);
    resize();

    function point(event: PointerEvent) {
      const box = surface!.getBoundingClientRect();
      targetX = (event.clientX - box.left) / box.width - 0.5;
      targetY = (event.clientY - box.top) / box.height - 0.5;
    }
    function reset() { targetX = 0; targetY = 0; }
    surface.addEventListener('pointermove', point);
    surface.addEventListener('pointerleave', reset);

    function draw(now: number) {
      const still = motion.matches;
      const t = still ? 0 : now / 1000;
      const active = mode.current === 'listening' || mode.current === 'speaking';
      const nextEnergy = still ? 0 : active ? level.current : mode.current === 'thinking' ? 0.16 : 0;
      energy += (nextEnergy - energy) * 0.16;
      tiltX += ((still ? 0 : targetX) - tiltX) * 0.1;
      tiltY += ((still ? 0 : targetY) - tiltY) * 0.1;
      surface!.style.setProperty('--energy', energy.toFixed(3));
      surface!.style.setProperty('--glow-x', (50 + tiltX * 26).toFixed(1) + '%');
      surface!.style.setProperty('--glow-y', (49 + tiltY * 20).toFixed(1) + '%');
      pen!.clearRect(0, 0, width, height);
      const angle = t * 0.24 + tiltX * 1.0;
      const pitch = -0.18 - tiltY * 0.6;
      const ca = Math.cos(angle);
      const sa = Math.sin(angle);
      const cp = Math.cos(pitch);
      const sp = Math.sin(pitch);
      const radius = Math.min(width, height) * 0.37;
      const centerX = width * 0.5 + tiltX * 16;
      const centerY = height * 0.49 + tiltY * 13;
      const [red, green, blue] = colors[mode.current];

      for (const dot of points) {
        const x = dot.x * ca - dot.z * sa;
        const depth = dot.x * sa + dot.z * ca;
        const y = dot.y * cp - depth * sp;
        const z = dot.y * sp + depth * cp;
        const ripple = Math.sin(dot.y * 14 + dot.x * 7 + t * 8);
        const stretch = 1 + energy * (0.09 + ripple * 0.16) + Math.sin(t * 1.7) * 0.012;
        const perspective = 1 / (1 - z * 0.17);
        const size = 0.58 + (z + 1) * 0.48 + energy * 0.7;
        const lift = Math.max(0, -y) * 20;
        const opacity = z > 0 ? 0.42 + z * 0.53 : 0.07 + (z + 1) * 0.24;
        pen!.fillStyle = 'rgba(' + Math.min(255, red + lift) + ',' + Math.min(255, green + lift) + ',' + blue + ',' + opacity + ')';
        pen!.beginPath();
        pen!.arc(centerX + x * radius * stretch * perspective, centerY + y * radius * stretch * perspective, size, 0, 2 * Math.PI);
        pen!.fill();
      }
      frame = window.requestAnimationFrame(draw);
    }
    frame = window.requestAnimationFrame(draw);
    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      surface.removeEventListener('pointermove', point);
      surface.removeEventListener('pointerleave', reset);
    };
  }, [level]);

  return <div className="orb-stage" data-voice={state} ref={stage} aria-hidden="true">
    <div className="orb-halo" />
    <div className="orb-reticle" />
    <canvas className="orb-canvas" ref={canvas} />
  </div>;
}
