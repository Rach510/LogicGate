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
  const [progress, setProgress] = useState(0);
  const [currentSeconds, setCurrentSeconds] = useState(0);
  const [measurement, setMeasurement] = useState<MeasurementOverlay>(metadata.activeMeasurements);
  const isVideo = metadata.mediaType === "video";
  const boundary = metadata.roadBoundary;

  useEffect(() => {
    setMeasurement(metadata.activeMeasurements);
    if (!isVideo) {
      setPlaying(false); setProgress(0); setCurrentSeconds(0);
    }
  }, [metadata.activeMeasurements, isVideo]);

  const togglePlay = async () => {
    if (!isVideo || !videoRef.current) return;
    try {
      if (videoRef.current.paused) { await videoRef.current.play(); setPlaying(true); }
      else { videoRef.current.pause(); setPlaying(false); }
    } catch { setPlaying(false); }
  };
  const handleTimeUpdate = () => {
    const element = videoRef.current;
    if (!element || !element.duration) return;
    setCurrentSeconds(element.currentTime); setProgress((element.currentTime / element.duration) * 100);
  };
  const seek = (value: number) => {
    setProgress(value);
    if (videoRef.current?.duration) videoRef.current.currentTime = (value / 100) * videoRef.current.duration;
  };
  const progressLabel = useMemo(() => {
    const total = Math.max(0, Math.floor(currentSeconds)); const minutes = Math.floor(total / 60); const seconds = total % 60;
    return `${String(minutes).padStart(2,"0")}:${String(seconds).padStart(2,"0")}`;
  }, [currentSeconds]);

  const geometryVisible = Boolean(boundary && boundary.confidence > 0);
  const leftTop = boundary?.leftTopX ?? 38; const leftBottom = boundary?.leftBottomX ?? 7;
  const rightTop = boundary?.rightTopX ?? 62; const rightBottom = boundary?.rightBottomX ?? 93;

  return <div data-testid="video-analysis-player" className={`video-stage relative overflow-hidden rounded-[28px] bg-[#16201f] shadow-2xl ${compact ? "min-h-[340px]" : "min-h-[560px] sm:min-h-[calc(100vh-180px)]"}`}>
    {isVideo && metadata.mediaUrl ? <video ref={videoRef} src={metadata.mediaUrl} muted={muted} playsInline preload="metadata" onTimeUpdate={handleTimeUpdate} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} className="absolute inset-0 h-full w-full object-cover opacity-75" /> : <img src={metadata.mediaUrl ?? bgImage ?? roadImage} alt="Uploaded road survey" className="absolute inset-0 h-full w-full object-cover opacity-75" />}
    <div className="video-tint absolute inset-0" />
    {geometryVisible && <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full" aria-label="Detected road boundary overlay">
      <path d={`M${leftTop} 38 L${leftBottom} 97 L${rightBottom} 97 L${rightTop} 38 Z`} fill="rgba(184,233,134,0.08)" stroke="rgba(184,233,134,0.92)" strokeWidth="0.3" />
      <path d={`M${leftTop} 38 L${leftBottom} 97 M${rightTop} 38 L${rightBottom} 97`} stroke="rgba(184,233,134,0.92)" strokeWidth="0.3" strokeDasharray="1 0.8" />
    </svg>}
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">
      {metadata.boxes.map((box) => <g key={`${box.label}-${box.x}-${box.y}`}><rect x={box.x} y={box.y} width={box.width} height={box.height} fill="rgba(237,111,97,0.08)" stroke="#edb06c" strokeWidth="0.28" rx="0.5" /><text x={box.x+0.5} y={Math.max(5,box.y-1)} fontSize="2.2" fill="#ffd699">{box.label} {box.confidence.toFixed(0)}%</text></g>)}
      {metadata.points.map((point) => <circle key={`${point.label}-${point.x}-${point.y}`} cx={point.x} cy={point.y} r="0.8" fill="#b8e986" stroke="#10241d" strokeWidth="0.3" />)}
    </svg>
    {measurement.roadWidth > 0 && <div className="pointer-events-none absolute left-[42%] top-[58%] rounded-md border border-[#b8e986]/60 bg-[#10241d]/80 px-2 py-1 text-[10px] font-medium text-[#d9ffc4] backdrop-blur-md">{measurement.roadWidth.toFixed(2)} m · ROAD WIDTH</div>}
    <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/10 bg-[#101918]/65 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/70 backdrop-blur-md"><span className="live-dot" /> {isVideo ? "Video analysis" : "Image analysis"}</div>
    <div className="absolute right-4 top-4"><button type="button" data-testid="video-scan-mode-button" onClick={onExpand} aria-label="Open deep analysis" className="glass-control flex h-9 w-9 items-center justify-center rounded-full text-white"><ScanLine size={15}/></button></div>
    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#08100f] via-[#08100f]/75 to-transparent px-4 pb-4 pt-20 sm:px-6 sm:pb-6">
      <div className="mb-3 flex items-end justify-between"><div><div className="text-[11px] uppercase tracking-[0.15em] text-white/45">{isVideo ? `Frame ${measurement.frame.toLocaleString("en-IN")}` : "Uploaded image"}</div><div className="mt-1 text-sm font-medium text-white">{isVideo ? "Road survey footage" : "Road survey image"}</div></div><div className="text-right"><div className="text-lg font-semibold tracking-tight text-white">{measurement.confidence.toFixed(1)}%</div><div className="text-[10px] uppercase tracking-[0.14em] text-white/40">confidence</div></div></div>
      {isVideo && <input data-testid="video-timeline-input" aria-label="Video timeline" type="range" min="0" max="100" value={progress} onChange={e=>seek(Number(e.target.value))} className="video-range w-full" />}
      {isVideo ? <div className="mt-3 flex items-center gap-3"><button type="button" data-testid="video-play-toggle-button" aria-label={playing ? "Pause road footage" : "Play road footage"} onClick={()=>void togglePlay()} className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[#0d1917]">{playing?<Pause size={15} fill="currentColor"/>:<Play size={15} fill="currentColor"/>}</button><span className="text-[11px] tabular-nums text-white/60">{progressLabel} / {metadata.duration}</span><div className="ml-auto flex items-center gap-3"><span className="hidden text-[10px] uppercase tracking-[0.14em] text-white/35 sm:inline">{metadata.resolution} · {metadata.fps} FPS</span><button type="button" onClick={()=>setMuted(v=>!v)} className="text-white/70">{muted?<VolumeX size={16}/>:<Volume2 size={16}/>}</button></div></div> : <div className="mt-3 flex items-center justify-between text-[10px] uppercase tracking-[0.14em] text-white/35"><span>Single-frame analysis</span><span>{metadata.resolution}</span></div>}
    </div>
  </div>;
}
