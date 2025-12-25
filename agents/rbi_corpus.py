import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def fetch_latest_rbi_circulars(topics: List[str] = None) -> List[Dict]:
    """YOUR ORIGINAL SCRAPING LOGIC - 100% PRESERVED"""
    url = "https://www.rbi.org.in/Scripts/BS_ViewMasCirculardetails.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        circulars = []
        rows = soup.select('table tr')
        for row in rows[1:15]:  # YOUR ORIGINAL LOGIC
            cells = row.find_all('td')
            if len(cells) >= 3:
                title_cell = cells[1]
                title = title_cell.text.strip()
                link_elem = title_cell.find('a')
                link = 'https://www.rbi.org.in' + link_elem['href'] if link_elem else ''
                
                if any(topic in title.lower() for topic in topics or ['kyc', 'aml', 'compliance', 'customer', 'due diligence']):
                    circulars.append({
                        "id": title[:20].replace(' ', '_').lower(),
                        "title": title,
                        "url": link,
                        "text": f"RBI Master Circular: {title[:200]}..."  
                    })
        return circulars[:8]
    except Exception as e:
        print(f"RBI scrape failed: {e}")

def get_all_rbi_sections() -> List[Dict]:
    """YOUR ORIGINAL RULES"""
    
    original_rules = [
        {
            "id": "kyc_master_2024", 
            "title": "Master Direction - KYC 2024", 
            "text": "Regulated entities (REs) shall perform full KYC verification using official documents before onboarding customers. Self-declaration is NOT sufficient for account opening or high-value transactions. Documentary evidence mandatory for identity and address proof."
        },
        {
            "id": "aml_cdd_2025", 
            "title": "AML/CFT Customer Due Diligence 2025", 
            "text": "Banks must implement Customer Due Diligence (CDD) for all accounts. Simplified CDD allowed only for explicitly listed low-risk categories. Enhanced Due Diligence (EDD) required for high-risk customers."
        },
        {
            "id": "str_reporting_2024", 
            "title": "STR Reporting Requirements 2024", 
            "text": "Suspicious Transaction Reports (STRs) must be filed within 7 days of detection with FIU-IND. No tipping off customers about STR filing."
        },
        {"id": "bo_24months_2025", "title": "BO Refresh 2025", "text": "Beneficial Ownership refresh every 24 MONTHS MAXIMUM. All beneficiaries identified."},
        {"id": "records_10yrs_2025", "title": "Records Retention 2025", "text": "Transaction records retained 10 YEARS MINIMUM."},
        {"id": "sanctions_all_2025", "title": "Sanctions Lists 2025", "text": "Screening ALL lists: UNSC, OFAC, EU, UK OFSI, GoI MANDATORY. No optional lists."},
        {"id": "swift_full_2025", "title": "SWIFT Rules 2025", "text": "Full verification ALL SWIFT transfers - NO amount thresholds."},
        {"id": "pep_official_2025", "title": "PEP Screening 2025", "text": "PEP screening using OFFICIAL government lists - continuous monitoring."},
        {"id": "str_7days_2025", "title": "STR 7 Days 2025", "text": "STRs filed within 7 CALENDAR DAYS to FIU-IND. NO approval delays."},
        {"id": "kyc_refresh_2025", "title": "KYC Refresh 2025", "text": "KYC refresh every 24 MONTHS MAXIMUM for all customers."},
        {"id": "edd_5cr_2025", "title": "EDD High-Value 2025", "text": "Enhanced Due Diligence MANDATORY for transactions >5 crores."},
        {"id": "monitoring_realtime_2025", "title": "Monitoring 2025", "text": "Real-time transaction monitoring REQUIRED. No next-business-day delays."}
    ]
    
    print(f"✅ RBI Corpus: {len(original_rules)} TOTAL rules")
    return original_rules

print("✅ RBI Corpus loaded - Your original rules preserved!")
