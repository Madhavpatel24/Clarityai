from typing import List, Dict
import google.generativeai as genai
from agents import MODELNAME
import json

def link_policy_to_rbi(clauses: List[Dict], rbi_rules: List[Dict]) -> List[Dict]:
    """DYNAMIC linking based on input size"""
    print("🔗 Dynamic linking...")
    
    links = keyword_fallback(clauses, rbi_rules)
    
    # Scale AI usage by clause count
    if len(links) < len(clauses) * 1.5:  # Need more links?
        try:
            clauses_text = '\n'.join([f"{c['id']}: {c['text'][:200]}" for c in clauses[:15]])  # Limit context
            rbi_text = '\n'.join([f"{r['id']}: {r['text'][:200]}" for r in rbi_rules])
            
            model = genai.GenerativeModel(MODELNAME)
            target_links = min(len(clauses) * 2, 40)
            prompt = f"""POLICY CLAUSES: {clauses_text}
RBI RULES: {rbi_text}

Create {target_links} JSON links between clauses and rules.
Return ONLY valid JSON array:
[
  {{"policyid": "clauseX", "rbiid": "ruleY", "similarity": 0.85}},
  ...
]
"""
            
            resp = model.generate_content(prompt)
            ai_links_data = json.loads(resp.text.strip())
            
            for link_data in ai_links_data:
                policy_clause = next((c for c in clauses if c['id'] == link_data['policyid']), clauses[0])
                rbi_rule = next((r for r in rbi_rules if r['id'] == link_data['rbiid']), rbi_rules[0])
                links.append({
                    'policyid': link_data['policyid'],
                    'policytext': policy_clause['text'],
                    'rbiid': link_data['rbiid'],
                    'rbitext': rbi_rule['text'],
                    'similarity': link_data['similarity']
                })
        except Exception as e:
            print(f"AI linking failed: {e}")
    
    print(f"🔗 Created {len(links)} policy-RBI pairs")
    return links  # No hard limit

def keyword_fallback(clauses: List[Dict], rbi_rules: List[Dict]) -> List[Dict]:
    """Unified keyword matching"""
    policy_keywords = [
        'kyc', 'str', 'pep', 'monitoring', 'documents', 'cash', 'beneficial', 
        'sanctions', 'swift', 'verification', 'threshold', 'reporting',
        'tier-1', 'pre-approved', 'internal assessment', 'written confirmation', 
        'ofac', 'self-declaration', 'not mandatory', 'next business day'
    ]
    
    links = []
    for clause in clauses:
        clause_lower = clause['text'].lower()
        best_matches = []
        
        for rbi in rbi_rules[:5]:
            rbi_lower = rbi['text'].lower()
            matches = sum(1 for kw in policy_keywords if kw in clause_lower or kw in rbi_lower)
            similarity = 0.15 if matches >= 2 else (0.10 if matches == 1 else 0.05)
            
            if similarity > 0:
                best_matches.append((rbi, similarity))
        
        best_matches.sort(key=lambda x: x[1], reverse=True)
        for rbi, sim in best_matches[:3]:
            links.append({
                'policyid': clause['id'],
                'policytext': clause['text'],
                'rbiid': rbi['id'],
                'rbitext': rbi['text'],
                'similarity': sim
            })
    
    return links
