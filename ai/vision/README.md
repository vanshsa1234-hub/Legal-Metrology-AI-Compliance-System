# ai/vision/ — Not yet implemented

This directory is reserved for a real, standalone vision module (see
docs/MetraAI_Final_Tech_Stack.pdf for the intended design). Today, a
demo-grade stand-in for this concern lives inline in
`backend/app/services/ocr_service.py`, which returns hardcoded data
for a fixed set of demo barcodes rather than running real extraction.

Roadmap: extract a real implementation into this directory and have
`OCRService` call into it, without changing the API layer that
already depends on `OCRService`. See docs/ROADMAP.md.
