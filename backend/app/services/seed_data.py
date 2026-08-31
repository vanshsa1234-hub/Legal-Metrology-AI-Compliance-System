"""
Legal Lens - Data Seeder Service
Loads rules from rules/legal_rules/SIH_Legal_Compliance_Master.csv and
populates realistic demo records (users, products, inspections, cases).
"""
import os
import csv
import datetime
from sqlalchemy.orm import Session
from ..core.config import LEGAL_RULES_CSV
from ..core.security import hash_password
from ..models import (
    User, LegalRule, Product, Inspection, InspectionImage,
    ExtractedDeclaration, ComplianceResult, Report, Request, OfficerAction, AuditLog
)
from .rule_engine import RuleEngine
from .report_service import ReportService

# Kept as a thin alias so the rest of this file (and any external callers)
# don't need to change; the real implementation now lives in core.security
# so hashing logic isn't duplicated across the auth route and the seeder.
hash_pw = hash_password

def seed_database(db: Session, base_dir: str = None):
    """
    Seed initial rules, users, products, inspections, and requests.

    `base_dir` is accepted for backward compatibility with older call
    sites but is no longer used to locate the rules CSV — that path is
    now resolved centrally via core.config.LEGAL_RULES_CSV.
    """
    # 1. Seed Rules from CSV
    csv_path = LEGAL_RULES_CSV if os.path.exists(LEGAL_RULES_CSV) else None

    if csv_path and os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rule_id = (row.get("Rule ID") or "").strip()
                if not rule_id:
                    continue
                existing_rule = db.query(LegalRule).filter(LegalRule.rule_id == rule_id).first()
                if not existing_rule:
                    rule = LegalRule(
                        rule_id=rule_id,
                        rule_title=(row.get("Rule Title") or "").strip(),
                        legal_requirement=(row.get("Legal Requirement") or "").strip(),
                        description=(row.get("Description (Simple English)") or "").strip(),
                        product_category=(row.get("Product Category") or "").strip(),
                        mandatory_conditional=(row.get("Mandatory/Conditional") or "Mandatory").strip(),
                        evidence_required=(row.get("Evidence Required") or "").strip(),
                        applicable_regulation=(row.get("Applicable Regulation") or "").strip(),
                        clause=(row.get("Clause") or "").strip(),
                        version_amendment=(row.get("Version/Amendment") or "").strip(),
                        effective_date=(row.get("Effective Date") or "").strip(),
                        remarks=(row.get("Remarks") or "").strip()
                    )
                    db.add(rule)
            db.commit()
            print(f"Master Rules successfully loaded from {csv_path}!")

    # 2. Seed Users
    if db.query(User).count() == 0:
        demo_users = [
            User(
                email="user@legallens.demo",
                full_name="Rahul Sharma",
                password_hash=hash_pw("user123"),
                role="user",
                designation="Field Consumer / Citizen",
                department="Public Citizen"
            ),
            User(
                email="admin@legallens.demo",
                full_name="Vikram Malhotra",
                password_hash=hash_pw("admin123"),
                role="officer",
                designation="Senior Legal Metrology Officer",
                department="Legal Metrology Department, Northern Zone",
                badge_number="LMD-UK-8821"
            ),
            User(
                email="officer@legallens.demo",
                full_name="Pooja Verma",
                password_hash=hash_pw("officer123"),
                role="officer",
                designation="Food Safety Officer",
                department="FSSAI Enforcement Division",
                badge_number="FSSAI-NZ-4412"
            )
        ]
        db.add_all(demo_users)
        db.commit()
        print("Demo users seeded!")

    # 3. Seed Products
    if db.query(Product).count() == 0:
        products = [
            Product(
                product_name="CrunchBite Classic Potato Chips",
                brand="CrunchBite",
                category="Packaged Food",
                sub_category="Snacks / Chips",
                manufacturer="CrunchBite Foods India Pvt. Ltd., Haridwar, Uttarakhand",
                net_quantity="100 g",
                mrp="₹50",
                batch_number="CB24082401",
                mfg_date="08/2026",
                best_before="6 Months",
                consumer_care="care@crunchbite.in / 1800-200-8899",
                ingredients="Potatoes, edible vegetable oil (palmolein), iodised salt, spices and condiments",
                veg_non_veg="Vegetarian",
                country_of_origin="India",
                barcode="8901234567890",
                fssai_license="10018012000456"
            ),
            Product(
                product_name="FreshFarm Whole Wheat Atta",
                brand="FreshFarm",
                category="Packaged Food",
                sub_category="Staples / Flour",
                manufacturer="FreshFarm Agro Industries, Gurugram, Haryana",
                net_quantity="5 kg",
                mrp="₹245",
                batch_number="FF-AT2408-09",
                mfg_date="07/2026",
                best_before="3 Months",
                consumer_care="support@freshfarm.co.in / 1800-111-2233",
                ingredients="100% Whole Wheat Grain",
                veg_non_veg="Vegetarian",
                country_of_origin="India",
                barcode="8901030383812",
                fssai_license="10015064000789"
            ),
            Product(
                product_name="PureDrop Packaged Drinking Water",
                brand="PureDrop",
                category="Packaged Water",
                sub_category="Drinking Water",
                manufacturer="PureDrop Bottlers Pvt. Ltd., Dehradun",
                net_quantity="1 L",
                mrp="₹20",
                batch_number="PDW-9901",
                mfg_date="08/2026",
                best_before="6 Months",
                consumer_care="customercare@puredrop.in",
                ingredients="Treated Drinking Water with added minerals",
                veg_non_veg="Exempted",
                country_of_origin="India",
                barcode="8901456789012",
                fssai_license="10012011000321"
            ),
            Product(
                product_name="NutriStart Probiotic Dahi",
                brand="NutriStart",
                category="Probiotic Foods",
                sub_category="Dairy / Probiotic",
                manufacturer="NutriStart Dairy Specialities, Noida",
                net_quantity="400 g",
                mrp="₹65",
                batch_number="NS-DH-104",
                mfg_date="08/2026",
                best_before="15 Days",
                consumer_care="help@nutristart.com",
                ingredients="Pasteurised toned milk, active probiotic cultures (Bifidobacterium lactis >= 10^8 CFU/g)",
                veg_non_veg="Vegetarian",
                country_of_origin="India",
                barcode="8906010501234",
                fssai_license="10019022000543"
            ),
            Product(
                product_name="DailyHarvest Butter Cookies",
                brand="DailyHarvest",
                category="Packaged Food",
                sub_category="Bakery / Biscuits",
                manufacturer="DailyHarvest Bakeries Ltd., Kashipur, Uttarakhand",
                net_quantity="200 g",
                mrp="₹80",
                batch_number="DHB-883",
                mfg_date="08/2026",
                best_before="4 Months",
                consumer_care="hello@dailyharvest.in",
                ingredients="Wheat flour, butter, sugar, condensed milk, raising agents",
                veg_non_veg="Vegetarian",
                country_of_origin="India",
                barcode="8901063012345",
                fssai_license="10017042000678"
            )
        ]
        db.add_all(products)
        db.commit()
        print("Demo products seeded!")

    # 4. Seed Demo Inspections
    if db.query(Inspection).count() == 0:
        user = db.query(User).filter(User.role == "user").first()
        officer = db.query(User).filter(User.role == "officer").first()
        prods = db.query(Product).all()

        from ..core.config import REPORTS_DIR
        reports_dir = REPORTS_DIR
        os.makedirs(reports_dir, exist_ok=True)

        ins1 = Inspection(
            inspection_code="LL-INS-2026-0001",
            user_id=user.id,
            product_id=prods[0].id,
            product_name=prods[0].product_name,
            brand=prods[0].brand,
            category=prods[0].category,
            barcode=prods[0].barcode,
            status="Potential Non-Compliance",
            overall_result="Potential Non-Compliance",
            confidence_score=86.4,
            rules_checked_count=6,
            no_issue_count=4,
            review_required_count=1,
            non_compliance_count=1,
            officer_review_status="Pending",
            officer_remarks=None,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        )
        db.add(ins1)
        db.commit()
        db.refresh(ins1)

        decs1 = [
            ExtractedDeclaration(inspection_id=ins1.id, field_name="Product Name", detected_value="CrunchBite Classic Potato Chips", confidence=98.2, confidence_level="High", evidence_image_type="front"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="MRP", detected_value="₹50 (Incl. of taxes)", confidence=95.8, confidence_level="High", evidence_image_type="back"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="Net Quantity", detected_value="100 g", confidence=96.0, confidence_level="High", evidence_image_type="front"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="Veg / Non-Veg", detected_value="Green dot logo (Vegetarian)", confidence=96.2, confidence_level="High", evidence_image_type="front"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="FSSAI License", detected_value="10018012000456", confidence=74.0, confidence_level="Medium", evidence_image_type="back"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="Nutritional Panel", detected_value="Energy 530 kcal, Protein 6.5g, Carbs 54g... [Trans fat/Added sugars breakdown incomplete]", confidence=68.5, confidence_level="Low", evidence_image_type="back"),
        ]
        db.add_all(decs1)

        res1 = [
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="LAB-NUT-001",
                rule_title="Mandatory Nutritional Panel",
                status="POTENTIAL NON-COMPLIANCE",
                confidence=72.5,
                evidence_type="Back Image",
                reason="Required nutritional declaration could not be confidently verified from the supplied package images.",
                what_checked="Mandatory Nutritional Information declaration per 100g/serving",
                what_found="Nutritional panel detected, but complete declaration of trans-fat and added sugars could not be verified.",
                why_flagged="The available evidence does not provide sufficient confidence that the required declaration is complete.",
                applicable_regulation="Food Safety and Standards (Labelling and Display) Regs",
                clause="5(3)(b)",
                version_amendment="V-VIII (2025)"
            ),
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="LAB-VEG-001",
                rule_title="Veg / Non-Veg Logo",
                status="NO ISSUE DETECTED",
                confidence=96.2,
                evidence_type="Front Image",
                reason="Required vegetarian declaration detected prominently.",
                what_checked="Vegetarian (green circle) symbol on Principal Display Panel",
                what_found="Green circle inside green square detected on front panel.",
                applicable_regulation="Food Safety and Standards (Labelling and Display) Regs",
                clause="5(4)",
                version_amendment="V-VIII (2025)"
            ),
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="LIC-FBO-001",
                rule_title="FSSAI License Requirement",
                status="REVIEW REQUIRED",
                confidence=68.0,
                evidence_type="Back Image",
                reason="License information extracted requires officer verification against central database.",
                what_checked="14-digit FSSAI License Number",
                what_found="Lic. No. 10018012000456",
                why_flagged="Officer verification recommended to confirm active license status.",
                applicable_regulation="Food Safety and Standards (Licensing & Registration) Regs",
                clause="2.1.2(1)",
                version_amendment="V-II (2017)"
            ),
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="SAF-TRF-001",
                rule_title="Trans Fatty Acids Limit",
                status="REVIEW REQUIRED",
                confidence=82.0,
                evidence_type="Back Image",
                reason="Industrial trans fatty acid limit (<=2%) requires physical certified lab assay.",
                what_checked="Trans fatty acid threshold <= 2% of total fats",
                what_found="Standard oils declaration present.",
                why_flagged="Physical laboratory analysis required for conclusive determination.",
                applicable_regulation="Food Safety and Standards (Prohibition/Restriction) Regs",
                clause="2.3.14 (21)",
                version_amendment="V-XI (2025)"
            ),
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="PKG-MIG-001",
                rule_title="Plastic Migration Limits",
                status="REVIEW REQUIRED",
                confidence=80.0,
                evidence_type="Back Image",
                reason="Food contact plastic migration requires statutory batch memo.",
                what_checked="Plastic migration ceiling 60mg/kg",
                what_found="Food grade recyclable packaging mark present.",
                why_flagged="Batch testing certificate required for official record.",
                applicable_regulation="Food Safety and Standards (Packaging) Regulations",
                clause="4(4)(b)",
                version_amendment="V-V (2025)"
            ),
            ComplianceResult(
                inspection_id=ins1.id,
                rule_id="MFG-REC-001",
                rule_title="Mandatory Recall Traceability",
                status="NO ISSUE DETECTED",
                confidence=92.5,
                evidence_type="Back Image",
                reason="Batch number and manufacturing date clearly visible for product recall traceability.",
                what_checked="Lot / Batch number and Packing date",
                what_found="Batch: CB24082401, Mfg: 08/2026",
                applicable_regulation="Food Safety and Standards (Food Recall Procedure) Regs",
                clause="6(1)",
                version_amendment="2017"
            )
        ]
        db.add_all(res1)
        db.commit()

        rpt1 = Report(
            report_code="LL-RPT-2026-0001",
            inspection_id=ins1.id,
            user_id=user.id,
            file_path=os.path.join(reports_dir, "LL-RPT-2026-0001.pdf"),
            file_name="LL-RPT-2026-0001.pdf",
            summary="Inspection detected Potential Non-Compliance on LAB-NUT-001 (Nutritional Panel) and 3 items under Review."
        )
        db.add(rpt1)
        db.commit()

        try:
            ReportService.generate_inspection_pdf("LL-RPT-2026-0001", ins1, prods[0], decs1, res1, reports_dir)
        except Exception as e:
            print(f"Error building PDF for ins1: {e}")

        ins2 = Inspection(
            inspection_code="LL-INS-2026-0002",
            user_id=user.id,
            product_id=prods[1].id,
            product_name=prods[1].product_name,
            brand=prods[1].brand,
            category=prods[1].category,
            barcode=prods[1].barcode,
            status="Completed",
            overall_result="No Issue Detected",
            confidence_score=95.8,
            rules_checked_count=5,
            no_issue_count=5,
            review_required_count=0,
            non_compliance_count=0,
            officer_review_status="Verified",
            officer_remarks="Mandatory declarations and FSSAI license verified against central registry.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        db.add(ins2)

        ins3 = Inspection(
            inspection_code="LL-INS-2026-0003",
            user_id=user.id,
            product_id=prods[2].id,
            product_name=prods[2].product_name,
            brand=prods[2].brand,
            category=prods[2].category,
            barcode=prods[2].barcode,
            status="Completed",
            overall_result="No Issue Detected",
            confidence_score=94.2,
            rules_checked_count=4,
            no_issue_count=4,
            review_required_count=0,
            non_compliance_count=0,
            officer_review_status="Verified",
            officer_remarks="Transparency standards and water labeling exemption verified.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
        )
        db.add(ins3)

        ins4 = Inspection(
            inspection_code="LL-INS-2026-0004",
            user_id=user.id,
            product_id=prods[4].id,
            product_name=prods[4].product_name,
            brand=prods[4].brand,
            category=prods[4].category,
            barcode=prods[4].barcode,
            status="Review Required",
            overall_result="Review Required",
            confidence_score=78.2,
            rules_checked_count=6,
            no_issue_count=3,
            review_required_count=3,
            non_compliance_count=0,
            officer_review_status="Pending",
            officer_remarks=None,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=3)
        )
        db.add(ins4)
        db.commit()

    # 5. Seed Demo Citizen Requests
    if db.query(Request).count() == 0:
        user = db.query(User).filter(User.role == "user").first()
        officer = db.query(User).filter(User.role == "officer").first()
        ins1 = db.query(Inspection).filter(Inspection.inspection_code == "LL-INS-2026-0001").first()
        ins4 = db.query(Inspection).filter(Inspection.inspection_code == "LL-INS-2026-0004").first()

        reqs = [
            Request(
                request_code="LL-REQ-2026-0001",
                inspection_id=ins1.id if ins1 else None,
                user_id=user.id,
                product_name="CrunchBite Classic Potato Chips",
                brand="CrunchBite",
                barcode="8901234567890",
                mrp="₹50",
                category="Packaged Food",
                purchase_date="24 Aug 2026",
                place_of_purchase="Paltan Bazaar, Dehradun",
                shop_name="Gupta Provision & General Store",
                shop_address="Shop No. 14, Main Market, Paltan Bazaar, Dehradun, Uttarakhand 248001",
                city="Dehradun",
                state="Uttarakhand",
                market_area="Paltan Bazaar",
                latitude=30.3165,
                longitude=78.0322,
                citizen_name="Rahul Sharma",
                citizen_phone="+91 98765 43210",
                citizen_email="rahul.sharma@email.demo",
                preferred_contact="Phone",
                description="I bought this packet of CrunchBite potato chips today. The nutritional table on the back is blurry, incomplete, and missing trans-fat breakdown. Kindly inspect the distributor batch.",
                priority="High",
                status="Submitted",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            ),
            Request(
                request_code="LL-REQ-2026-0002",
                inspection_id=ins4.id if ins4 else None,
                user_id=user.id,
                product_name="DailyHarvest Butter Cookies",
                brand="DailyHarvest",
                barcode="8901063012345",
                mrp="₹80",
                category="Packaged Food",
                purchase_date="22 Aug 2026",
                place_of_purchase="Haridwar Road, Rishikesh",
                shop_name="SuperMart Grocery",
                shop_address="21, Bypass Road, Rishikesh, Uttarakhand 249201",
                city="Rishikesh",
                state="Uttarakhand",
                market_area="Bypass Market",
                latitude=30.0869,
                longitude=78.2676,
                citizen_name="Rahul Sharma",
                citizen_phone="+91 98765 43210",
                citizen_email="rahul.sharma@email.demo",
                preferred_contact="Email",
                description="MRP overcharging observed at the counter. The printed MRP is smudged with a sticker priced higher.",
                priority="Medium",
                status="Under Review",
                officer_remarks="Assigned to Field Inspector for physical shelf verification on 26th Aug.",
                officer_id=officer.id,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
            ),
            Request(
                request_code="LL-REQ-2026-0003",
                inspection_id=None,
                user_id=user.id,
                product_name="Himalayan Herbal Health Tonic",
                brand="Mountain Cure",
                barcode="8908821990123",
                mrp="₹320",
                category="Ayurveda Aahara",
                purchase_date="20 Aug 2026",
                place_of_purchase="Civil Lines, Roorkee",
                shop_name="Arogya Medical & Wellness",
                shop_address="Near IIT Roorkee Gate, Civil Lines, Roorkee 247667",
                city="Roorkee",
                state="Uttarakhand",
                market_area="Civil Lines",
                latitude=29.8543,
                longitude=77.8880,
                citizen_name="Amit Patel",
                citizen_phone="+91 91234 56789",
                citizen_email="amit.patel@email.demo",
                preferred_contact="Phone",
                description="Suspected synthetic vitamins added in an Ayurveda Aahara marketed for toddlers.",
                priority="Urgent",
                status="Action Initiated",
                officer_remarks="Notices issued under Regulation 3(2) and 3(4). Statutory lab sample dispatch memo QTY-SMP-001 initiated.",
                officer_id=officer.id,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=4)
            )
        ]
        db.add_all(reqs)
        db.commit()

    # 6. Seed Initial Audit Logs
    if db.query(AuditLog).count() == 0:
        logs = [
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=3), user_email="system@legallens.demo", user_role="System", action="System Initialization", entity_type="System", details="Master compliance rules loaded from CSV repository (26 provisions)."),
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2), user_email="user@legallens.demo", user_role="user", action="Inspection Created", entity_type="Inspection", entity_id="LL-INS-2026-0001", details="Product scanned: CrunchBite Classic Potato Chips"),
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2), user_email="system@legallens.demo", user_role="System", action="Rules Evaluated", entity_type="Inspection", entity_id="LL-INS-2026-0001", details="6 rules evaluated. Result: Potential Non-Compliance on LAB-NUT-001"),
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2), user_email="system@legallens.demo", user_role="System", action="Report Generated", entity_type="Report", entity_id="LL-RPT-2026-0001", details="PDF Report generated and signed with SHA-256 hash"),
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1), user_email="user@legallens.demo", user_role="user", action="Request Raised", entity_type="Request", entity_id="LL-REQ-2026-0001", details="Citizen complaint submitted for shop 'Gupta Provision Store'"),
            AuditLog(timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=1), user_email="admin@legallens.demo", user_role="officer", action="Status Updated", entity_type="Request", entity_id="LL-REQ-2026-0002", details="Status changed from Submitted to Under Review")
        ]
        db.add_all(logs)
        db.commit()
