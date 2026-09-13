import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from lib.dates import relative_label
from lib.db import db
from models.project import Project, ProjectCreate, ProjectDocument, RoadLocation

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)


def _doc_to_project(document: dict) -> Project:
    document = dict(document)
    document.pop("_id", None)
    updated_at = document.get("updated_at") or document.get("created_at")
    if isinstance(updated_at, datetime):
        label = relative_label(updated_at)
    else:
        label = "Updated just now"
    doc = ProjectDocument(**document)
    return doc.to_project(updated_label=label)


@router.get("", response_model=list[Project])
async def list_projects():
    documents = await db.projects.find().sort("updated_at", -1).to_list(200)
    return [_doc_to_project(document) for document in documents]


@router.post("", response_model=Project)
async def create_project(payload: ProjectCreate):
    location = payload.location or RoadLocation(
        latitude=13.3409, longitude=74.7421, address="Udupi, Karnataka",
        heading=122, streetViewAvailable=False, panoramaId=None,
    )
    document = ProjectDocument(
        name=payload.name,
        route=payload.fileName,
        status="Processing",
        condition="Good",
        coverage="0 km covered",
        location=location,
    )
    await db.projects.insert_one(document.model_dump())
    return document.to_project(updated_label="Updated just now")


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    document = await db.projects.find_one({"id": project_id})
    if document is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _doc_to_project(document)
