import json
from typing import Dict
import time

from agents.ingestion_agent import build_policy_clauses
from agents.rbi_search_agent import extract_rbi_rules_from_web
from agents.linking_agent import link_policy_to_rbi
from agents.conflict_agent import detect_conflict
from agents.risk_shap_agent import score_risk
from agents.narrative_agent import build_narrative

# FIXED SYMBOLS
CONFLICT_SYMBOLS = {
    'CONTRADICTSREG': '🚨 CONTRADICTS REG',
    'RELAXESREG': '⚠️ RELAXES REG',
    'STRICTERTHANREG': '✅ STRICTER THAN REG',
    'FULLYALIGNS': '✓ FULLY ALIGNS'
}

def run_clarity(policy_text: str) -> Dict:
    print("🚀 Processing policy text...")
    start_time = time.time()

    clauses = build_policy_clauses(policy_text)
    clause_count = len(clauses)
    print(f"📄 {clause_count} policy clauses extracted")

    max_pairs = min(clause_count * 2, 40)
    max_conflicts = min(int(clause_count * 1.2), 30)

    rbi_rules = extract_rbi_rules_from_web(policy_text)[:12]

    print(f"⚡ Dynamic: {max_pairs} pairs | {max_conflicts} conflicts | {len(rbi_rules)} RBI rules")

    links = link_policy_to_rbi(clauses, rbi_rules)[:max_pairs]

    print("🔍 Detecting conflicts...")
    conflicts = []
    seen_policy_rules = set()

    for i, link in enumerate(links):
        print(f"🔍 Checking pair {i+1}/{len(links)}...")
        conflict = detect_conflict(link)

        status = conflict.get("status", "UNKNOWN")
        print(f"  {CONFLICT_SYMBOLS.get(status, '❓ UNKNOWN')}")

        rule_id = (conflict.get("policyid"), conflict.get("rulematched"))

        if (
            status in ["RELAXESREG", "CONTRADICTSREG"]
            and rule_id not in seen_policy_rules
            and len(conflicts) < max_conflicts
        ):
            seen_policy_rules.add(rule_id)
            score_risk(conflict)
            build_narrative(conflict)
            conflicts.append(conflict)

    duration = round(time.time() - start_time, 1)

    critical_count = sum(1 for c in conflicts if c["status"] == "CONTRADICTSREG")
    warning_count = sum(1 for c in conflicts if c["status"] == "RELAXESREG")

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "processing_time_seconds": duration,
        "policy_clauses_count": clause_count,
        "rbi_rules_matched": len(rbi_rules),
        "pairs_checked": len(links),
        "conflicts": conflicts,
        "summary": {
            "critical": critical_count,
            "warnings": warning_count,
            "safe": len(links) - len(conflicts),
            "total_checked": len(links)
        }
    }

    print(
        f"\n🎯 Summary: {critical_count} 🚨 + {warning_count} ⚠️ "
        f"= {len(conflicts)} conflicts in {duration}s"
    )

    return output
