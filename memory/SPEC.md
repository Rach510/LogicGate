# RoadRead living spec

## Product
RoadRead is a dark-first road-condition analysis demo for infrastructure teams. It turns uploaded road footage into a video-first workspace with computer-vision measurements, road condition analytics, INR budgets, map context, and issue reporting.

## Data model
- `User`: mock session user with organization and role.
- `Project`: named road survey with route, status, condition, coverage, and optional `RoadLocation`.
- `AnalyticsData`: confidence, quality, defects, road profile, condition breakdown, and reports.
- `BudgetData`: INR overall estimate, material costs, and financing options.
- `VideoOverlayMetadata`: synchronized measurement values, detection boxes, and points.
- `IssueReport`: category, description, optional attachment and location.
- `AiRoadBrief`: persisted GPT-5.4 project brief with project ID, content, model, and creation time.

## Key flows
1. Sign in or create a local demo account. The session intentionally resets on refresh.
2. Choose an existing seeded project or create a new project.
3. Upload a video/photo, optionally search for a location, then watch simulated processing.
4. Explore the dashboard video environment, deep video analysis, analytics, budgets, settings, and account drawer through floating navigation.
5. Submit a report issue with optional attachment and see processing/success states.
6. Generate a streaming AI road brief from the active project's measurements, condition, defects, and budget; the latest brief is persisted and available across Dashboard and Analytics.

## Integrations
All product data now comes from the FastAPI + MongoDB backend, reached through `frontend/src/api/*.ts`:
- `GET/POST /api/projects`, `GET /api/projects/{id}` — project list, creation, lookup.
- `GET /api/projects/{id}/analytics`, `/budget`, `/video` — per-project analytics, budget, and video overlay metadata.
- `POST /api/issues` — issue report submission.
- `POST /api/ai/road-brief/stream`, `GET /api/ai/road-briefs/{project_id}` — RoadRead AI, a real server-side GPT-5.4 integration using `EMERGENT_LLM_KEY` (only available where the private `emergentintegrations` package is installed — the Emergent.sh pod; elsewhere the endpoint returns 503 and the rest of the backend is unaffected).

Two things remain frontend-only by design, not backend TODOs:
- **Auth** is a local demo session (see `hooks/useAuth.ts`) — it intentionally resets on refresh and is never persisted server-side.
- **Google Maps/Street View** is configured through `VITE_GOOGLE_MAPS_API_KEY` on the client; without a key the UI uses a graceful map preview and reports Street View unavailable.

A fresh MongoDB is auto-seeded on backend startup (`backend/lib/seed.py`) with the same three demo projects the old frontend mocks shipped, so the out-of-the-box experience is unchanged.
