import google.generativeai as genai
import json
import re
from typing import List, Dict
from agents import MODEL_NAME

def build_policy_clauses(policy_text: str) -> List[Dict]:
    """🎯 Extract ALL policy clauses - FULL TEXT, GENERIC, NO LIMITS"""
    
    # STEP 1: AI EXTRACTION (FULL DOCUMENT)
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
Extract ALL SPECIFIC policy clauses from document. Get EVERY:
- Numbered sections (1.1, 2.3, SECTION 1, etc.)
- Requirements, prohibitions, timelines (days, months, years)
- Compliance policies, thresholds, verification rules

FULL POLICY DOCUMENT:

{policy_text}

Return ONLY valid JSON array - ALL clauses found:
[
  {{"id": "clause_1", "text": "Full clause text", "section": "1.1"}},
  ...
]
"""
    
    try:
        resp = model.generate_content(prompt)
        clauses = json.loads(resp.text.strip())
        print(f"✅ AI extracted {len(clauses)} clauses (ALL)")
        return clauses  # NO LIMIT
    except:
        print("⚠️ AI extraction failed → GENERIC FALLBACK")
    
    # STEP 2: GENERIC FALLBACK (ALL SECTIONS)
    clauses = []
    
    # GENERIC SECTION PATTERNS
    section_patterns = r'(SECTION \d+| \d\.\d+|\d+\.\d+|\d+\w+|PART \d+|CHAPTER \d+)'
    sections = re.split(section_patterns, policy_text, flags=re.IGNORECASE)
    
    # GENERIC VIOLATION PATTERNS
    violation_patterns = [
        r'(\d+ (?:months?|days?|years?|crores?|lakhs?))',
        r'(self[-\s]?declaration)', r'(written confirmation)', r'(not mandatory)', 
        r'(next business day)', r'(tier[-—]?\d+)', r'(pre[-]?approved)',
        r'(no re[-]?verification)', r'(trustee)', r'(simplified)'
    ]
    
    clause_id = 1
    for section in sections:  # FULL PROCESSING
        section = section.strip()
        if len(section) > 30:
            violations = []
            for pattern in violation_patterns:
                match = re.search(pattern, section, re.IGNORECASE)
                if match:
                    violations.append(match.group(1))
            
            clauses.append({
                "id": f"clause_{clause_id}",
                "text": section[:1200],
                "section": f"SEC-{clause_id}",
                "violations_detected": violations
            })
            clause_id += 1
    
    # GENERIC KEYWORD EXTRACTION
    keyword_clauses = extract_policy_keywords(policy_text)
    clauses.extend(keyword_clauses)
    
    print(f"✅ FULL FALLBACK: {len(clauses)} clauses extracted")
    return clauses  # ALL CLAUSES

def extract_policy_keywords(policy_text: str) -> List[Dict]:
    """Generic keyword extraction - NO bank-specific terms"""
    generic_keywords = [
        'calendar days', 'months?', 'years?', 'not mandatory', 'self-declaration',
        'written confirmation', 'next business day', 'tier-', 'pre-approved'
    ]
    
    clauses = []
    for kw_pattern in generic_keywords:
        matches = list(re.finditer(re.escape(kw_pattern), policy_text, re.IGNORECASE))
        for match in matches:
            start = max(0, match.start() - 150)
            end = min(len(policy_text), match.end() + 250)
            clauses.append({
                "id": f"kw_clause_{len(clauses)+1}",
                "text": policy_text[start:end],
                "section": f"KEYWORD-{kw_pattern.upper()}",
                "violations_detected": [kw_pattern]
            })
    
    return clauses

if __name__ == "__main__":
    test_text = "KYC refresh every 36 months. STRs within 10 calendar days. OFAC screening not mandatory."
    clauses = build_policy_clauses(test_text)
    print(f"Test: Extracted ALL {len(clauses)} clauses")
