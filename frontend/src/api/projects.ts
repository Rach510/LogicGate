import { apiGet, apiPost } from "@/lib/api";
import type { Project, RoadLocation } from "@/types";

export const projectsApi = {
  list: () => apiGet<Project[]>("/projects"),
  create: (name: string, fileName: string, location?: RoadLocation | null) =>
    apiPost<Project>("/projects", { name, fileName, location: location ?? undefined }),
  get: (projectId: string) => apiGet<Project>(`/projects/${projectId}`),
};
