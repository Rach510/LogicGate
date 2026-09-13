import { apiGet } from "@/lib/api";
import type { AnalyticsData } from "@/types";

export const analyticsApi = {
  get: (projectId: string) => apiGet<AnalyticsData>(`/projects/${projectId}/analytics`),
};
