"""
Legal Lens - Automated End-to-End API Test Suite
Smart India Hackathon Prototype Verification
"""
import os
import sys
import unittest
from fastapi.testclient import TestClient

# This file lives at tests/backend/test_api.py, three levels below the
# project root (tests/backend/ -> tests/ -> project root), so climb up
# three directories to put the project root on sys.path.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import LegalRule, User, Product, Inspection, Request, Report, AuditLog


class TestLegalLensAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["system"], "Legal Lens")
        self.assertEqual(data["compliance_rules"], 26)

    def test_02_login_citizen(self):
        res = self.client.post("/api/auth/login", json={
            "email": "user@legallens.demo",
            "password": "user123",
            "role": "user"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "user")
        self.assertEqual(data["user"]["full_name"], "Rahul Sharma")

    def test_03_login_officer(self):
        res = self.client.post("/api/auth/login", json={
            "email": "admin@legallens.demo",
            "password": "admin123",
            "role": "officer"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "officer")
        self.assertEqual(data["user"]["full_name"], "Vikram Malhotra")

    def test_04_rules_repository(self):
        res = self.client.get("/api/rules")
        self.assertEqual(res.status_code, 200)
        rules = res.json()
        self.assertEqual(len(rules), 26, "Should load all 26 rules from CSV")

        rule_ids = [r["rule_id"] for r in rules]
        self.assertIn("LAB-NUT-001", rule_ids)
        self.assertIn("LAB-VEG-001", rule_ids)
        self.assertIn("LIC-FBO-001", rule_ids)
        self.assertIn("PKG-WAT-001", rule_ids)

        res_single = self.client.get("/api/rules/LAB-NUT-001")
        self.assertEqual(res_single.status_code, 200)
        self.assertEqual(res_single.json()["rule_title"], "Mandatory Nutritional Panel")

    def test_05_inspection_workflow(self):
        create_res = self.client.post("/api/inspections", json={
            "barcode": "8901234567890",
            "product_name": "CrunchBite Classic Potato Chips",
            "brand": "CrunchBite",
            "category": "Packaged Food"
        })
        self.assertEqual(create_res.status_code, 200)
        ins_data = create_res.json()
        ins_id = ins_data["id"]
        ins_code = ins_data["inspection_code"]
        self.assertTrue(ins_code.startswith("LL-INS-2026-"))

        proc_res = self.client.post(f"/api/inspections/{ins_id}/process", data={
            "barcode": "8901234567890"
        })
        self.assertEqual(proc_res.status_code, 200)
        proc_data = proc_res.json()
        self.assertEqual(proc_data["overall_result"], "Potential Non-Compliance")
        self.assertGreater(proc_data["rules_checked_count"], 0)
        self.assertGreater(len(proc_data["declarations"]), 0)
        self.assertGreater(len(proc_data["compliance_results"]), 0)

        report_res = self.client.get(f"/api/inspections/{ins_id}/report")
        self.assertEqual(report_res.status_code, 200)
        self.assertEqual(report_res.headers["content-type"], "application/pdf")
        self.assertGreater(len(report_res.content), 1000)

    def test_06_citizen_request_workflow(self):
        req_res = self.client.post("/api/requests", json={
            "product_name": "CrunchBite Classic Potato Chips",
            "brand": "CrunchBite",
            "barcode": "8901234567890",
            "mrp": "\u20b950",
            "category": "Packaged Food",
            "shop_name": "Verma Grocery Store",
            "shop_address": "Chakrata Road, Dehradun",
            "city": "Dehradun",
            "state": "Uttarakhand",
            "citizen_name": "Rahul Sharma",
            "citizen_phone": "+91 98765 43210",
            "citizen_email": "rahul.sharma@email.demo",
            "description": "Blurred nutritional label with missing trans fat declaration.",
            "priority": "High"
        })
        self.assertEqual(req_res.status_code, 200)
        req_data = req_res.json()
        req_id = req_data["id"]
        req_code = req_data["request_code"]
        self.assertTrue(req_code.startswith("LL-REQ-2026-"))
        self.assertEqual(req_data["status"], "Submitted")

        action_res = self.client.post(f"/api/requests/{req_id}/action", json={
            "new_status": "Under Review",
            "remarks": "Accepted for field sampling by Dehradun inspector."
        })
        self.assertEqual(action_res.status_code, 200)
        updated_data = action_res.json()
        self.assertEqual(updated_data["status"], "Under Review")
        self.assertEqual(len(updated_data["officer_actions"]), 1)

    def test_07_audit_trail(self):
        res = self.client.get("/api/audit")
        self.assertEqual(res.status_code, 200)
        logs = res.json()
        self.assertGreater(len(logs), 0, "Audit logs should record actions")

    def test_08_violations_view(self):
        """New: violations are queryable as their own resource."""
        res = self.client.get("/api/violations")
        self.assertEqual(res.status_code, 200)
        violations = res.json()
        self.assertGreater(len(violations), 0, "Test 05 should have produced at least one violation")

    def test_09_declarations_and_compliance_subresources(self):
        """New: per-inspection sub-resource routers work independently."""
        ins_res = self.client.get("/api/inspections")
        self.assertEqual(ins_res.status_code, 200)
        inspections_list = ins_res.json()
        self.assertGreater(len(inspections_list), 0)
        ins_id = inspections_list[0]["id"]

        dec_res = self.client.get(f"/api/declarations/inspection/{ins_id}")
        self.assertEqual(dec_res.status_code, 200)

        comp_res = self.client.get(f"/api/compliance/inspection/{ins_id}")
        self.assertEqual(comp_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
