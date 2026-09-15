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

function renderBriefContent(text: string) {
  const sections = text.split("\n\n");
  return sections.map((section, idx) => {
    const lines = section.split("\n");
    const isHeader = lines.length > 1 && !lines[0].startsWith("1.") && !lines[0].startsWith("2.") && !lines[0].startsWith("3.");
    if (isHeader) {
      return (
        <div key={idx} className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold tracking-tight text-white">
            <span className="h-1.5 w-1.5 rounded-full bg-[#b8e986]" />
            {lines[0]}
          </h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-white/70">{lines.slice(1).join("\n")}</div>
        </div>
      );
    }
    return (
      <div key={idx} className="whitespace-pre-wrap text-sm leading-relaxed text-white/70">
        {section}
      </div>
    );
  });
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
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#b8e986]/12 text-[#b8e986]">
          <BrainCircuit size={19} />
        </span>
        <div>
          <div className="flex items-center gap-2">
            <span className="section-kicker text-[#b8e986]">AI road brief</span>
            <span data-testid="ai-model-label" className="rounded-full border border-[#b8e986]/25 bg-[#b8e986]/10 px-2.5 py-0.5 text-[9px] font-medium text-[#cbedab]">
              {latestBrief?.model ?? "RoadRead Neural AI"}
            </span>
          </div>
          <h2 data-testid="ai-road-brief-heading" className="mt-2 text-xl font-semibold tracking-tight text-white">Decision support from this survey</h2>
          <p className="mt-1 text-xs leading-5 text-white/40">Grounded in live telemetry: {video.activeMeasurements.roadWidth}m width, {analytics.defectsDetected} defect(s), {analytics.roadCondition}.</p>
        </div>
      </div>
      <Button data-testid="ai-generate-road-brief-button" type="button" onClick={() => generate(request)} disabled={isGenerating} className="h-10 rounded-xl bg-[#b8e986] px-4 text-xs font-medium text-[#10201b] shadow-lg shadow-[#b8e986]/10 hover:bg-[#d3f5ad]">
        {isGenerating ? <><LoaderCircle size={14} className="animate-spin" /> Synthesizing telemetry...</> : content ? <><RefreshCw size={14} /> Re-analyze with AI</> : <><Sparkles size={14} /> Generate AI brief</>}
      </Button>
    </div>
    {content ? (
      <div data-testid="ai-road-brief-content" aria-live="polite" className="mt-6 space-y-4 border-t border-white/10 pt-5">
        {renderBriefContent(content)}
        {isGenerating && (
          <div className="flex items-center gap-2 pt-1 text-xs text-[#b8e986]">
            <span className="inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-[#b8e986]" />
            <span className="text-[11px] text-white/40">Streaming neural highway analysis...</span>
          </div>
        )}
      </div>
    ) : (
      <div data-testid="ai-road-brief-empty-state" className="mt-6 flex items-center gap-3 rounded-2xl border border-dashed border-white/10 bg-white/[0.025] p-4 text-xs leading-5 text-white/35">
        <Sparkles size={15} className="shrink-0 text-[#b8e986]" /> Click Generate AI brief for an automated assessment, priority interventions, and procurement advice based on this road's profile.
      </div>
    )}
    {error && <div data-testid="ai-road-brief-error" role="alert" className="mt-4 flex items-center gap-2 rounded-xl border border-[#ed6f61]/25 bg-[#ed6f61]/[0.06] p-3 text-xs text-[#ffb3a9]"><TriangleAlert size={14} /> {error.message}</div>}
    <div className="mt-4 text-[10px] leading-4 text-white/25">AI guidance can be inaccurate. Verify road safety, quantities, and procurement decisions in the field.</div>
  </section>;
}
