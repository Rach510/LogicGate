export type AppView = "dashboard" | "video" | "analytics" | "budgets" | "settings";

export interface User {
  id: string;
  name: string;
  email: string;
  organization: string;
  role: string;
  initials: string;
}

export interface RoadLocation {
  latitude: number;
  longitude: number;
  address?: string;
  heading?: number;
  streetViewAvailable: boolean;
  panoramaId?: string;
}

export interface Project {
  id: string;
  name: string;
  route: string;
  updated: string;
  status: "Ready" | "Processing" | "Needs review";
  condition: "Good" | "Minor defects" | "Moderate defects" | "Severe defects";
  coverage: string;
  location: RoadLocation;
}

export interface MeasurementOverlay {
  roadWidth: number;
  leftLane: number;
  kerbToKerb: number;
  confidence: number;
  quality: number;
  frame: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  severity: "low" | "medium" | "high";
}

export interface DetectionPoint {
  x: number;
  y: number;
  label: string;
}

export interface VideoOverlayMetadata {
  duration: string;
  fps: number;
  resolution: string;
  analyzedFrames: number;
  activeMeasurements: MeasurementOverlay;
  boxes: BoundingBox[];
  points: DetectionPoint[];
}

export interface AnalyticsData {
  confidence: number;
  quality: number;
  roadCondition: Project["condition"];
  defectsDetected: number;
  analyzedDistance: string;
  roadProfile: Array<{ label: string; value: number }>;
  conditionBreakdown: Array<{ label: string; value: number; color: string }>;
  reports: Report[];
}

export interface MaterialCost {
  name: string;
  amount: string;
  value: number;
  color: string;
}

export interface LenderOption {
  name: string;
  subtitle: string;
  rate: string;
  term: string;
  highlight?: boolean;
}

export interface BudgetData {
  total: string;
  totalValue: number;
  change: string;
  materials: MaterialCost[];
  lenders: LenderOption[];
}

export interface Report {
  id: string;
  title: string;
  category: string;
  created: string;
  note: string;
}

export interface IssueReport {
  description: string;
  category: string;
  location?: RoadLocation;
  attachmentName?: string;
}

export type ProcessingStep = {
  label: string;
  status: "pending" | "active" | "complete";
};

export interface AiRoadBriefRequest {
  project_id: string;
  project_name: string;
  route: string;
  condition: string;
  confidence: number;
  quality: number;
  defects_detected: number;
  road_width: number;
  left_lane: number;
  kerb_to_kerb: number;
  budget_total: string;
}

export interface AiRoadBrief {
  id: string;
  project_id: string;
  model: string;
  content: string;
  created_at: string;
}

export interface AiStreamEvent {
  type: "delta" | "done" | "error";
  content?: string;
  brief?: AiRoadBrief;
  message?: string;
}

