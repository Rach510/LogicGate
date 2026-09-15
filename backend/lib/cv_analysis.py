"""RoadRead road geometry + road-damage analysis.

YOLO handles road-damage recognition. OpenCV handles capture quality and
perspective-aware road-boundary geometry. Metric width is a calibrated estimate
when a reference width is supplied; otherwise a clearly lower-confidence scale
prior is used rather than pretending pixels are metres.
"""
from __future__ import annotations

import os
import tempfile
from statistics import median
from typing import List

import cv2
import numpy as np

from lib.road_damage_ai import predict_damage
from models.video import BoundingBox, DetectionPoint

DEFAULT_ROAD_WIDTH_M = float(os.getenv("ROADREAD_DEFAULT_ROAD_WIDTH_M", "7.0"))
SURVEY_SPEED_KMH = float(os.getenv("ROADREAD_SURVEY_SPEED_KMH", "25"))


def analyze_image(image_bytes: bytes, reference_width_m: float | None = None) -> dict:
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    result = _analyze_frame(img, reference_width_m=reference_width_m)
    result["estimated_distance_km"] = 0.05
    return result


def analyze_video(video_bytes: bytes, suffix: str = ".mp4", reference_width_m: float | None = None) -> dict:
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        with open(temp_path, "wb") as handle:
            handle.write(video_bytes)
        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError("Could not decode the uploaded video")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_seconds = frame_count / fps if fps > 0 else 0.0
        sample_count = min(12, max(4, int(round(duration_seconds / 2)))) if duration_seconds > 0 else 8
        indices = np.linspace(0, max(frame_count - 1, 0), sample_count, dtype=int)
        analyses: list[dict] = []
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            ok, frame = capture.read()
            if ok and frame is not None:
                analyses.append(_analyze_frame(frame, reference_width_m=reference_width_m))
        capture.release()
        if not analyses:
            raise ValueError("No readable frames were found in the uploaded video")

        representative = max(analyses, key=lambda item: (item["confidence"], len(item["boxes"])))
        widths = [item["road_width"] for item in analyses if item["road_width"] > 0]
        confidence = float(np.mean([item["confidence"] for item in analyses]))
        quality = float(np.mean([item["quality"] for item in analyses]))
        if len(widths) >= 2:
            spread = float(np.std(widths))
            confidence = float(np.clip(confidence + max(0.0, min(5.0, 5.0 - spread * 5.0)), 20, 98))

        # Conservative route-distance estimate from video duration. This is a
        # configurable planning value, not GPS-derived ground truth.
        estimated_distance_km = round(duration_seconds / 3600.0 * SURVEY_SPEED_KMH, 3)
        return {
            "boxes": representative["boxes"],
            "points": representative["points"],
            "road_width": round(float(median(widths)), 2) if widths else representative["road_width"],
            "quality": round(quality, 1),
            "confidence": round(confidence, 1),
            "defects_detected": len(representative["boxes"]),
            "detection_confidence": representative.get("detection_confidence", 0.0),
            "max_detection_confidence": representative.get("max_detection_confidence", 0.0),
            "boundary_confidence": representative.get("boundary_confidence", 0.0),
            "road_boundary": representative.get("road_boundary"),
            "fps": max(1, round(fps)),
            "analyzed_frames": len(analyses),
            "duration": _format_duration(duration_seconds),
            "estimated_distance_km": estimated_distance_km,
        }
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _capture_quality(gray: np.ndarray) -> tuple[float, float]:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    contrast = float(np.std(gray))
    edge_density = float(np.count_nonzero(cv2.Canny(blurred, 50, 150)) / max(gray.shape[0] * gray.shape[1], 1))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    visibility = float(np.clip(25 + contrast * 0.70 + edge_density * 150 + min(sharpness / 90, 22), 0, 100))
    return visibility, edge_density


