# ai/preprocessing/ — Real implementation lives in backend/

Image quality scoring (blur via Laplacian variance, brightness,
contrast, glare/overexposure) and OCR preprocessing (denoising,
adaptive thresholding, upscaling) are implemented for real in
`backend/app/services/ocr_service.py` (`evaluate_image_quality()` and
`_run_ocr()`). See docs/ROADMAP.md for what's still planned beyond
this (e.g. perspective correction).
