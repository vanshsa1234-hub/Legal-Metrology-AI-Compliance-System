# ai/ocr/ — Real implementation lives in backend/, PaddleOCR upgrade pending

A real OCR pipeline now exists: `backend/app/services/ocr_service.py`
runs OpenCV preprocessing + Tesseract text recognition + regex-based
structured field extraction. It is genuinely functional, not a demo
catalog.

What's still pending, matching the original tech stack doc
(docs/MetraAI_Final_Tech_Stack.pdf): swapping Tesseract for PaddleOCR
for better multilingual/stylised-font accuracy. That only requires
changing `OCRService._run_ocr()` - the rest of the pipeline (regex
parsers, confidence scoring, callers) is engine-agnostic. See
docs/ROADMAP.md.
