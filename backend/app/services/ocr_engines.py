"""
Legal Lens - OCR Engine Abstraction (Phase 9: docs/PRODUCTION_READINESS_PRD.md)

OCR_ENGINE unset/"tesseract" (default): pytesseract, zero extra setup,
matches every behavior this codebase has been tested against so far.

OCR_ENGINE=paddleocr: uses PaddleOCR (the engine named in the original
tech-stack doc) instead. Requires `pip install paddleocr paddlepaddle`
and a one-time model weight download on first use (hosted on Baidu's
infra, not verified reachable from every network - if the weights
can't download, construction raises and the caller should fall back
to Tesseract; see get_ocr_engine()).

Both engines return the same contract: (full_text: str, words: list of
{text, confidence, bbox}) - callers in ocr_service.py don't know or
care which engine produced it.
"""
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Tuple

# How long PaddleOCR's first-use model download/construction gets
# before we give up and fall back to Tesseract. Verified necessary:
# an unreachable weight host doesn't fail fast, it hangs - so a
# regular try/except around a slow network call isn't enough on its
# own to keep a request thread from blocking indefinitely.
PADDLEOCR_INIT_TIMEOUT_SECONDS = 30


class OCREngine(ABC):
    @abstractmethod
    def recognize(self, preprocessed_image) -> Tuple[str, List[Dict[str, Any]]]:
        """
        preprocessed_image: a single-channel (grayscale/thresholded)
        numpy array, already denoised/upscaled by the caller.
        Returns (full_text, words), words = [{text, confidence, bbox: [x1,y1,x2,y2]}, ...]
        """


class TesseractEngine(OCREngine):
    def recognize(self, preprocessed_image):
        import pytesseract

        full_text = pytesseract.image_to_string(preprocessed_image)

        data = pytesseract.image_to_data(preprocessed_image, output_type=pytesseract.Output.DICT)
        words = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            try:
                conf = float(data["conf"][i])
            except (ValueError, TypeError):
                conf = -1.0
            if text and conf >= 0:
                words.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": [data["left"][i], data["top"][i], data["left"][i] + data["width"][i], data["top"][i] + data["height"][i]],
                })
        return full_text, words


class PaddleOCREngine(OCREngine):
    def __init__(self):
        # Constructed lazily, once, on first use - not at import time -
        # so that the (optional) paddleocr dependency and its model
        # weight download only happen when OCR_ENGINE=paddleocr is
        # actually set. use_doc_orientation_classify/use_doc_unwarping
        # are disabled since our images are already-cropped label
        # photos, not scanned documents.
        from paddleocr import PaddleOCR
        self._reader = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang="en",
        )

    def recognize(self, preprocessed_image):
        import cv2
        # PaddleOCR expects a 3-channel image, not the single-channel
        # thresholded image Tesseract prefers.
        bgr = cv2.cvtColor(preprocessed_image, cv2.COLOR_GRAY2BGR)

        words: List[Dict[str, Any]] = []
        lines: List[str] = []
        for page in self._reader.predict(bgr):
            res = page if isinstance(page, dict) else page.get("res", page)
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            boxes = res.get("rec_boxes", res.get("rec_polys", []))
            for text, score, box in zip(texts, scores, boxes):
                xs = [p[0] for p in box] if hasattr(box[0], "__len__") else [box[0], box[2]]
                ys = [p[1] for p in box] if hasattr(box[0], "__len__") else [box[1], box[3]]
                words.append({
                    "text": text,
                    "confidence": float(score) * 100,  # match Tesseract's 0-100 scale
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                })
                lines.append(text)

        return "\n".join(lines), words


_engine_instance = None


def get_ocr_engine() -> OCREngine:
    """Returns the configured OCR engine, falling back to Tesseract if
    OCR_ENGINE=paddleocr was requested but the package/weights aren't
    available (never hard-fails the whole request over an engine swap)."""
    global _engine_instance
    if _engine_instance is not None:
        return _engine_instance

    requested = os.environ.get("OCR_ENGINE", "tesseract").lower()
    if requested == "paddleocr":
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            _engine_instance = pool.submit(PaddleOCREngine).result(timeout=PADDLEOCR_INIT_TIMEOUT_SECONDS)
            pool.shutdown(wait=False)
            return _engine_instance
        except FutureTimeoutError:
            # Don't wait=True here - the model hoster connectivity check
            # that timed out can itself take 30-60s+ to give up on its
            # own; we've already decided to fall back, so don't block
            # this thread on that abandoned background attempt too.
            pool.shutdown(wait=False)
            print(
                f"OCR_ENGINE=paddleocr requested but model setup didn't finish within "
                f"{PADDLEOCR_INIT_TIMEOUT_SECONDS}s (likely an unreachable weight host); "
                f"falling back to Tesseract."
            )
        except Exception as e:
            pool.shutdown(wait=False)
            print(f"OCR_ENGINE=paddleocr requested but unavailable ({e}); falling back to Tesseract.")

    _engine_instance = TesseractEngine()
    return _engine_instance
