from typing import Dict
import google.generativeai as genai
from agents import MODELNAME

NARRATIVE_SYSTEM_PROMPT = """
You write clear compliance reports for bank executives and RBI auditors.

Structure:
1. State the RBI requirement
2. State what bank policy says  
3. Explain the gap/conflict
4. Give risk score + why
5. Suggest next action

Keep it concise (3-4 sentences), professional tone.
"""

def build_narrative(conflict: Dict) -> Dict:
    """AI-powered audit-ready narrative - FIXED KEYS"""
    model = genai.GenerativeModel(MODELNAME, system_instruction=NARRATIVE_SYSTEM_PROMPT)
    
    # FIXED: Use correct keys from conflict_agent.py
    rbitext = conflict.get('rbitext', '')
    policytext = conflict.get('policytext', '')
    risk_score = conflict.get('risk_score', 0)
    components = conflict.get('components', {})
    status = conflict.get('status', '')
    rulematched = conflict.get('rulematched', '')
    
    prompt = f"""
RBI Requirement: {rbitext}
Bank Policy: {policytext}
Status: {status}
Rule Triggered: {rulematched}
Risk Score: {risk_score}/10
Factors - Strictness: {components.get('regulatory_strictness', 0)}, Gap: {components.get('policy_gap', 0)}, Exposure: {components.get('audit_exposure', 0)}

Write audit-ready narrative following exact structure.
"""
    
    try:
        resp = model.generate_content(prompt)
        conflict["narrative"] = resp.text.strip()  # Cap for frontend
        print(f"   📝 Narrative generated ({len(conflict['narrative'])} chars)")
    except Exception as e:
        print(f"   ⚠️ Narrative failed: {e}")
        conflict["narrative"] = f"""
VIOLATION SUMMARY ({status})

RBI: {rbitext}
Policy: {policytext}
Risk: {risk_score}/10

Action Required: Immediate policy alignment needed.
"""
    
    return conflict

if __name__ == "__main__":
    test_conflict = {
        'status': 'CONTRADICTSREG',
        'rbitext': 'STRs must be filed within 7 calendar days to FIU-IND',
        'policytext': 'STRs prepared within 7 days but filed within 10 calendar days after manager approval',
        'rulematched': '10 calendar days',
        'risk_score': 9.3,
        'components': {'regulatory_strictness': 3.2, 'policy_gap': 3.5, 'audit_exposure': 2.6}
    }
    
    result = build_narrative(test_conflict)
    print("✅ Test Narrative:")
    print(result["narrative"])
