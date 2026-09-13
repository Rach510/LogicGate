import { apiGet } from "@/lib/api";
import type { VideoOverlayMetadata } from "@/types";

export const videoApi = {
  getOverlayMetadata: (projectId: string) =>
    apiGet<VideoOverlayMetadata>(`/projects/${projectId}/video`),

  uploadImage: async (projectId: string, file: File): Promise<VideoOverlayMetadata> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`/api/projects/${projectId}/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  },
};