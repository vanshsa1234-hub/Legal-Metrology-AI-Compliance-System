"""
Legal Lens - Package Localization (Phase 10: docs/PRODUCTION_READINESS_PRD.md)

Crops the photo to the physical product before OCR, cutting out
background/table/hand clutter. Two layers, in order:

1. YOLO (COCO-pretrained), only when ENABLE_YOLO_LOCALIZATION is set.
   Honest limitation: COCO's 80 classes don't include a generic
   "package"/"box"/"pouch" class - only bottle/cup/bowl are relevant
   to packaged goods, so this only fires for bottled products (oil,
   water, beverages), not the majority case of boxes/pouches/packets.
   A custom-trained "declaration panel" detector would need a labeled
   dataset that doesn't exist yet (see docs/PRODUCTION_READINESS_PRD.md
   Phase 10). Falls back gracefully (bounded timeout, same pattern as
   ocr_engines.py's PaddleOCR fallback) if the package/weights aren't
   available.
2. Classical CV fallback (always available, no extra dependency): the
   largest foreground contour against the background, via grayscale +
   Otsu threshold. Works for any package shape, not just COCO classes,
   as long as the photo has reasonable contrast against its background
   - which is exactly what evaluate_image_quality() already screens for.

Never crops if neither layer is confident - callers OCR the full image
in that case, exactly like before this phase, so this can only improve
extraction, never regress it.
"""
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Optional

import cv2
import numpy as np

YOLO_INIT_TIMEOUT_SECONDS = 30
# COCO classes plausibly relevant to a packaged commodity photo.
PACKAGE_RELEVANT_CLASSES = {"bottle", "cup", "bowl"}
YOLO_CONFIDENCE_THRESHOLD = 0.4

_yolo_model = None
_yolo_unavailable = False


def _get_yolo_model():
    global _yolo_model, _yolo_unavailable
    if _yolo_model is not None or _yolo_unavailable:
        return _yolo_model

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        def _load():
            from ultralytics import YOLO
            return YOLO("yolov8n.pt")

        _yolo_model = pool.submit(_load).result(timeout=YOLO_INIT_TIMEOUT_SECONDS)
        pool.shutdown(wait=False)
        return _yolo_model
    except FutureTimeoutError:
        pool.shutdown(wait=False)
        print(f"YOLO model setup didn't finish within {YOLO_INIT_TIMEOUT_SECONDS}s; disabling YOLO localization for this process.")
    except Exception as e:
        pool.shutdown(wait=False)
        print(f"YOLO unavailable ({e}); disabling YOLO localization for this process.")
    _yolo_unavailable = True
    return None


def _yolo_crop_box(image_path: str):
    if os.environ.get("ENABLE_YOLO_LOCALIZATION", "").lower() not in ("1", "true", "yes"):
        return None
    model = _get_yolo_model()
    if model is None:
        return None

    results = model(image_path, verbose=False)
    best_box, best_conf = None, 0.0
    for r in results:
        for box in r.boxes:
            cls_name = r.names.get(int(box.cls[0]), "")
            conf = float(box.conf[0])
            if cls_name in PACKAGE_RELEVANT_CLASSES and conf >= YOLO_CONFIDENCE_THRESHOLD and conf > best_conf:
                best_conf = conf
                best_box = [int(v) for v in box.xyxy[0].tolist()]
    return best_box


def _classical_cv_crop_box(gray: np.ndarray):
    """Largest foreground contour against the background - works for any package shape."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    img_area = gray.shape[0] * gray.shape[1]
    contour_area = cv2.contourArea(largest)
    # Too small (noise) or too large (background itself got thresholded
    # as foreground) - neither is a confident package region.
    if contour_area < 0.05 * img_area or contour_area > 0.95 * img_area:
        return None

    x, y, w, h = cv2.boundingRect(largest)
    return [x, y, x + w, y + h]


def localize_package(image_path: str) -> Optional[str]:
    """
    Returns a path to a cropped copy of image_path if a confident
    package region was found (YOLO, then classical CV fallback), or
    None if neither is confident - callers should OCR the original
    image unchanged in that case.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    box = _yolo_crop_box(image_path)
    if box is None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        box = _classical_cv_crop_box(gray)
    if box is None:
        return None

    x1, y1, x2, y2 = box
    h, w = img.shape[:2]
    # Small padding so we don't clip text right at the package edge.
    pad_x, pad_y = int(0.03 * w), int(0.03 * h)
    x1, y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
    x2, y2 = min(w, x2 + pad_x), min(h, y2 + pad_y)
    cropped = img[y1:y2, x1:x2]
    if cropped.size == 0:
        return None

    cropped_path = f"{image_path}.cropped.jpg"
    cv2.imwrite(cropped_path, cropped)
    return cropped_path
