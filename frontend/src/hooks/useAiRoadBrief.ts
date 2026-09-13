import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { aiApi } from "@/api/ai";
import type { AiRoadBriefRequest } from "@/types";

export function useAiRoadBrief(projectId: string) {
  const queryClient = useQueryClient();
  const [streamedContent, setStreamedContent] = useState("");
  const briefsQuery = useQuery({
    queryKey: ["ai-road-briefs", projectId],
    queryFn: () => aiApi.listBriefs(projectId),
    retry: false,
  });
  const generate = useMutation({
    mutationFn: (request: AiRoadBriefRequest) => {
      setStreamedContent("");
      return aiApi.generateRoadBrief(request, (delta) => setStreamedContent((current) => current + delta));
    },
    onSuccess: (brief) => {
      setStreamedContent(brief.content);
      void queryClient.invalidateQueries({ queryKey: ["ai-road-briefs", projectId] });
    },
  });
  return {
    latestBrief: briefsQuery.data?.[0],
    streamedContent,
    generate: generate.mutate,
    isGenerating: generate.isPending,
    error: generate.error,
  };
}
