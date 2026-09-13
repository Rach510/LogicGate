import { apiGet } from "@/lib/api";
import type { BudgetData } from "@/types";

export const budgetsApi = {
  get: (projectId: string) => apiGet<BudgetData>(`/projects/${projectId}/budget`),
};
