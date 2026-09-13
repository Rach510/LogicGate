import { useEffect, useMemo, useRef, useState } from "react";
import { Pause, Play, ScanLine, Volume2, VolumeX } from "lucide-react";
import type { MeasurementOverlay, VideoOverlayMetadata } from "@/types";

interface VideoPlayerWithOverlaysProps {
  metadata: VideoOverlayMetadata;
  compact?: boolean;
  onExpand?: () => void;
  bgImage?: string;
}

const roadImage = "https://images.unsplash.com/photo-1585652516863-fbc02c1c206e?auto=format&fit=crop&w=1800&q=88";

export function VideoPlayerWithOverlays({ metadata, compact = false, onExpand, bgImage }: VideoPlayerWithOverlaysProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(true);
  const [progress, setProgress] = useState(61);
  const [measurement, setMeasurement] = useState<MeasurementOverlay>(metadata.activeMeasurements);
  useEffect(() => {
    if (!playing) return;
    let frameId = 0;
    const tick = () => {
      setProgress((current) => (current >= 99.5 ? 0 : current + 0.035));
      setMeasurement((current) => ({ ...current, frame: current.frame >= 12870 ? 12180 : current.frame + 2, roadWidth: Number((6.84 + Math.sin(Date.now() / 2200) * 0.035).toFixed(2)), confidence: Number((94.2 + Math.sin(Date.now() / 2600) * 0.5).toFixed(1)) }));
      frameId = requestAnimationFrame(tick);
    };
    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [playing]);
  const progressLabel = useMemo(() => `${String(Math.floor(progress / 12.5)).padStart(2, "0")}:${String(Math.floor((progress % 12.5) * 4.03)).padStart(2, "0")}`, [progress]);
  return (
    <div data-testid="video-analysis-player" className={`video-stage relative overflow-hidden rounded-[28px] bg-[#16201f] shadow-2xl ${compact ? "min-h-[340px]" : "min-h-[560px] sm:min-h-[calc(100vh-180px)]"}`}>
      <video ref={videoRef} muted={muted} playsInline poster={bgImage ?? roadImage} aria-label="Road survey footage with computer vision overlays" className="absolute inset-0 h-full w-full object-cover opacity-75" />
      <div className="video-tint absolute inset-0" />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-label="Road geometry overlay">
        <path d="M39 100 L47 60 L58 60 L83 100" fill="rgba(184,233,134,0.07)" stroke="rgba(184,233,134,0.92)" strokeWidth="0.25" />
        <path d="M47 60 L39 100 M58 60 L83 100" stroke="rgba(184,233,134,0.88)" strokeWidth="0.25" strokeDasharray="1 0.8" />
        <path d="M50 78 L55 78" stroke="#f6c76d" strokeWidth="0.4" />
        {metadata.boxes.map((box) => <rect key={box.label} x={box.x} y={box.y} width={box.width} height={box.height} fill="rgba(237,111,97,0.1)" stroke="#edb06c" strokeWidth="0.28" rx="0.5" />)}
        {metadata.points.map((point) => <circle key={`${point.label}-${point.x}-${point.y}`} cx={point.x} cy={point.y} r="0.8" fill="#b8e986" stroke="#10241d" strokeWidth="0.3" />)}
      </svg>
      <div className="pointer-events-none absolute left-[42%] top-[59%] rounded-md border border-[#b8e986]/60 bg-[#10241d]/80 px-2 py-1 text-[10px] font-medium text-[#d9ffc4] backdrop-blur-md">6.84 m · ROAD WIDTH</div>
      <div className="pointer-events-none absolute left-[65%] top-[48%] rounded-md border border-[#edb06c]/50 bg-[#241b13]/80 px-2 py-1 text-[10px] font-medium text-[#ffd699] backdrop-blur-md">Pothole · 87%</div>
      <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/10 bg-[#101918]/65 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/70 backdrop-blur-md"><span className="live-dot" /> Live analysis</div>
      <div className="absolute right-4 top-4 flex gap-2"><button type="button" data-testid="video-scan-mode-button" onClick={onExpand} aria-label="Open deep analysis" className="glass-control flex h-9 w-9 items-center justify-center rounded-full text-white"><ScanLine size={15} /></button></div>
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#08100f] via-[#08100f]/70 to-transparent px-4 pb-4 pt-20 sm:px-6 sm:pb-6">
        <div className="mb-3 flex items-end justify-between"><div><div className="text-[11px] uppercase tracking-[0.15em] text-white/45">Frame {measurement.frame.toLocaleString("en-IN")}</div><div className="mt-1 text-sm font-medium text-white">NH-66 / Udupi municipal connector</div></div><div className="text-right"><div className="text-lg font-semibold tracking-tight text-white">{measurement.confidence}%</div><div className="text-[10px] uppercase tracking-[0.14em] text-white/40">confidence</div></div></div>
        <input data-testid="video-timeline-input" aria-label="Video timeline" type="range" min="0" max="100" value={progress} onChange={(event) => setProgress(Number(event.target.value))} className="video-range w-full" />
        <div className="mt-3 flex items-center gap-3"><button type="button" data-testid="video-play-toggle-button" aria-label={playing ? "Pause road footage" : "Play road footage"} onClick={() => setPlaying((current) => !current)} className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[#0d1917] transition-transform active:scale-90">{playing ? <Pause size={15} fill="currentColor" /> : <Play size={15} fill="currentColor" />}</button><span className="text-[11px] tabular-nums text-white/60">{progressLabel} / {metadata.duration}</span><div className="ml-auto flex items-center gap-3"><span className="hidden text-[10px] uppercase tracking-[0.14em] text-white/35 sm:inline">4K · {metadata.fps} FPS</span><button type="button" data-testid="video-mute-toggle-button" aria-label={muted ? "Unmute video" : "Mute video"} onClick={() => setMuted((current) => !current)} className="text-white/70 transition-transform active:scale-90">{muted ? <VolumeX size={16} /> : <Volume2 size={16} />}</button></div></div>
      </div>
    </div>
  );
}
