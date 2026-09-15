"""Road-damage-specific YOLO inference for RoadRead.

The checkpoint is a YOLOv8s model trained on the RDD2022 road-damage taxonomy:
longitudinal crack, transverse crack, alligator/fatigue crack and pothole.
The model is downloaded lazily so the API can still boot when the checkpoint is
not yet present locally. Set ROAD_DAMAGE_MODEL_PATH to a local .pt file when
internet access is unavailable.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "road_damage"
MODEL_PATH = Path(os.getenv("ROAD_DAMAGE_MODEL_PATH", MODEL_DIR / "yolov8s_rdd2022.pt"))
MODEL_URL = os.getenv(
    "ROAD_DAMAGE_MODEL_URL",
    "https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark/resolve/main/"
    "yolo-rdd2022-benchmark/yolov8s_seed0_best.pt?download=true",
)

_MODEL = None
_MODEL_LOCK = Lock()

CLASS_NAMES = {
    "D00": "Longitudinal crack",
    "D10": "Transverse crack",
    "D20": "Alligator crack",
    "D40": "Pothole",
}
CLASS_THRESHOLDS = {"D00": 0.22, "D10": 0.22, "D20": 0.22, "D40": 0.14}
ALIASES = {
    "0": "D00", "1": "D10", "2": "D20", "3": "D40",
    "D00": "D00", "D10": "D10", "D20": "D20", "D40": "D40",
    "LONGITUDINAL CRACK": "D00", "TRANSVERSE CRACK": "D10",
    "ALLIGATOR CRACK": "D20", "ALLIGATOR/FATIGUE CRACK": "D20",
    "FATIGUE CRACK": "D20", "POTHOLE": "D40", "OTHER": None,
}


def _download_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size >= 10_000_000:
        return
    if not MODEL_URL:
        raise RuntimeError("ROAD_DAMAGE_MODEL_URL is not configured and no local checkpoint was supplied")

    import requests

    logger.info("Downloading RoadRead RDD2022 model to %s", MODEL_PATH)
    tmp = MODEL_PATH.with_suffix(".download")
    try:
        with requests.get(MODEL_URL, stream=True, timeout=(20, 300)) as response:
            response.raise_for_status()
            with open(tmp, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        if tmp.stat().st_size < 10_000_000:
            raise RuntimeError("Downloaded checkpoint is unexpectedly small")
        tmp.replace(MODEL_PATH)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _ensure_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        try:
            from ultralytics import YOLO
        except Exception as exc:
            raise RuntimeError("Ultralytics is not installed. Run pip install -r requirements.txt") from exc
        try:
            _download_model()
        except Exception as exc:
            raise RuntimeError(
                "Road-damage model is not available. Ensure this machine has internet access "
                "or set ROAD_DAMAGE_MODEL_PATH to a local yolov8s RDD2022 checkpoint."
            ) from exc
        _MODEL = YOLO(str(MODEL_PATH))
        logger.info("RoadRead RDD2022 model loaded from %s", MODEL_PATH)
        return _MODEL


def _normalise_class(raw_name: str, cls_id: int) -> str | None:
    text = str(raw_name).strip().upper().replace("_", " ")
    return ALIASES.get(text, ALIASES.get(str(cls_id)))


def _inside_road_surface(cx: int, cy: int, h: int, w: int, road_mask: np.ndarray | None) -> bool:
    if cy < int(h * 0.22):
        return False
    t = np.clip((cy / max(h - 1, 1) - 0.22) / 0.78, 0.0, 1.0)
    left = w * (0.22 - 0.22 * t)
    right = w * (0.78 + 0.22 * t)
    if not (left <= cx <= right):
        return False
    if road_mask is not None:
        if not (0 <= cy < road_mask.shape[0] and 0 <= cx < road_mask.shape[1]):
            return False
        # Check local neighborhood (within 25px) to confirm nearby road surface,
        # preventing false rejections on dark, shadowed, or water-filled pothole craters
        y_min, y_max = max(0, cy - 25), min(road_mask.shape[0], cy + 26)
        x_min, x_max = max(0, cx - 25), min(road_mask.shape[1], cx + 26)
        if np.count_nonzero(road_mask[y_min:y_max, x_min:x_max]) == 0:
            return False
    return True


def predict_damage(image: np.ndarray, road_mask: np.ndarray | None = None) -> list[dict]:
    model = _ensure_model()
    results = model.predict(
        source=image,
        imgsz=960,
        conf=0.10,
        iou=0.45,
        max_det=20,
        verbose=False,
        device="cpu",
    )
    if not results:
        return []
    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    names = getattr(result, "names", None) or getattr(model, "names", {})
    h, w = image.shape[:2]
    detections: list[dict] = []
    for box in boxes:
        cls_id = int(box.cls[0])
        raw_name = names.get(cls_id, cls_id) if isinstance(names, dict) else cls_id
        code = _normalise_class(str(raw_name), cls_id)
        if code not in CLASS_NAMES:
            continue
        confidence = float(box.conf[0])
        if confidence < CLASS_THRESHOLDS[code]:
            continue
        x1, y1, x2, y2 = [int(round(v)) for v in box.xyxy[0].tolist()]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if not _inside_road_surface(cx, cy, h, w, road_mask):
            continue
        detections.append({
            "code": code,
            "label": CLASS_NAMES[code],
            "confidence": round(confidence * 100.0, 1),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        })
    detections.sort(key=lambda item: item["confidence"], reverse=True)
    return detections[:12]
