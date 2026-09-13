import { apiGet, apiStream } from "@/lib/api";
import type { AiRoadBrief, AiRoadBriefRequest, AiStreamEvent } from "@/types";

export const aiApi = {
  listBriefs: (projectId: string) => apiGet<AiRoadBrief[]>(`/ai/road-briefs/${projectId}`),
  generateRoadBrief: async (
    request: AiRoadBriefRequest,
    onDelta: (content: string) => void,
  ): Promise<AiRoadBrief> => {
    let completedBrief: AiRoadBrief | undefined;
    let streamError: string | undefined;
    await apiStream("/ai/road-brief/stream", request, (rawData) => {
      const event = JSON.parse(rawData) as AiStreamEvent;
      if (event.type === "delta" && event.content) onDelta(event.content);
      if (event.type === "done" && event.brief) completedBrief = event.brief;
      if (event.type === "error") streamError = event.message ?? "AI generation failed";
    });
    if (streamError) throw new Error(streamError);
    if (!completedBrief) throw new Error("RoadRead AI returned no completed brief");
    return completedBrief;
  },
};
