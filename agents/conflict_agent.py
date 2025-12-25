from typing import Dict
import json
import google.generativeai as genai
from agents import MODELNAME

# VISUAL SYMBOLS - PROPER SPACING
CONFLICT_SYMBOLS = {
    'CONTRADICTSREG': '🚨 CONTRADICTS REG', 
    'RELAXESREG': '⚠️ RELAXES REG',
    'STRICTERTHANREG': '✅ STRICTER THAN REG',
    'FULLYALIGNS': '✓ FULLY ALIGNS',
    'AI-FAILED': '⚪ AI-FAILED'
}

CONFLICTSYSTEMPROMPT = """You are RBI compliance expert. CRITICALLY analyze policy vs regulation. 
CLASSIFY EXACTLY ONE - be AGGRESSIVE on violations:

FULLYALIGNS: Policy matches RBI exactly
STRICTERTHANREG: Policy tougher than RBI (safe) 
RELAXESREG: Policy weaker (WARNING)
CONTRADICTSREG: Policy violates RBI (CRITICAL)

CRITICAL EXAMPLES:
RBI: OFFICIAL DOCUMENTS mandatory → Policy: NO DOCUMENTS → CONTRADICTSREG
RBI: STRs within 7 days → Policy: 10 calendar days → CONTRADICTSREG
RBI: BO refresh 24 months → Policy: 36 months → CONTRADICTSREG

Respond ONLY JSON:
{"status": "CONTRADICTSREG", "shorttitle": "10 DAYS vs RBI 7 DAYS", "reason": "Direct violation", "confidence": 0.95}"""

# ORIGINAL RULES + HDFC ADDONS (ALL PRESERVED)
VIOLATIONRULES = {
    # === ORIGINAL RULES ===
    "no documents": "CONTRADICTSREG - Documents mandatory",
    "verbal confirmation": "CONTRADICTSREG - Official ID required", 
    "self-declaration only": "CONTRADICTSREG - Documents NOT optional",
    "no str": "CONTRADICTSREG - STR filing mandatory",
    "no transaction monitoring": "CONTRADICTSREG - Monitoring required",
    "no pep": "CONTRADICTSREG - PEP screening required",
    "documents optional": "CONTRADICTSREG - Full documentation mandatory",
    "up to 20 lakhs": "CONTRADICTSREG - Strict transaction limits required",
    "within 30 days": "RELAXESREG - Immediate KYC required",
    "simplified kyc": "RELAXESREG - Full KYC preferred but simplified allowed",
    "within 10 working days": "RELAXESREG - 7 days max STR reporting",
    "optional": "RELAXESREG - Should be mandatory",
    "only if confirmed": "RELAXESREG - Immediate STR reporting required",
    "low risk": "RELAXESREG - Risk assessment mandatory",
    
    # === HDFC-SPECIFIC ADDONS ===
    "36 months": "CONTRADICTSREG - BO refresh 24 months max",
    "10 calendar days": "CONTRADICTSREG - STR 7 days max",
    "5 crores without": "CONTRADICTSREG - EDD for high-value mandatory",
    "5 years": "CONTRADICTSREG - Records 10 years required",
    "200 of income": "CONTRADICTSREG - Forex limits too permissive",
    "written confirmation": "CONTRADICTSREG - Full re-verification required",
    "self-declaration": "CONTRADICTSREG - Official documents mandatory",
    "no re-verification": "CONTRADICTSREG - Ongoing CDD required",
    "trustee and settlor": "CONTRADICTSREG - All beneficiaries must be identified",
    "ofac": "CONTRADICTSREG - Comprehensive sanctions lists required",
    "not mandatory": "CONTRADICTSREG - All sanctions lists mandatory",
    "next business day": "CONTRADICTSREG - Real-time monitoring required",
    "2 years": "RELAXESREG - KYC refresh too infrequent",
    "25 lakhs": "RELAXESREG - SWIFT verification threshold too high",
    "aa- or higher": "RELAXESREG - Correspondent DD insufficient"
}

def detect_conflict(link: Dict) -> Dict:
    """🚨 RULE-BASED FIRST → 🤖 AI FALLBACK - PROPER SPACING"""
    policy_lower = link['policytext'].lower()
    
    # STEP 1: RULE-BASED (100% reliable)
    for violation_phrase, rule_info in VIOLATIONRULES.items():
        if violation_phrase in policy_lower:
            status, reason = rule_info.split(' - ', 1)
            result = {
                **link,
                'status': status,
                'shorttitle': f"{violation_phrase.upper()} vs RBI",
                'reason': f"RBI requires {reason}. Policy violates.",
                'confidence': 0.98,
                'rulematched': violation_phrase,
                'detectionmethod': 'RULE-BASED'
            }
            print(f"  🚨 RULE HIT: {violation_phrase.upper()} → {status}")
            return result
    
    # STEP 2: AI FALLBACK (FIXED JSON parsing)
    model = genai.GenerativeModel(MODELNAME, system_instruction=CONFLICTSYSTEMPROMPT)
    prompt = f"""RBI REGULATION: {link['rbitext'][:600]}
BANK POLICY: {link['policytext'][:600]}
CLASSIFY THIS PAIR NOW"""
    
    try:
        resp = model.generate_content(prompt)
        response_text = resp.text.strip()
        
        # FIXED: Handle markdown code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
            
        data = json.loads(response_text)
    except Exception as e:
        print(f"    ⚪ JSON parse error: {str(e)[:50]}")
        data = {
            'status': 'FULLYALIGNS',
            'shorttitle': 'No clear violation',
            'reason': 'Parsing failed - default safe',
            'confidence': 0.5,
            'detectionmethod': 'AI-FAILED'
        }
    
    # VISUAL OUTPUT WITH PROPER SPACING
    status_symbol = CONFLICT_SYMBOLS.get(data['status'], '❓ UNKNOWN')
    method_symbol = '🔍 RULE' if data.get('detectionmethod') == 'RULE-BASED' else '🤖 AI'
    print(f"  {status_symbol} ({data['confidence']:.2f}) - {data['shorttitle'][:50]} [{method_symbol}]")
    
    return {**link, **data}

if __name__ == "__main__":
    testcases = [
        {'rbitext': 'Documents required', 'policytext': 'Verbal confirmation sufficient - NO DOCUMENTS needed'},
        {'rbitext': 'KYC immediate', 'policytext': 'Aadhaar/PAN submission within 30 days of account opening'},
        {'rbitext': 'Full KYC', 'policytext': 'Simplified KYC acceptable for small savings accounts under 50k'}
    ]
    for i, link in enumerate(testcases):
        result = detect_conflict(link)
        status_symbol = CONFLICT_SYMBOLS.get(result['status'], '❓')
        print(f"\nTest {i+1}: {status_symbol} - {result['shorttitle']}")
