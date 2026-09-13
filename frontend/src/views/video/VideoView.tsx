import { useRef, useState } from "react";
import { ArrowLeft, Crosshair, Info, Ruler, Scan, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VideoPlayerWithOverlays } from "@/components/video/VideoPlayerWithOverlays";
import { videoApi } from "@/api/video";
import type { Project, VideoOverlayMetadata } from "@/types";

interface VideoViewProps { project: Project; video: VideoOverlayMetadata; bgImage?: string; onBack: () => void; }

export function VideoView({ project, video, bgImage: propBgImage, onBack }: VideoViewProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [analysing, setAnalysing] = useState(false);
  const [localVideo, setLocalVideo] = useState(video);
  const [bgImage, setBgImage] = useState<string | undefined>(propBgImage);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalysing(true);
    setBgImage(URL.createObjectURL(file));
    try {
      const result = await videoApi.uploadImage(project.id, file);
      setLocalVideo(result);
    } catch {
      alert("Analysis failed — make sure the backend is running.");
    } finally {
      setAnalysing(false);
    }
  };

  return <main data-testid="video-screen" className="app-screen min-h-svh bg-[#08100f] px-4 pb-8 pt-20 text-white sm:px-8 sm:pt-24"><div className="mx-auto max-w-[1500px]"><header className="mb-5 flex items-center justify-between"><div><button type="button" data-testid="video-back-button" onClick={onBack} className="mb-4 flex items-center gap-2 text-xs text-white/45 hover:text-white"><ArrowLeft size={14} /> Dashboard</button><h1 data-testid="video-heading" className="text-3xl font-semibold tracking-[-0.05em] sm:text-5xl">Deep analysis</h1><p className="mt-2 text-sm text-white/40">{project.name} · frame-synced road geometry</p></div><div className="flex items-center gap-2"><span className="analysis-tool-pill hidden sm:flex"><Crosshair size={13} /> Detection points</span><span className="analysis-tool-pill hidden sm:flex"><Ruler size={13} /> Measurements</span><input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleUpload} /><Button type="button" onClick={() => fileRef.current?.click()} disabled={analysing} className="h-9 rounded-xl text-xs">{analysing ? "Analysing..." : "Upload image"}</Button></div></header><div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]"><VideoPlayerWithOverlays metadata={localVideo} onExpand={() => undefined} bgImage={bgImage} /><aside className="space-y-4"><div data-testid="video-measurements-panel" className="glass-panel rounded-[25px] p-5"><div className="flex items-center justify-between"><span className="section-kicker">Measurements</span><SlidersHorizontal size={15} className="text-white/35" /></div><div className="mt-5 space-y-4">{[["Road width", `${localVideo.activeMeasurements.roadWidth} m`], ["Left lane", `${localVideo.activeMeasurements.leftLane} m`], ["Kerb-to-kerb", `${localVideo.activeMeasurements.kerbToKerb} m`], ["Confidence", `${localVideo.activeMeasurements.confidence}%`]].map(([label, value]) => <div key={label} className="flex items-end justify-between border-b border-white/[0.07] pb-3"><span className="text-xs text-white/45">{label}</span><span className="text-lg font-medium tracking-tight text-white">{value}</span></div>)}</div></div><div data-testid="video-detection-panel" className="glass-panel rounded-[25px] p-5"><div className="flex items-center gap-2"><Scan size={15} className="text-[#edb06c]" /><span className="section-kicker">Detections</span></div><div className="mt-4 space-y-3">{localVideo.boxes.map((box) => <div key={box.label} className="flex items-center justify-between"><span className="text-xs text-white/65">{box.label}</span><span className="text-[10px] uppercase tracking-[0.12em] text-[#edb06c]">{box.severity}</span></div>)}</div><div className="mt-5 flex gap-2 rounded-xl bg-white/[0.04] p-3 text-[10px] leading-4 text-white/35"><Info size={13} className="shrink-0 text-white/45" /> Overlay data is synchronized to the current analysis frame.</div></div><Button data-testid="video-export-button" type="button" variant="outline" onClick={() => undefined} className="h-10 w-full rounded-xl border-white/10 bg-white/[0.04] text-xs text-white/70 hover:bg-white/10"><ArrowLeft size={13} className="rotate-180" /> Export frame report</Button></aside></div></div></main>;
}