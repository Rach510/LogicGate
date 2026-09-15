import logging
import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from lib.cv_analysis import analyze_image, analyze_video
from lib.db import db
from models.video import MeasurementOverlay, VideoOverlayMetadata, RoadBoundary

router = APIRouter(prefix="/projects", tags=["video"])
logger = logging.getLogger(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
IMAGE_EXTENSIONS={".jpg",".jpeg",".png",".webp",".bmp"}
VIDEO_EXTENSIONS={".mp4",".mov",".avi",".mkv",".webm"}


def _empty_video() -> VideoOverlayMetadata:
    return VideoOverlayMetadata(duration="",fps=0,resolution="No survey media uploaded",analyzedFrames=0,
        activeMeasurements=MeasurementOverlay(roadWidth=0,leftLane=0,kerbToKerb=0,confidence=0,quality=0,frame=0),
        boxes=[],points=[],mediaType="image",mediaUrl=None,roadBoundary=None)

@router.get("/{project_id}/video", response_model=VideoOverlayMetadata)
async def get_video_overlay(project_id: str):
    project=await db.projects.find_one({"id":project_id})
    if project is None: raise HTTPException(status_code=404,detail="Project not found")
    stored=await db.video_analysis.find_one({"project_id":project_id})
    if not stored: return _empty_video()
    result=dict(stored.get("result",{}))
    result.setdefault("mediaUrl",f"/api/projects/{project_id}/image")
    result.setdefault("mediaType","video")
    if result.get("roadBoundary") is not None:
        result["roadBoundary"]=RoadBoundary(**result["roadBoundary"])
    return VideoOverlayMetadata(**result)

@router.get("/{project_id}/image")
async def get_project_media(project_id: str):
    stored=await db.video_analysis.find_one({"project_id":project_id})
    if stored and stored.get("image_path") and os.path.exists(stored["image_path"]):
        return FileResponse(stored["image_path"])
    raise HTTPException(status_code=404,detail="No survey media found")

@router.post("/{project_id}/upload", response_model=VideoOverlayMetadata)
async def upload_and_analyze(project_id: str,file: UploadFile=File(...),reference_width_m: float|None=Form(default=None)):
    project=await db.projects.find_one({"id":project_id})
    if project is None: raise HTTPException(status_code=404,detail="Project not found")
    contents=await file.read(); suffix=Path(file.filename or "survey.jpg").suffix.lower()
    if suffix not in IMAGE_EXTENSIONS|VIDEO_EXTENSIONS:
        raise HTTPException(status_code=415,detail="Upload a JPG, PNG, WEBP, MP4, MOV, AVI, MKV or WEBM file")
    try:
        if suffix in VIDEO_EXTENSIONS:
            result=analyze_video(contents,suffix=suffix,reference_width_m=reference_width_m); media_type="video"; duration=result["duration"]; fps=result["fps"]; analyzed_frames=result["analyzed_frames"]; resolution="Survey video"
        else:
            result=analyze_image(contents,reference_width_m=reference_width_m); media_type="image"; duration=""; fps=0; analyzed_frames=1; resolution="Uploaded image"
    except Exception as exc:
        logger.exception("Survey analysis failed")
        raise HTTPException(status_code=422,detail=f"Survey media analysis failed: {exc}")

    media_path=os.path.join(UPLOAD_DIR,f"{project_id}{suffix}")
    with open(media_path,"wb") as handle: handle.write(contents)
    road_width=float(result["road_width"])
    overlay=VideoOverlayMetadata(
        duration=duration,fps=fps,resolution=resolution,analyzedFrames=analyzed_frames,
        activeMeasurements=MeasurementOverlay(roadWidth=road_width,leftLane=round(road_width/2,2) if road_width else 0,kerbToKerb=round(road_width*1.05,2) if road_width else 0,confidence=result["confidence"],quality=result["quality"],frame=1),
        boxes=result["boxes"],points=result["points"],mediaType=media_type,mediaUrl=f"/api/projects/{project_id}/image",
        roadBoundary=RoadBoundary(**result["road_boundary"]) if result.get("road_boundary") else None,
    )
    await db.video_analysis.update_one({"project_id":project_id},{"$set":{
        "project_id":project_id,"result":overlay.model_dump(),"image_path":media_path,"filename":file.filename,
        "estimatedDistanceKm":float(result.get("estimated_distance_km",0.0)),
        "detectionConfidence":float(result.get("detection_confidence",0.0)),
        "maxDetectionConfidence":float(result.get("max_detection_confidence",0.0)),
        "boundaryConfidence":float(result.get("boundary_confidence",0.0)),
        "widthStability":float(result.get("width_stability",result.get("boundary_confidence",0.0))),
    }},upsert=True)
    quality=float(result["quality"]); condition="Good" if quality>=85 else "Minor defects" if quality>=65 else "Moderate defects" if quality>=45 else "Severe defects"
    distance=float(result.get("estimated_distance_km",0.0)); coverage=f"{distance:.2f} km covered" if distance>0 else project.get("coverage","0 km covered")
    await db.projects.update_one({"id":project_id},{"$set":{"status":"Ready","condition":condition,"coverage":coverage,"updated_at":__import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    return overlay