def _detect_road_boundaries(img: np.ndarray) -> tuple[np.ndarray, dict, float, list[float]]:
    """Build an image-adaptive road mask and estimate its perspective edges.

    The primary signal is a connected low-saturation surface region that touches
    the bottom-center of the frame (typical asphalt). Hough lines are used as a
    secondary cue when the surface mask is weak. This is more stable than a
    fixed trapezoid for both narrow roads and multi-lane highways.
    """
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    # Asphalt is often relatively low saturation. Keep a broad value range so
    # wet/dark roads remain eligible; exclude near-black frame artifacts and
    # blown-out sky/highlights.
    surface = ((sat < 115) & (val > 28) & (val < 248)).astype(np.uint8) * 255
    corridor = np.zeros((h, w), dtype=np.uint8)
    corridor_poly = np.array([
        [int(w * 0.03), int(h * 0.99)], [int(w * 0.34), int(h * 0.38)],
        [int(w * 0.66), int(h * 0.38)], [int(w * 0.97), int(h * 0.99)],
    ], dtype=np.int32)
    cv2.fillPoly(corridor, [corridor_poly], 255)
    surface = cv2.bitwise_and(surface, corridor)
    surface = cv2.morphologyEx(surface, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    surface = cv2.morphologyEx(surface, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    n, labels, stats, _ = cv2.connectedComponentsWithStats(surface, connectivity=8)
    component = 0
    bottom_center = labels[min(h - 3, h - 1), w // 2]
    if bottom_center > 0 and stats[bottom_center, cv2.CC_STAT_AREA] >= h * w * 0.02:
        component = int(bottom_center)
    elif n > 1:
        candidates = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            x, y, bw, bh = (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
            touches_bottom = y + bh >= int(h * 0.96)
            center_penalty = abs((x + bw / 2) - w / 2) / w
            score = area * (1.7 if touches_bottom else 1.0) * (1.0 - 0.65 * center_penalty)
            candidates.append((score, i))
        if candidates:
            component = max(candidates)[1]

    mask = (labels == component).astype(np.uint8) * 255 if component else surface
    if cv2.countNonZero(mask) < h * w * 0.015:
        mask = corridor.copy()
        surface_conf = 35.0
    else:
        surface_conf = float(np.clip(45 + cv2.countNonZero(mask) / max(h * w, 1) * 120, 45, 88))

    # Derive boundary points directly from the segmented road component.
    ys = [0.46, 0.58, 0.68, 0.78, 0.88, 0.94]
    left_pts, right_pts = [], []
    for ratio in ys:
        y = int(h * ratio)
        xs = np.where(mask[y] > 0)[0]
        if xs.size < max(20, int(w * 0.04)):
            continue
        # Ignore tiny isolated runs; use the largest continuous run.
        runs = []
        split = np.where(np.diff(xs) > 3)[0]
        starts = np.r_[0, split + 1]
        ends = np.r_[split, len(xs) - 1]
        for a, b in zip(starts, ends):
            run = xs[a:b+1]
            if run.size >= 8:
                runs.append(run)
        if not runs:
            continue
        run = max(runs, key=len)
        left_pts.append((y, float(run[0])))
        right_pts.append((y, float(run[-1])))

    def fit_line(points):
        if len(points) < 2:
            return None
        arr = np.asarray(points, dtype=float)
        slope, intercept = np.polyfit(arr[:, 0], arr[:, 1], 1)
        return float(slope), float(intercept)

    left_fit, right_fit = fit_line(left_pts), fit_line(right_pts)

    # Hough fallback for one or both sides when segmentation missed an edge.
    if left_fit is None or right_fit is None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
        edges = cv2.bitwise_and(edges, corridor)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=max(40, int(w*0.045)), minLineLength=max(40, int(w*0.07)), maxLineGap=max(20, int(w*0.02)))
        left_models, right_models = [], []
        if lines is not None:
            for x1,y1,x2,y2 in lines[:,0,:].astype(float):
                dy=y2-y1; dx=x2-x1
                if abs(dy) < h*0.08 or abs(dx) < 3: continue
                a=dx/dy; b=x1-a*y1; length=(dx*dx+dy*dy)**0.5
                xt=a*h*0.44+b; xb=a*h*0.92+b
                if a < -0.03 and 0.12*w <= xb <= 0.49*w: left_models.append((a,b,length))
                elif a > 0.03 and 0.51*w <= xb <= 0.88*w: right_models.append((a,b,length))
        def weighted(models):
            if not models: return None
            weights=np.array([m[2] for m in models]); vals=np.array([[m[0],m[1]] for m in models])
            return tuple(np.average(vals,axis=0,weights=weights))
        left_fit = left_fit or weighted(left_models)
        right_fit = right_fit or weighted(right_models)

    # Stable prior only if an edge truly cannot be observed.
    left_fit = left_fit or (-0.46, w*0.55)
    right_fit = right_fit or (0.46, w*0.45)

    def x_at(model, y): return float(model[0]*y + model[1])
    y_top=int(h*0.38); y_bottom=int(h*0.97)
    lx_top=np.clip(x_at(left_fit,y_top),0.15*w,0.49*w)
    lx_bottom=np.clip(x_at(left_fit,y_bottom),0.01*w,0.49*w)
    rx_top=np.clip(x_at(right_fit,y_top),0.51*w,0.85*w)
    rx_bottom=np.clip(x_at(right_fit,y_bottom),0.51*w,0.99*w)
    if rx_bottom <= lx_bottom + 0.25*w:
        lx_bottom, rx_bottom = 0.08*w, 0.92*w

    adaptive = np.zeros((h,w),dtype=np.uint8)
    polygon=np.array([[int(lx_top),y_top],[int(rx_top),y_top],[int(rx_bottom),y_bottom],[int(lx_bottom),y_bottom]],dtype=np.int32)
    cv2.fillPoly(adaptive,[polygon],255)
    mask=cv2.bitwise_and(mask,adaptive) if cv2.countNonZero(mask) >= h*w*0.015 else adaptive

    edge_points = len(left_pts) + len(right_pts)
    boundary_conf=float(np.clip(surface_conf + edge_points*3.5 + (8 if left_pts and right_pts else 0),35,94))
    boundary={
        "leftTopX": round(lx_top/w*100,1), "leftBottomX": round(lx_bottom/w*100,1),
        "rightTopX": round(rx_top/w*100,1), "rightBottomX": round(rx_bottom/w*100,1),
        "confidence": round(boundary_conf,1),
    }
    return mask,boundary,boundary_conf,[lx_top,lx_bottom,rx_top,rx_bottom]


def _analyze_frame(img: np.ndarray, reference_width_m: float | None = None) -> dict:
    h,w=img.shape[:2]
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    road_roi,boundary,boundary_conf,_=_detect_road_boundaries(img)
    visibility,_=_capture_quality(gray)

    detections=predict_damage(img, road_mask=road_roi)
    boxes:List[BoundingBox]=[]; points:List[DetectionPoint]=[]
    for d in detections:
        x1,y1,x2,y2=d["x1"],d["y1"],d["x2"],d["y2"]
        bw,bh=max(1,x2-x1),max(1,y2-y1)
        conf=float(d["confidence"]); area_ratio=(bw*bh)/max(w*h,1); code=d["code"]
        if code=="D40":
            severity="high" if (conf>=55 or area_ratio>=0.0035) else "medium" if (conf>=25 or area_ratio>=0.0015) else "low"
        elif code=="D20":
            severity="high" if (conf>=55 or area_ratio>=0.004) else "medium" if conf>=30 else "low"
        else:
            severity="high" if conf>=60 else "medium" if conf>=35 else "low"
        boxes.append(BoundingBox(x=round(x1/w*100,1),y=round(y1/h*100,1),width=round(bw/w*100,1),height=round(bh/h*100,1),label=d["label"],severity=severity,confidence=round(conf,1)))
        points.append(DetectionPoint(x=round((x1+x2)/2/w*100,1),y=round((y1+y2)/2/h*100,1),label=d["label"]))

    model_scores=[b.confidence for b in boxes]
    detection_confidence=float(np.mean(model_scores)) if model_scores else float(np.clip(visibility*0.55+boundary_conf*0.45,25,96))
    road_width,width_conf=_estimate_road_width(gray,boundary,reference_width_m)
    confidence=(detection_confidence*0.45 + boundary_conf*0.25 + visibility*0.20 + width_conf*0.10) if model_scores else (boundary_conf*0.40+visibility*0.30+width_conf*0.30)
    confidence=float(np.clip(confidence,20,98))
    high_count = sum(1 for b in boxes if b.severity == "high")
    med_count = sum(1 for b in boxes if b.severity == "medium")
    defect_penalty = min(50.0, high_count * 10.0 + med_count * 5.0 + len(boxes) * 2.0)
    base_quality = float(np.clip(visibility*0.55+boundary_conf*0.25+width_conf*0.20,20,98))
    quality = float(np.clip(base_quality - defect_penalty, 15, 98))
    return {
        "boxes":boxes,"points":points,"road_width":road_width,
        "quality":round(quality,1),"confidence":round(confidence,1),
        "defects_detected":len(boxes),"detection_confidence":round(detection_confidence,1),
        "max_detection_confidence":round(max(model_scores,default=0.0),1),
        "boundary_confidence":round(boundary_conf,1),"road_boundary":boundary,
    }


def _estimate_road_width(gray: np.ndarray, boundary: dict, reference_width_m: float | None) -> tuple[float,float]:
    h,w=gray.shape
    rows=[0.62,0.70,0.78,0.86,0.92]
    spans=[]
    for ratio in rows:
        t=(ratio-0.38)/(0.97-0.38)
        left=boundary["leftTopX"]+(boundary["leftBottomX"]-boundary["leftTopX"])*t
        right=boundary["rightTopX"]+(boundary["rightBottomX"]-boundary["rightTopX"])*t
        spans.append(max(0.20,right-left)/100.0)
    median_span=float(median(spans))
    stability=100.0-min(45.0,float(np.std(spans)*260.0))
    bottom_span=max(0.20,spans[-1])
    if reference_width_m and reference_width_m>0:
        width=float(np.clip(reference_width_m*(median_span/bottom_span),2.5,18.0))
        scale_conf=92.0
    else:
        # Transparent prior: 7 m at ~80% frame occupancy. Image-derived span
        # changes the result; this is intentionally lower confidence without calibration.
        width=float(np.clip(DEFAULT_ROAD_WIDTH_M*(median_span/0.80),2.5,14.0))
        scale_conf=52.0
    conf=float(np.clip(stability*0.55+scale_conf*0.35+boundary.get("confidence",0)*0.10,35,95))
    return round(width,2),round(conf,1)


def _format_duration(seconds: float) -> str:
    total=max(0,int(round(seconds))); hours,rem=divmod(total,3600); minutes,secs=divmod(rem,60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
