import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/analytics";
import { budgetsApi } from "@/api/budgets";
import { projectsApi } from "@/api/projects";
import { videoApi } from "@/api/video";
import type { AnalyticsData, BudgetData, Project, RoadLocation, VideoOverlayMetadata } from "@/types";

const emptyAnalytics = (project: Project): AnalyticsData => ({
  confidence: 0,
  quality: 0,
  roadCondition: project.condition,
  defectsDetected: 0,
  analyzedDistance: "0 km",
  roadProfile: [],
  conditionBreakdown: [{ label: "Awaiting analysis", value: 100, color: "#60716a" }],
  reports: [],
});

const emptyBudget = (): BudgetData => ({
  total: "Awaiting analysis",
  totalValue: 0,
  change: "No survey data yet",
  materials: [],
  lenders: [],
});

const emptyVideo: VideoOverlayMetadata = {
  duration: "",
  fps: 0,
  resolution: "No survey media uploaded",
  analyzedFrames: 0,
  activeMeasurements: { roadWidth: 0, leftLane: 0, kerbToKerb: 0, confidence: 0, quality: 0, frame: 0 },
  boxes: [],
  points: [],
  mediaType: "image",
  mediaUrl: null,
  roadBoundary: null,
};

export function useRoadRead() {
  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: projectsApi.list });
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [video, setVideo] = useState<VideoOverlayMetadata | null>(null);
  const [bgImage, setBgImage] = useState<string | undefined>(undefined);

  const loadWorkspace = useCallback(async (project: Project) => {
    // Set the project first so an individual endpoint failure never prevents
    // the user from opening an existing project.
    setActiveProject(project);
    const [analyticsResult, budgetResult, videoResult] = await Promise.allSettled([
      analyticsApi.get(project.id),
      budgetsApi.get(project.id),
      videoApi.getOverlayMetadata(project.id),
    ]);

    setAnalytics(analyticsResult.status === "fulfilled" ? analyticsResult.value : emptyAnalytics(project));
    setBudget(budgetResult.status === "fulfilled" ? budgetResult.value : emptyBudget());
    setVideo(videoResult.status === "fulfilled" ? videoResult.value : emptyVideo);

    try {
      const imageUrl = `/api/projects/${project.id}/image`;
      const res = await fetch(imageUrl);
      setBgImage(res.ok ? imageUrl : undefined);
    } catch {
      setBgImage(undefined);
    }
  }, []);

  const createProject = useCallback(async (
    name: string,
    fileName: string,
    location?: Project["location"] | null,
    file?: File | null,
  ) => {
    const project = await projectsApi.create(name, fileName, location as RoadLocation | null | undefined);
    await projectsQuery.refetch();
    await loadWorkspace(project);
    if (file) {
      const result = await videoApi.uploadImage(project.id, file);
      setVideo(result);
      setBgImage(`/api/projects/${project.id}/image`);
      const [nextAnalytics, nextBudget] = await Promise.all([
        analyticsApi.get(project.id),
        budgetsApi.get(project.id),
      ]);
      setAnalytics(nextAnalytics);
      setBudget(nextBudget);
      // Refresh the project so updated condition/coverage/status are reflected.
      const updatedProject = await projectsApi.get(project.id).catch(() => project);
      setActiveProject(updatedProject);
    }
    return project;
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
