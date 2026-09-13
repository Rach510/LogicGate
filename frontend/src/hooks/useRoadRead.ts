import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/analytics";
import { budgetsApi } from "@/api/budgets";
import { projectsApi } from "@/api/projects";
import { videoApi } from "@/api/video";
import type { AnalyticsData, BudgetData, Project, RoadLocation, VideoOverlayMetadata } from "@/types";

export function useRoadRead() {
  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: projectsApi.list });
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [video, setVideo] = useState<VideoOverlayMetadata | null>(null);
  const [bgImage, setBgImage] = useState<string | undefined>(undefined);

  const loadWorkspace = useCallback(async (project: Project) => {
  const [nextAnalytics, nextBudget, nextVideo] = await Promise.all([
    analyticsApi.get(project.id),
    budgetsApi.get(project.id),
    videoApi.getOverlayMetadata(project.id),
  ]);
  setActiveProject(project);
  setAnalytics(nextAnalytics);
  setBudget(nextBudget);
  setVideo(nextVideo);
  // Try to load stored image
  try {
    const imageUrl = `/api/projects/${project.id}/image`;
    const res = await fetch(imageUrl);
    if (res.ok) setBgImage(imageUrl);
    else setBgImage(undefined);
  } catch {
    setBgImage(undefined);
  }
}, []);

  const createProject = useCallback(async (name: string, fileName: string, location?: Project["location"] | null, file?: File | null) => {
  const project = await projectsApi.create(name, fileName, location as RoadLocation | null | undefined);
  await projectsQuery.refetch();
  await loadWorkspace(project);
  if (file) {
  try {
    const result = await videoApi.uploadImage(project.id, file);
    setVideo(result);
    setBgImage(`/api/projects/${project.id}/image`);
    // Refresh analytics and budget now that OpenCV data exists
    const [nextAnalytics, nextBudget] = await Promise.all([
      analyticsApi.get(project.id),
      budgetsApi.get(project.id),
    ]);
    setAnalytics(nextAnalytics);
    setBudget(nextBudget);
  } catch {
    console.error("Auto-analysis failed");
  }
}
}, [loadWorkspace, projectsQuery]);

  return {
  projects: projectsQuery.data ?? [],
  projectsLoading: projectsQuery.isLoading,
  activeProject,
  analytics,
  budget,
  video,
  bgImage,
  loadWorkspace,
  createProject,
};
}
