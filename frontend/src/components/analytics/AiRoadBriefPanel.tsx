import { BrainCircuit, LoaderCircle, RefreshCw, Sparkles, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAiRoadBrief } from "@/hooks/useAiRoadBrief";
import type { AnalyticsData, BudgetData, Project, VideoOverlayMetadata } from "@/types";

interface AiRoadBriefPanelProps {
  project: Project;
  analytics: AnalyticsData;
  budget: BudgetData;
  video: VideoOverlayMetadata;
  className?: string;
}

export function AiRoadBriefPanel({ project, analytics, budget, video, className = "" }: AiRoadBriefPanelProps) {
  const { latestBrief, streamedContent, generate, isGenerating, error } = useAiRoadBrief(project.id);
  const content = streamedContent || latestBrief?.content;
  const request = {
    project_id: project.id,
    project_name: project.name,
    route: project.route,
    condition: analytics.roadCondition,
    confidence: analytics.confidence,
    quality: analytics.quality,
    defects_detected: analytics.defectsDetected,
    road_width: video.activeMeasurements.roadWidth,
    left_lane: video.activeMeasurements.leftLane,
    kerb_to_kerb: video.activeMeasurements.kerbToKerb,
    budget_total: budget.total,
  };

  return <section data-testid="ai-road-brief-panel" className={`ai-brief-panel rounded-[26px] p-5 sm:p-6 ${className}`}>
    <div className="flex flex-wrap items-start justify-between gap-4"><div className="flex items-start gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#b8e986]/12 text-[#b8e986]"><BrainCircuit size={19} /></span><div><div className="flex items-center gap-2"><span className="section-kicker text-[#b8e986]">AI road brief</span><span data-testid="ai-model-label" className="rounded-full border border-white/10 px-2 py-0.5 text-[9px] text-white/35">GPT-5.4</span></div><h2 data-testid="ai-road-brief-heading" className="mt-2 text-xl font-semibold tracking-tight text-white">Decision support from this survey</h2><p className="mt-1 text-xs leading-5 text-white/40">RoadRead AI uses the current measurements, defects, condition, and budget.</p></div></div><Button data-testid="ai-generate-road-brief-button" type="button" onClick={() => generate(request)} disabled={isGenerating} className="h-10 rounded-xl bg-[#b8e986] px-4 text-xs text-[#10201b] hover:bg-[#d3f5ad]">{isGenerating ? <><LoaderCircle size={14} className="animate-spin" /> Analyzing</> : content ? <><RefreshCw size={14} /> Refresh brief</> : <><Sparkles size={14} /> Generate brief</>}</Button></div>
    {content ? <div data-testid="ai-road-brief-content" aria-live="polite" className="ai-brief-prose mt-6 whitespace-pre-wrap border-t border-white/10 pt-5 text-sm leading-7 text-white/70">{content}{isGenerating && <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-[#b8e986] align-middle" />}</div> : <div data-testid="ai-road-brief-empty-state" className="mt-6 flex items-center gap-3 rounded-2xl border border-dashed border-white/10 bg-white/[0.025] p-4 text-xs leading-5 text-white/35"><Sparkles size={15} className="shrink-0 text-[#b8e986]" /> Generate a concise assessment, priority actions, and budget note grounded in the active road survey.</div>}
    {error && <div data-testid="ai-road-brief-error" role="alert" className="mt-4 flex items-center gap-2 rounded-xl border border-[#ed6f61]/25 bg-[#ed6f61]/[0.06] p-3 text-xs text-[#ffb3a9]"><TriangleAlert size={14} /> {error.message}</div>}
    <div className="mt-4 text-[10px] leading-4 text-white/25">AI guidance can be inaccurate. Verify road safety, quantities, and procurement decisions in the field.</div>
  </section>;
}
