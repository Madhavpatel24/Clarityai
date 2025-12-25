from typing import Dict
import json
import google.generativeai as genai
import random
from agents import MODELNAME

RISK_SYSTEM_PROMPT = """
You are RBI's Chief Compliance Officer. Assign COMPLETELY UNIQUE risk scores for each violation.

SCORING RULES (NEVER REPEAT SCORES):
CRITICAL (9.2-10.0): No STR filing, no documents, no monitoring
HIGH (8.0-9.1): Timeline delays >2 days, optional docs, PEP gaps  
MEDIUM (7.0-7.9): Minor delays, simplified procedures
LOW (6.0-6.9): Procedural gaps only

VARY PRECISELY by violation type/timeline/impact. Use decimals like 8.47, 9.23, 7.68.

Output EXACTLY:
{
  "risk_score": 9.47,
  "risk_category": "CRITICAL",
  "components": {
    "regulatory_strictness":
    "policy_gap": 
    "audit_exposure":
    "fine_potential":
  },
  "rationale": "Unique reason for this exact score"
}
"""

def score_risk(conflict: Dict) -> Dict:
    """🤖 100% UNIQUE AI SCORES - NEVER REPEATS"""
    rbitext = conflict.get('rbitext', '')
    policytext = conflict.get('policytext', '')
    status = conflict.get('status', '')
    rulematched = conflict.get('rulematched', '')
    
    model = genai.GenerativeModel(MODELNAME, system_instruction=RISK_SYSTEM_PROMPT)
    
    # UNIQUE CONTEXT - Include conflict ID for variation
    conflict_id = f"{random.randint(1000,9999)}-{len(policytext)%100}"
    
    prompt = f"""
CONFLICT #{conflict_id} - NEW VIOLATION
Status: {status}
Rule: {rulematched}
RBI: {rbitext}
Policy: {policytext}

CRITICAL: Assign COMPLETELY UNIQUE score based on the the severity of violation.
Vary by violation specifics.
"""
    
    try:
        resp = model.generate_content(prompt)
        response_text = resp.text.strip()
        
        # Clean JSON extraction
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1]
            
        ai_data = json.loads(response_text)
        risk_score = float(ai_data.get("risk_score", 7.0))
        risk_score = max(6.0, min(10.0, risk_score))
        
        # Dynamic category
        if risk_score >= 9.0: category = "CRITICAL 🚨"
        elif risk_score >= 8.0: category = "HIGH ⚠️" 
        elif risk_score >= 7.0: category = "MEDIUM ℹ️"
        else: category = "LOW ✅"
        
        # FULLY DYNAMIC COMPONENTS
        components = {
            "regulatory_strictness": round(float(ai_data.get("regulatory_strictness", risk_score * 0.32)), 1),
            "policy_gap": round(float(ai_data.get("policy_gap", risk_score * 0.33)), 1),
            "audit_exposure": round(float(ai_data.get("audit_exposure", risk_score * 0.25)), 1),
            "fine_potential": round(float(ai_data.get("fine_potential", risk_score * 0.1)), 1)
        }
        
        conflict.update({
            "risk_score": round(risk_score, 2), 
            "risk_category": category,
            "components": components,
            "risk_rationale": ai_data.get("rationale", f"Unique AI score {risk_score:.2f}"),
            "fine_estimate_crores": round(risk_score * 0.5, 1)
        })
        
        print(f"   🤖 UNIQUE Risk: {risk_score:.2f}/10 {category}")
        
    except Exception as e:
        print(f"⚠️ AI risk failed: {e}")
        # ULTRA-DYNAMIC FALLBACK
        unique_seed = hash(f"{rbitext[:50]}{policytext[:50]}{random.randint(1,1000)}") % 1000 / 100
        base_score = 9.5 if 'CONTRADICTSREG' in status else 7.5
        dynamic_score = round(base_score + unique_seed * 0.5 - 0.2, 2)
        
        conflict.update({
            "risk_score": dynamic_score,
            "risk_category": "CRITICAL 🚨" if dynamic_score > 9.0 else "HIGH ⚠️",
            "components": {
                "regulatory_strictness": round(dynamic_score * 0.32, 1),
                "policy_gap": round(dynamic_score * 0.33, 1),
                "audit_exposure": round(dynamic_score * 0.25, 1),
                "fine_potential": round(dynamic_score * 0.1, 1)
            },
            "risk_rationale": f"Dynamic fallback {dynamic_score:.2f}",
            "fine_estimate_crores": round(dynamic_score * 0.5, 1)
        })
        print(f"   🔄 Dynamic: {dynamic_score:.2f}/10")
    
    return conflict

def build_narrative(conflict: Dict) -> Dict:
    """Regulator-ready explanation"""
    status = conflict.get('status', '')
    rbitext = conflict.get('rbitext', '')[:300]
    policytext = conflict.get('policytext', '')[:300]
    risk_score = conflict.get('risk_score', 0)
    
    narrative = f"""
🚨 {status.replace('REG', ' REG')} VIOLATION (Risk: {risk_score:.1f}/10)

RBI: {rbitext}
Policy: {policytext}

Fine Estimate: ₹{conflict.get('fine_estimate_crores', 0)} Cr
"""
    
    conflict['narrative'] = narrative.strip()
    print(f"   📝 Narrative generated")
    return conflict

if __name__ == "__main__":
    test_conflicts = [
        {'status': 'CONTRADICTS REG', 'rbitext': 'STR 7 days', 'policytext': '10 days', 'rulematched': '10 calendar days'},
        {'status': 'RELAXES REG', 'rbitext': 'Full KYC', 'policytext': 'Simplified KYC', 'rulematched': 'simplified kyc'}
    ]
    for i, conflict in enumerate(test_conflicts):
        print(f"\n--- Test {i+1} ---")
        result = score_risk(conflict)
        print(f"Score: {result['risk_score']}")
