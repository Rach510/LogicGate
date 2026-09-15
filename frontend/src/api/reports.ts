const BASE = "/api";

export const reportsApi = {
  download: async (projectId: string, scope: "frame" | "full") => {
    const response = await fetch(`${BASE}/projects/${projectId}/report/pdf?scope=${scope}`);
    if (!response.ok) {
      const body = await response.text().catch(() => "");
      throw new Error(body || "Could not export report");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `roadread-${scope}-report.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  },
};
