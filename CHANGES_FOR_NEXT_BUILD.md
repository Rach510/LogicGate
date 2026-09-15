# RoadRead — fixes in this build

## Analysis / CV
- Pothole detection is precision-first and constrained to the perspective road surface.
- Sky, clouds, vehicles, barriers and lane-marking regions are filtered out by road geometry and local pavement checks.
- Pothole confidence is derived from local darkness, contrast, shape and texture.
- Duplicate detections are suppressed.
- Surface-crack detection is deliberately conservative to avoid false positives.
- Video analysis samples multiple frames and combines their confidence/measurement stability.
- Projects without uploaded media no longer show fake seeded confidence values.

## Plans / checkout
- Selecting a non-current plan opens a demo payment page.
- No real payment is processed and no card data is stored.
- Confirming the demo checkout activates the selected plan and returns to Settings.
- The selected plan persists in the browser for the demo session.

## Existing projects
- Existing projects are paginated at 5 projects per page.
- Previous/Next controls prevent a long project list from making the onboarding page unnecessarily tall.

## Reports
- Existing PDF report/export functionality remains enabled.
