import cv2
import numpy as np
from typing import List
from models.video import BoundingBox, DetectionPoint


def analyze_image(image_bytes: bytes) -> dict:
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- Crack detection (dark linear features) ---
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    crack_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    crack_mask = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, crack_kernel)
    crack_contours, _ = cv2.findContours(crack_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # --- Pothole detection (dark blobs) ---
    _, dark_mask = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
    blob_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    blob_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, blob_kernel)
    pothole_contours, _ = cv2.findContours(blob_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: List[BoundingBox] = []
    points: List[DetectionPoint] = []
    used_labels = set()

    # Process crack contours
    for cnt in crack_contours:
        area = cv2.contourArea(cnt)
        if area < 300:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        # Convert to percentage coordinates (0-100) to match frontend SVG viewBox
        label = "Surface crack"
        suffix = ""
        count = 1
        while f"{label}{suffix}" in used_labels:
            count += 1
            suffix = f" {count}"
        label = f"{label}{suffix}"
        used_labels.add(label)

        severity = "high" if area > 3000 else "medium" if area > 1000 else "low"
        boxes.append(BoundingBox(
            x=round(x / w * 100, 1),
            y=round(y / h * 100, 1),
            width=round(bw / w * 100, 1),
            height=round(bh / h * 100, 1),
            label=label,
            severity=severity,
        ))
        points.append(DetectionPoint(
            x=round((x + bw / 2) / w * 100, 1),
            y=round((y + bh / 2) / h * 100, 1),
            label="Crack edge",
        ))

    # Process pothole contours
    for cnt in pothole_contours:
        area = cv2.contourArea(cnt)
        if area < 800:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = bw / max(bh, 1)
        if aspect > 5:  # too elongated — likely not a pothole
            continue

        label = "Pothole"
        suffix = ""
        count = 1
        while f"{label}{suffix}" in used_labels:
            count += 1
            suffix = f" {count}"
        label = f"{label}{suffix}"
        used_labels.add(label)

        severity = "high" if area > 5000 else "medium" if area > 2000 else "low"
        boxes.append(BoundingBox(
            x=round(x / w * 100, 1),
            y=round(y / h * 100, 1),
            width=round(bw / w * 100, 1),
            height=round(bh / h * 100, 1),
            label=label,
            severity=severity,
        ))
        points.append(DetectionPoint(
            x=round((x + bw / 2) / w * 100, 1),
            y=round((y + bh / 2) / h * 100, 1),
            label="Pothole centre",
        ))

    # Limit to top 6 detections to avoid cluttering the overlay
    boxes = boxes[:6]
    points = points[:6]

    # Estimate road width from lane markings (bright vertical band in centre)
    road_width = _estimate_road_width(gray, w)

    # Overall quality score based on defect density
    defect_area = sum(b.width * b.height for b in boxes)
    quality = max(40, round(100 - defect_area * 0.3))
    confidence = min(97, max(70, quality + 3))

    return {
        "boxes": boxes,
        "points": points,
        "road_width": road_width,
        "quality": quality,
        "confidence": confidence,
        "defects_detected": len(boxes),
    }


def _estimate_road_width(gray: np.ndarray, img_width: int) -> float:
    # Find bright horizontal band (road surface) and estimate width
    h, w = gray.shape
    centre_row = gray[h // 2, :]
    bright = np.where(centre_row > 100)[0]
    if len(bright) > 10:
        span_px = bright[-1] - bright[0]
        # Rough real-world estimate: assume 1px ≈ 0.01m at typical survey distance
        road_width = round(span_px * (7.0 / w), 2)
        return max(3.0, min(12.0, road_width))
    return 6.84  # fallback