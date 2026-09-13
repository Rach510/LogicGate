import type { User } from "@/types";

// The auth flow is intentionally local-only (see memory/SPEC.md): sign-in never persists,
// so this is the one piece of "mock data" that stays in the frontend by design. Everything
// else (projects, analytics, budgets, video overlays, issues) now comes from the backend —
// see src/api/*.ts.
export const mockUser: User = {
  id: "user-arjun",
  name: "Arjun Menon",
  email: "arjun@civicscope.in",
  organization: "CivicScope Infrastructure",
  role: "Infrastructure Lead",
  initials: "AM",
};
