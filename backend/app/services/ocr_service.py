"""
Legal Lens - Modular OCR & Product Information Extraction Service
Follows Evidence-First Architecture with confidence scores and source image mapping.

STATUS (be upfront about this — it matters for demos and judging):
This service does NOT currently run real OCR/computer vision. It is a
demo-grade abstraction with a fixed, hardcoded product catalog keyed by
barcode. extract_product_data() only reads the `barcode` argument to pick
a pre-written record — it never analyzes the uploaded image content.
evaluate_image_quality() only checks pixel dimensions via PIL, not real
blur/glare/contrast detection.

The class is intentionally shaped so a real implementation (PaddleOCR +
OpenCV + YOLO + spaCy/Transformers, as described in
docs/MetraAI_Final_Tech_Stack.pdf) can be dropped in behind the same
two static methods without touching any caller. See docs/ROADMAP.md.
"""
import os
import re
from typing import Dict, Any, List
from PIL import Image

class OCRService:
    """
    Modular abstraction for Computer Vision, Image Quality, OCR, and NER.
    Currently backed by a fixed demo catalog (see module docstring).
    Designed to be swapped for PaddleOCR/OpenCV/YOLO without changing callers.
    """

    @staticmethod
    def evaluate_image_quality(image_path: str) -> Dict[str, Any]:
        """
        Evaluate image resolution, aspect ratio, and simulated clarity/contrast.
        """
        try:
            if not os.path.exists(image_path):
                return {"score": 90.0, "label": "Good", "details": "File uploaded"}
            
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check resolution
                if width < 400 or height < 400:
                    return {"score": 62.0, "label": "Low Resolution", "details": f"Dimensions: {width}x{height}px"}
                elif width < 800 or height < 800:
                    return {"score": 78.0, "label": "Needs Better Lighting", "details": f"Dimensions: {width}x{height}px"}
                else:
                    return {"score": 95.0, "label": "Good", "details": f"High resolution: {width}x{height}px"}
        except Exception as e:
            return {"score": 85.0, "label": "Good", "details": str(e)}

    @staticmethod
    def extract_product_data(images: List[Dict[str, str]], barcode: str = None) -> Dict[str, Any]:
        """
        Extract structured declarations from images and barcode.
        """
        # Catalog of demo scenarios to ensure rich, deterministic demo presentations
        demo_catalog = {
            "8901234567890": {
                "product_name": "CrunchBite Classic Potato Chips",
                "brand": "CrunchBite Foods",
                "category": "Packaged Food",
                "sub_category": "Snacks / Potato Chips",
                "manufacturer": "CrunchBite Foods India Pvt. Ltd., Plot 42, Industrial Area, Haridwar, Uttarakhand",
                "net_quantity": "100 g",
                "mrp": "₹50 (Inclusive of all taxes)",
                "batch_number": "CB24082401",
                "mfg_date": "08/2026",
                "best_before": "6 Months from packaging",
                "consumer_care": "care@crunchbite.in / 1800-200-8899",
                "ingredients": "Farm fresh potatoes, edible vegetable oil (palmolein), iodised salt, spices and condiments",
                "veg_non_veg": "Vegetarian",
                "fssai_license": "10018012000456",
                "country_of_origin": "India",
                "has_nutrition_issue": True,
                "declarations": [
                    {
                        "field_name": "Product Name",
                        "detected_value": "CrunchBite Classic Potato Chips",
                        "confidence": 98.2,
                        "confidence_level": "High",
                        "evidence_image_type": "front",
                        "bounding_box": "[120, 80, 480, 160]"
                    },
                    {
                        "field_name": "Brand",
                        "detected_value": "CrunchBite",
                        "confidence": 97.5,
                        "confidence_level": "High",
                        "evidence_image_type": "front",
                        "bounding_box": "[180, 40, 420, 85]"
                    },
                    {
                        "field_name": "Net Quantity",
                        "detected_value": "100 g",
                        "confidence": 96.0,
                        "confidence_level": "High",
                        "evidence_image_type": "front",
                        "bounding_box": "[350, 420, 490, 460]"
                    },
                    {
                        "field_name": "MRP (Maximum Retail Price)",
                        "detected_value": "₹50 (Incl. of all taxes)",
                        "confidence": 95.8,
                        "confidence_level": "High",
                        "evidence_image_type": "back",
                        "bounding_box": "[280, 110, 460, 150]"
                    },
                    {
                        "field_name": "Manufacturer Name & Address",
                        "detected_value": "CrunchBite Foods India Pvt. Ltd., Haridwar, Uttarakhand",
                        "confidence": 88.4,
                        "confidence_level": "Medium",
                        "evidence_image_type": "back",
                        "bounding_box": "[60, 200, 520, 270]"
                    },
                    {
                        "field_name": "Batch / Lot Number",
                        "detected_value": "CB24082401",
                        "confidence": 92.1,
                        "confidence_level": "High",
                        "evidence_image_type": "back",
                        "bounding_box": "[80, 120, 240, 150]"
                    },
                    {
                        "field_name": "Date of Packaging / Mfg",
                        "detected_value": "08/2026",
                        "confidence": 91.5,
                        "confidence_level": "High",
                        "evidence_image_type": "back",
                        "bounding_box": "[80, 160, 240, 190]"
                    },
                    {
                        "field_name": "Best Before Declaration",
                        "detected_value": "Best Before 6 Months from packaging",
                        "confidence": 94.0,
                        "confidence_level": "High",
                        "evidence_image_type": "back",
                        "bounding_box": "[260, 160, 500, 190]"
                    },
                    {
                        "field_name": "Veg / Non-Veg Logo",
                        "detected_value": "Green dot in green square (Vegetarian)",
                        "confidence": 96.2,
                        "confidence_level": "High",
                        "evidence_image_type": "front",
                        "bounding_box": "[50, 60, 110, 120]"
                    },
                    {
                        "field_name": "FSSAI License Number",
                        "detected_value": "Lic. No. 10018012000456",
                        "confidence": 74.0,
                        "confidence_level": "Medium",
                        "evidence_image_type": "back",
                        "bounding_box": "[80, 320, 340, 360]"
                    },
                    {
                        "field_name": "Consumer Care Helpline",
                        "detected_value": "care@crunchbite.in / 1800-200-8899",
                        "confidence": 89.0,
                        "confidence_level": "Medium",
                        "evidence_image_type": "back",
                        "bounding_box": "[80, 380, 480, 420]"
                    },
                    {
                        "field_name": "Nutritional Panel Extract",
                        "detected_value": "Energy 530 kcal, Protein 6.5g, Carbs 54g... [Trans fat/Added sugars breakdown incomplete/blurred]",
                        "confidence": 68.5,
                        "confidence_level": "Low",
                        "evidence_image_type": "back",
                        "bounding_box": "[60, 430, 510, 560]"
                    }
                ]
            },
            "8901030383812": {
                "product_name": "FreshFarm Whole Wheat Atta",
                "brand": "FreshFarm Mills",
                "category": "Packaged Food",
                "sub_category": "Staples / Flour",
                "manufacturer": "FreshFarm Agro Industries, Sector 18, Gurugram, Haryana",
                "net_quantity": "5 kg",
                "mrp": "₹245 (Inclusive of all taxes)",
                "batch_number": "FF-AT2408-09",
                "mfg_date": "07/2026",
                "best_before": "3 Months from packaging",
                "consumer_care": "support@freshfarm.co.in / 1800-111-2233",
                "ingredients": "100% Whole Wheat Grain",
                "veg_non_veg": "Vegetarian",
                "fssai_license": "10015064000789",
                "country_of_origin": "India",
                "has_nutrition_issue": False,
                "declarations": [
                    {"field_name": "Product Name", "detected_value": "FreshFarm Whole Wheat Atta", "confidence": 99.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[100, 100, 500, 180]"},
                    {"field_name": "Brand", "detected_value": "FreshFarm", "confidence": 98.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[150, 40, 450, 95]"},
                    {"field_name": "Net Quantity", "detected_value": "5 kg", "confidence": 97.5, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[350, 450, 480, 490]"},
                    {"field_name": "MRP (Maximum Retail Price)", "detected_value": "₹245 (Incl. of taxes)", "confidence": 96.0, "confidence_level": "High", "evidence_image_type": "back", "bounding_box": "[300, 100, 480, 140]"},
                    {"field_name": "Veg / Non-Veg Logo", "detected_value": "Green dot in green square (Vegetarian)", "confidence": 97.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[40, 50, 90, 100]"},
                    {"field_name": "FSSAI License Number", "detected_value": "Lic. No. 10015064000789", "confidence": 95.0, "confidence_level": "High", "evidence_image_type": "back", "bounding_box": "[80, 300, 360, 340]"},
                    {"field_name": "Nutritional Panel Extract", "detected_value": "Energy 364 kcal, Protein 12g, Carbs 72g, Added Sugars 0g, Total Fat 1.5g", "confidence": 94.0, "confidence_level": "High", "evidence_image_type": "back", "bounding_box": "[80, 360, 500, 500]"}
                ]
            },
            "8901456789012": {
                "product_name": "PureDrop Packaged Drinking Water",
                "brand": "PureDrop Beverages",
                "category": "Packaged Water",
                "sub_category": "Packaged Drinking Water",
                "manufacturer": "PureDrop Bottlers Pvt. Ltd., Industrial Estate, Dehradun",
                "net_quantity": "1 L",
                "mrp": "₹20",
                "batch_number": "PDW-9901",
                "mfg_date": "08/2026",
                "best_before": "6 Months from packaging",
                "consumer_care": "customercare@puredrop.in",
                "ingredients": "Treated Drinking Water with added minerals",
                "veg_non_veg": "Exempted (Water)",
                "fssai_license": "10012011000321",
                "country_of_origin": "India",
                "has_nutrition_issue": False,
                "declarations": [
                    {"field_name": "Product Name", "detected_value": "PureDrop Packaged Drinking Water", "confidence": 98.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[100, 80, 500, 150]"},
                    {"field_name": "Net Quantity", "detected_value": "1 L", "confidence": 97.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[200, 400, 350, 440]"},
                    {"field_name": "MRP (Maximum Retail Price)", "detected_value": "₹20", "confidence": 96.5, "confidence_level": "High", "evidence_image_type": "back", "bounding_box": "[250, 100, 400, 140]"},
                    {"field_name": "Packaging Transparency Check", "detected_value": "Colourless, transparent bottle (Estimated >85% transmission)", "confidence": 92.0, "confidence_level": "High", "evidence_image_type": "front", "bounding_box": "[0, 0, 600, 800]"},
                    {"field_name": "Veg Logo Exemption Note", "detected_value": "Exempt from Veg/Non-Veg logo per Reg 5(4) Proviso", "confidence": 95.0, "confidence_level": "High", "evidence_image_type": "back", "bounding_box": "[50, 200, 450, 250]"}
                ]
            }
        }

        # Select matching demo item or generate fallback structured record
        clean_barcode = (barcode or "").strip()
        if clean_barcode in demo_catalog:
            return demo_catalog[clean_barcode]
        
        # Default fallback for any newly scanned or entered product
        fallback_name = "Packaged Consumer Commodity"
        if clean_barcode:
            fallback_name += f" (EAN: {clean_barcode})"

        return {
            "product_name": fallback_name,
            "brand": "Generic Consumer Goods",
            "category": "Packaged Food",
            "sub_category": "Packaged Retail Goods",
            "manufacturer": "Manufactured & Packed in India",
            "net_quantity": "100 g / 1 Unit",
            "mrp": "₹50 (Inclusive of all taxes)",
            "batch_number": "BATCH-2026-X1",
            "mfg_date": "08/2026",
            "best_before": "Best Before 6 Months",
            "consumer_care": "contact@customercare.in",
            "ingredients": "Packaged food ingredients",
            "veg_non_veg": "Vegetarian",
            "fssai_license": "10024000000123",
            "country_of_origin": "India",
            "has_nutrition_issue": True,
            "declarations": [
                {
                    "field_name": "Product Name",
                    "detected_value": fallback_name,
                    "confidence": 88.0,
                    "confidence_level": "Medium",
                    "evidence_image_type": "front",
                    "bounding_box": "[100, 80, 500, 150]"
                },
                {
                    "field_name": "Net Quantity",
                    "detected_value": "100 g / 1 Unit",
                    "confidence": 89.5,
                    "confidence_level": "Medium",
                    "evidence_image_type": "front",
                    "bounding_box": "[300, 400, 450, 440]"
                },
                {
                    "field_name": "MRP (Maximum Retail Price)",
                    "detected_value": "₹50 (Incl. of taxes)",
                    "confidence": 91.0,
                    "confidence_level": "High",
                    "evidence_image_type": "back",
                    "bounding_box": "[260, 110, 420, 150]"
                },
                {
                    "field_name": "Veg / Non-Veg Logo",
                    "detected_value": "Green dot logo detected",
                    "confidence": 92.0,
                    "confidence_level": "High",
                    "evidence_image_type": "front",
                    "bounding_box": "[50, 50, 100, 100]"
                },
                {
                    "field_name": "FSSAI License Requirement",
                    "detected_value": "FSSAI registration reference found",
                    "confidence": 72.0,
                    "confidence_level": "Medium",
                    "evidence_image_type": "back",
                    "bounding_box": "[80, 300, 360, 340]"
                },
                {
                    "field_name": "Mandatory Nutritional Panel",
                    "detected_value": "Nutritional panel detected, but trans-fat / sugar values uncertain",
                    "confidence": 69.0,
                    "confidence_level": "Low",
                    "evidence_image_type": "back",
                    "bounding_box": "[60, 400, 500, 520]"
                }
            ]
        }
