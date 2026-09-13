import { apiPost } from "@/lib/api";
import type { IssueReport } from "@/types";

export const issuesApi = {
  submit: (issue: IssueReport) => apiPost<{ id: string; status: string }>("/issues", issue),
};
