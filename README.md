# ⚖️ Legal Metrology AI Compliance System

An AI-powered compliance inspection platform that automatically analyzes packaged commodity labels and product images to detect potential violations under India's **Legal Metrology (Packaged Commodities) Rules, 2011**.

The system combines **Computer Vision, OCR, NLP, and a rule-based compliance engine** to extract mandatory declarations, validate them against applicable regulations, identify potential violations, highlight evidence, and generate digital inspection reports.

---

## 🚀 Features

- 📷 **AI Product Scanning** — Analyze images of packaged commodities.
- 🔍 **OCR & Text Extraction** — Extract text and mandatory declarations from labels.
- 🧠 **AI Information Extraction** — Identify product, manufacturer, MRP, quantity, dates, consumer-care details, etc.
- ⚖️ **Rule-Based Compliance Engine** — Validate declarations against applicable Legal Metrology requirements.
- 🚨 **Violation Detection** — Identify missing, incomplete, or potentially non-compliant declarations.
- 🔠 **Font & Readability Analysis** — Analyze text visibility, readability, and applicable size requirements.
- 🖼️ **Evidence Highlighting** — Highlight relevant regions of product images.
- 📊 **Compliance Dashboard** — Monitor inspections, violations, and product status.
- 📄 **Automated Reports** — Generate digital compliance and inspection reports.
- 🗂️ **Inspection Repository** — Store and retrieve scanned products and inspection history.
- 🔐 **Role-Based Access** — Secure access for officers, reviewers, and administrators.
- 🛒 **E-Commerce Listing Analysis** — Support analysis of online product information and images.

---

## 🧠 How It Works

```text
                 PRODUCT IMAGE
                       │
                       ▼
              Image Preprocessing
                       │
                       ▼
             Text / Label Detection
                       │
                       ▼
                      OCR
                       │
                       ▼
             Information Extraction
                       │
                       ▼
              Structured Product Data
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Legal Rule Database    Legal RAG
             │                   │
             └─────────┬─────────┘
                       ▼
              Compliance Engine
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       COMPLIANT    VIOLATION     REVIEW
          │            │            │
          └────────────┼────────────┘
                       ▼
              Evidence & Report
                       │
                       ▼
              Officer Dashboard