# rules/applicability/ — Partially implemented

Basic applicability filtering (by product category / sub-category)
already runs inside RuleEngine.get_applicable_rules() in
backend/app/services/rule_engine.py. This directory is reserved for
richer applicability logic (pack type, sales channel, inspection
date, documented exceptions) as a standalone, testable module,
per docs/MetraAI_Final_Tech_Stack.pdf section 9. See docs/ROADMAP.md.
