import logging
import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from lib.db import db
from lib.seed import DEFAULT_VIDEO
from lib.cv_analysis import analyze_image
from models.video import VideoOverlayMetadata, MeasurementOverlay

router = APIRouter(prefix="/projects", tags=["video"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/{project_id}/video", response_model=VideoOverlayMetadata)
async def get_video_overlay(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    stored = await db.video_analysis.find_one({"project_id": project_id})
    if stored:
        return VideoOverlayMetadata(**stored["result"])
    return VideoOverlayMetadata(**DEFAULT_VIDEO)


@router.get("/{project_id}/image")
async def get_project_image(project_id: str):
    stored = await db.video_analysis.find_one({"project_id": project_id})
    if stored and stored.get("image_path") and os.path.exists(stored["image_path"]):
        return FileResponse(stored["image_path"])
    raise HTTPException(status_code=404, detail="No image found")


@router.post("/{project_id}/upload", response_model=VideoOverlayMetadata)
async def upload_and_analyze(project_id: str, file: UploadFile = File(...)):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    contents = await file.read()

    try:
        result = analyze_image(contents)
    except Exception as exc:
        logger.exception("OpenCV analysis failed")
        raise HTTPException(status_code=422, detail=f"Image analysis failed: {exc}")

    # Save image to disk
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    image_path = os.path.join(UPLOAD_DIR, f"{project_id}{ext}")
    with open(image_path, "wb") as f:
        f.write(contents)

    road_width = result["road_width"]
    overlay = VideoOverlayMetadata(
        duration="00:00:01",
        fps=1,
        resolution="Uploaded image",
        analyzedFrames=1,
        activeMeasurements=MeasurementOverlay(
            roadWidth=road_width,
            leftLane=round(road_width / 2, 2),
            kerbToKerb=round(road_width * 1.05, 2),
            confidence=result["confidence"],
            quality=result["quality"],
            frame=1,
        ),
        boxes=result["boxes"],
        points=result["points"],
    )

    await db.video_analysis.update_one(
        {"project_id": project_id},
        {"$set": {"project_id": project_id, "result": overlay.model_dump(), "image_path": image_path}},
        upsert=True,
    )

    return overlay