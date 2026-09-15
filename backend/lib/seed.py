"""Demo fixtures mirroring frontend/src/data/mockData.ts.

Keeps the out-of-the-box experience identical to the old frontend-only mocks: three
seeded projects, and analytics/budget/video payloads keyed by project id. Runs once
against an empty `projects` collection so a fresh MongoDB still shows a populated demo.
"""

import logging
from datetime import datetime, timedelta, timezone

from lib.db import db

logger = logging.getLogger(__name__)

NH66_ID = "project-nh66"
AIRPORT_ID = "project-airport"
UDUPI_ID = "project-udupi"

_NOW = datetime.now(timezone.utc)

SEED_PROJECTS = [
    {
        "id": NH66_ID,
        "name": "NH-66 Road Survey",
        "route": "Kundapur · Karnataka",
        "status": "Ready",
        "condition": "Good",
        "coverage": "42.8 km covered",
        "location": {"latitude": 13.6333, "longitude": 74.6907, "address": "NH-66, Kundapur", "heading": 96, "streetViewAvailable": True, "panoramaId": "mock-nh66"},
        "created_at": _NOW - timedelta(days=1),
        "updated_at": _NOW - timedelta(days=1),
    },
    {
        "id": AIRPORT_ID,
        "name": "Airport Road Analysis",
        "route": "Mangaluru International Airport",
        "status": "Needs review",
        "condition": "Minor defects",
        "coverage": "9.6 km covered",
        "location": {"latitude": 12.9619, "longitude": 74.8901, "address": "Mangaluru Airport Road", "heading": 275, "streetViewAvailable": False, "panoramaId": None},
        "created_at": _NOW - timedelta(days=3),
        "updated_at": _NOW - timedelta(days=3),
    },
    {
        "id": UDUPI_ID,
        "name": "Udupi Municipal Roads",
        "route": "Manipal · Udupi, Karnataka",
        "status": "Ready",
        "condition": "Moderate defects",
        "coverage": "18.4 km covered",
        "location": {"latitude": 13.3409, "longitude": 74.7421, "address": "Udupi, Karnataka", "heading": 122, "streetViewAvailable": True, "panoramaId": "mock-udupi"},
        "created_at": _NOW - timedelta(minutes=12),
        "updated_at": _NOW - timedelta(minutes=12),
    },
]

DEFAULT_VIDEO = {
    "duration": "00:08:24",
    "fps": 30,
    "resolution": "4K UHD",
    "analyzedFrames": 15120,
    "activeMeasurements": {"roadWidth": 6.84, "leftLane": 3.42, "kerbToKerb": 7.02, "confidence": 94.2, "quality": 91, "frame": 12481},
    "boxes": [
        {"x": 61, "y": 54, "width": 11, "height": 10, "label": "Surface crack", "severity": "medium", "confidence": 82.0},
        {"x": 76, "y": 63, "width": 8, "height": 7, "label": "Pothole", "severity": "high", "confidence": 87.0},
    ],
    "mediaType": "video",
    "mediaUrl": None,
    "points": [
        {"x": 39, "y": 63, "label": "Kerb"},
        {"x": 58, "y": 61, "label": "Lane edge"},
        {"x": 71, "y": 59, "label": "Kerb"},
    ],
}

DEFAULT_ANALYTICS = {
    "confidence": 94.2,
    "quality": 91,
    "roadCondition": "Moderate defects",
    "defectsDetected": 37,
    "analyzedDistance": "18.4 km",
    "roadProfile": [
        {"label": "06:00", "value": 91}, {"label": "08:00", "value": 95}, {"label": "10:00", "value": 93},
        {"label": "12:00", "value": 88}, {"label": "14:00", "value": 94}, {"label": "16:00", "value": 97},
        {"label": "18:00", "value": 94},
    ],
    "conditionBreakdown": [
        {"label": "Good", "value": 64, "color": "#b8e986"},
        {"label": "Minor defects", "value": 22, "color": "#f6c76d"},
        {"label": "Moderate defects", "value": 10, "color": "#e89d5c"},
        {"label": "Severe defects", "value": 4, "color": "#ed6f61"},
    ],
    "reports": [
        {"id": "r-1", "title": "Pothole cluster near service lane", "category": "Surface damage", "created": "Today, 09:42", "note": "3 high-confidence detections within 120 m."},
        {"id": "r-2", "title": "Lane edge visibility reduced", "category": "Road markings", "created": "Yesterday, 17:18", "note": "Recommend repainting after resurfacing."},
    ],
}

DEFAULT_BUDGET = {
    "total": "₹18.4L",
    "totalValue": 1840000.0,
    "change": "+6.8% vs last estimate",
    "materials": [
        {"name": "Patching", "amount": "₹4.2L", "value": 420000, "color": "#edb06c"},
        {"name": "Resurfacing", "amount": "₹7.8L", "value": 780000, "color": "#b8e986"},
        {"name": "Preventive", "amount": "₹2.1L", "value": 210000, "color": "#91a4b6"},
        {"name": "Maintenance", "amount": "₹4.3L", "value": 430000, "color": "#8b9de0"},
    ],
    "lenders": [
        {"name": "NABARD Infrastructure", "subtitle": "Rural road improvement", "rate": "7.2% p.a.", "term": "Up to 10 years", "highlight": True},
        {"name": "HDFC Project Finance", "subtitle": "Flexible drawdown", "rate": "8.1% p.a.", "term": "Up to 7 years"},
        {"name": "SIDBI Green Corridors", "subtitle": "Lower-carbon materials", "rate": "7.6% p.a.", "term": "Up to 12 years"},
    ],
}


async def seed_if_empty() -> None:
    try:
        if await db.projects.count_documents({}) == 0:
            await db.projects.insert_many(SEED_PROJECTS)
            logger.info("seed_if_empty: inserted %d demo projects", len(SEED_PROJECTS))

        # Seed video_analysis for demo projects if missing
        if await db.video_analysis.count_documents({"project_id": UDUPI_ID}) == 0:
            await db.video_analysis.update_one(
                {"project_id": UDUPI_ID},
                {"$set": {
                    "project_id": UDUPI_ID,
                    "result": DEFAULT_VIDEO,
                    "estimatedDistanceKm": 18.4,
                    "detectionConfidence": 87.0,
                    "maxDetectionConfidence": 87.0,
                    "boundaryConfidence": 94.2,
                    "widthStability": 94.2,
                }},
                upsert=True
            )
            logger.info("seed_if_empty: seeded video_analysis for %s", UDUPI_ID)
    except Exception:  # never block boot on seeding
        logger.exception("seed_if_empty failed")
