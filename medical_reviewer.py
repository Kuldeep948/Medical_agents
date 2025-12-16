"""
Medical Reviewer Agent
Validates scientific/medical claims against backup documentation and PubMed.
"""

import os
import json
import asyncio
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from pubmed_service import PubMedService

SYSTEM_PROMPT = """
ROLE: You are a Medical Reviewer for pharmaceutical marketing materials in India. Extract and validate ALL scientific/medical claims against provided backup documentation and indicate which claims need PubMed verification. You focus ONLY on medical/scientific accuracy—regulatory compliance is handled by Compliance Officer. Output JSON only.
SCOPE:
•	IN SCOPE: Scientific claims, efficacy data, safety statements, statistical claims, mechanism claims, comparative claims, dosing claims, patient population claims
•	OUT OF SCOPE: Regulatory compliance (→ Compliance Officer), messaging effectiveness (→ Copywriting Expert), visual design (→ Visual Design Expert), document structure (→ Best Practices Coach)
CLAIM TYPES TO EXTRACT:
1.	EFFICACY_CLAIM: Statements about drug effectiveness (e.g., "47% reduction in HbA1c", "significant improvement in symptoms")
2.	SAFETY_CLAIM: Statements about safety profile (e.g., "well-tolerated", "minimal side effects", "safe in renal impairment")
3.	COMPARATIVE_CLAIM: Comparisons to other treatments (e.g., "superior to", "better than", "faster onset than")
4.	MECHANISM_CLAIM: MOA statements (e.g., "inhibits DPP-4", "blocks calcium channels")
5.	STATISTICAL_CLAIM: P-values, confidence intervals, percentages (e.g., "p<0.001", "95% CI", "NNT of 8")
6.	DOSING_CLAIM: Dosage statements (e.g., "once daily dosing", "start with 5mg")
7.	POPULATION_CLAIM: Patient population statements (e.g., "suitable for elderly", "safe in pregnancy", "for all diabetic patients")
8.	ONSET_DURATION_CLAIM: Time-related claims (e.g., "works within 30 minutes", "24-hour protection")
VALIDATION HIERARCHY (in order of priority):
1.	BACKUP_DOCUMENTS (PRIMARY): User-uploaded scientific articles, clinical trial reports, prescribing information. If claim found here with matching data → SUBSTANTIATED_BACKUP
2.	PUBMED_SEARCH (SECONDARY): For claims not found in backup docs, flag for PubMed verification by backend. Return search_query suggestion.
3.	PRESCRIBING INFORMATION: If backup includes approved PI/SmPC, dosing and indication claims should match exactly.
EVIDENCE STATUS CLASSIFICATIONS:
•	SUBSTANTIATED_BACKUP: Claim directly supported by uploaded backup document with matching data
•	SUBSTANTIATED_PUBMED: Claim verified via PubMed search (backend fills this after search)
•	PARTIALLY_SUBSTANTIATED: Claim has some support but data doesn't fully match (e.g., claim says 47%, backup says 45%)
•	NEEDS_PUBMED_CHECK: Not found in backup, needs PubMed verification—provide search_query
•	UNSUBSTANTIATED: No evidence found in backup AND PubMed search returned no matches
•	CONTRADICTED: Backup document shows DIFFERENT data than claimed (e.g., claim says 67%, backup says 45%)
•	OVERSTATED: Claim exaggerates evidence (e.g., p=0.08 claimed as "significant")
SEVERITY RULES:
•	CRITICAL: 
• Unsubstantiated efficacy claim (could mislead prescribing)
• Contradicted claim (data doesn't match backup)
• Comparative claim without head-to-head trial data
• Statistical misrepresentation (p=0.08 shown as significant)
• Safety claim contradicted by evidence
• Claim beyond approved indication
•	MAJOR: 
• Partially substantiated (numbers don't quite match)
• Outdated citation (>5 years for fast-evolving therapy areas)
• Overgeneralization ("suitable for all patients" when label has restrictions)
• Missing citation for specific data point
• Needs PubMed check (claim not in backup)
•	MINOR: 
• Imprecise language ("significant" without specifying statistical/clinical)
• Minor rounding differences (<2%)
• Citation format issues
SPECIFIC ISSUE TYPES TO FLAG:
•	UNSUBSTANTIATED_CLAIM: Claim has no supporting evidence
•	DATA_MISMATCH: Claim number differs from source (e.g., says 67%, source says 54%)
•	COMPARATIVE_WITHOUT_H2H: Comparative claim without head-to-head trial data
•	STATISTICAL_MISREPRESENTATION: P-value or CI misinterpreted or misrepresented
•	OVERGENERALIZATION: Claim broader than evidence supports
•	OUTDATED_EVIDENCE: Citation >5 years old for evolving field, or superseded by newer data
•	CHERRY_PICKED_DATA: Using favorable subgroup when overall result different
•	BEYOND_INDICATION: Claim for patient population not in approved label
•	MISSING_CONTEXT: Efficacy shown without mentioning important limitations
•	MISSING_CITATION: Specific data point without reference
INDIAN MARKET CONSIDERATIONS:
•	Indian Studies Preferred: Note if data is from Western populations only; Indian population data is stronger evidence for Indian market
•	ICMR Guidelines: Claims should align with ICMR treatment guidelines where applicable
•	Indian Journals: Indian Journal of Medical Research, Journal of Association of Physicians of India carry weight
•	Dosing Differences: Some drugs have different approved doses in India vs US/EU—verify against Indian PI
OUTPUT FORMAT (JSON only, no markdown):
{   "overall_score": 65,   "summary": {     "total_claims": 12,     "substantiated_backup": 5,     "substantiated_pubmed": 2,     "needs_pubmed_check": 2,     "unsubstantiated": 2,     "contradicted": 1   },   "claims": [     {       "id": "CLM-001",       "claim_text": "47% reduction in HbA1c compared to placebo",       "claim_type": "EFFICACY_CLAIM",       "location": "Slide 5, bullet 2",       "evidence_status": "SUBSTANTIATED_BACKUP",       "severity": null,       "backup_reference": {         "document": "Phase3_Trial_Results.pdf",         "page": 12,         "matching_text": "HbA1c reduction of 47.2% (p<0.001)",         "confidence": 0.95       },       "issues": []     }   ],   "pubmed_queries_needed": [],   "backup_documents_reviewed": [],   "recommendations": {     "immediate_actions": [],     "citations_needed": []   } }
RULES:
1.	Output ONLY valid JSON. No markdown, no backticks, no explanations.
2.	Extract ALL claims—do not skip any medical/scientific statements.
3.	For each claim, check ALL provided backup documents before marking as needs_pubmed_check.
4.	Comparative claims (better than, superior to, vs) ALWAYS need H2H trial data—flag as CRITICAL if missing.
5.	p>0.05 is NOT statistically significant—flag any claim stating otherwise.
6.	For NEEDS_PUBMED_CHECK status, always provide a pubmed_search_query.
7.	Include confidence score (0.0-1.0) for backup_reference matches.
8.	Every issue MUST have recommendation and suggested_revision.
9.	You are ADVISORY only. Human medical reviewer makes final decisions.
"""


class MedicalReviewer:
    def __init__(self, api_key: str, pubmed_api_key: Optional[str] = None):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.pubmed_service = PubMedService(api_key=pubmed_api_key)

    async def analyze(self, collateral_text: str, backup_docs: List[Dict[str, str]], 
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze collateral for medical accuracy.
        
        Args:
            collateral_text: Full text of the marketing collateral.
            backup_docs: List of dicts with 'filename' and 'text' keys.
            metadata: Dict with brand_name, generic_name, therapy_area, etc.
        """
        # Validate inputs
        if not isinstance(backup_docs, list):
            backup_docs = []
        
        # Ensure each backup_doc is a dict
        validated_backup_docs = []
        for doc in backup_docs:
            if isinstance(doc, dict):
                validated_backup_docs.append(doc)
            elif isinstance(doc, str):
                validated_backup_docs.append({"filename": "Unknown", "text": doc})
        
        if not isinstance(metadata, dict):
            metadata = {}
        
        prompt = self._construct_prompt(collateral_text, validated_backup_docs, metadata)
        
        try:
            response = await self.model.generate_content_async(prompt)
            
            # Clean up response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate response structure
            self.validate_response(result)
            
            # Process PubMed queries for claims that need verification
            await self._process_pubmed_queries(result)
            
            # Recalculate overall score
            result["overall_score"] = self.calculate_score(result.get("claims", []))
            
            return result
            
        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parsing failed: {str(e)}",
                "raw_response": response_text[:500] if 'response_text' in dir() else "No response",
                "overall_score": 0,
                "summary": {"total_claims": 0},
                "claims": [],
                "pubmed_queries_needed": [],
                "backup_documents_reviewed": [],
                "recommendations": {"immediate_actions": [], "citations_needed": []}
            }
        except Exception as e:
            return {
                "error": str(e),
                "overall_score": 0,
                "summary": {"total_claims": 0},
                "claims": [],
                "pubmed_queries_needed": [],
                "backup_documents_reviewed": [],
                "recommendations": {"immediate_actions": [], "citations_needed": []}
            }

    def _construct_prompt(self, collateral_text: str, backup_docs: List[Dict[str, str]], 
                          metadata: Dict[str, Any]) -> str:
        backup_section = ""
        for doc in backup_docs:
            backup_section += f"""
--- DOCUMENT: {doc.get('filename', 'Unknown')} ---
{doc.get('text', '')}
--- END DOCUMENT ---
"""
        
        return f"""{SYSTEM_PROMPT}

Review this pharmaceutical marketing collateral for medical accuracy.

COLLATERAL TEXT:
{collateral_text}

BACKUP DOCUMENTS PROVIDED:
{backup_section if backup_section else "No backup documents provided."}

METADATA:
Brand Name: {metadata.get('brand_name', 'Unknown')}
Generic Name: {metadata.get('generic_name', 'Unknown')}
Therapy Area: {metadata.get('therapy_area', 'Unknown')}
Approved Indications: {metadata.get('indications', 'Unknown')}
Target Audience: {metadata.get('target_audience', 'Unknown')}

Analyze ALL scientific/medical claims and validate against backup documents."""

    async def _process_pubmed_queries(self, result: Dict[str, Any]) -> None:
        """Process claims that need PubMed verification."""
        
        pubmed_queries = result.get("pubmed_queries_needed", [])
        
        for query_info in pubmed_queries:
            claim_id = query_info.get("claim_id")
            query = query_info.get("query", "")
            
            if not query:
                continue
            
            # Find the corresponding claim
            claim = None
            for c in result.get("claims", []):
                if c.get("id") == claim_id:
                    claim = c
                    break
            
            if not claim:
                continue
            
            # Search PubMed
            articles = await self.pubmed_service.search(query, max_results=5, years=10)
            
            if articles:
                # Found evidence - update claim
                best_article = articles[0]
                claim["evidence_status"] = "SUBSTANTIATED_PUBMED"
                claim["pubmed_reference"] = {
                    "pmid": best_article.get("pmid"),
                    "title": best_article.get("title"),
                    "authors": best_article.get("authors", []),
                    "journal": best_article.get("journal"),
                    "year": best_article.get("year"),
                    "confidence": self.pubmed_service.calculate_relevance_score(query, best_article)
                }
                # Reduce severity if evidence found
                if claim.get("severity") == "CRITICAL":
                    claim["severity"] = "MAJOR"
                elif claim.get("severity") == "MAJOR":
                    claim["severity"] = "MINOR"
            else:
                # No evidence found
                claim["evidence_status"] = "UNSUBSTANTIATED"
                claim["severity"] = "CRITICAL"

    def validate_response(self, data: Dict[str, Any]) -> bool:
        """Validate AI response structure."""
        
        valid_statuses = [
            "SUBSTANTIATED_BACKUP", "SUBSTANTIATED_PUBMED",
            "PARTIALLY_SUBSTANTIATED", "NEEDS_PUBMED_CHECK",
            "UNSUBSTANTIATED", "CONTRADICTED", "OVERSTATED"
        ]
        valid_severities = ["CRITICAL", "MAJOR", "MINOR", None]
        valid_claim_types = [
            "EFFICACY_CLAIM", "SAFETY_CLAIM", "COMPARATIVE_CLAIM",
            "MECHANISM_CLAIM", "STATISTICAL_CLAIM", "DOSING_CLAIM",
            "POPULATION_CLAIM", "ONSET_DURATION_CLAIM"
        ]
        
        try:
            assert "overall_score" in data
            assert 0 <= data["overall_score"] <= 100
            assert "claims" in data
            
            for claim in data.get("claims", []):
                assert "id" in claim
                assert "claim_text" in claim
                assert "claim_type" in claim
                assert claim["claim_type"] in valid_claim_types
                assert "evidence_status" in claim
                assert claim["evidence_status"] in valid_statuses
                assert claim.get("severity") in valid_severities
            
            return True
        except AssertionError as e:
            print(f"Validation warning: {e}")
            return False

    def calculate_score(self, claims: List[Dict[str, Any]]) -> int:
        """Calculate overall medical accuracy score."""
        
        if not claims:
            return 100  # No claims = nothing to validate
        
        total_claims = len(claims)
        
        # Count by status
        status_counts = {
            "SUBSTANTIATED_BACKUP": 0,
            "SUBSTANTIATED_PUBMED": 0,
            "PARTIALLY_SUBSTANTIATED": 0,
            "NEEDS_PUBMED_CHECK": 0,
            "UNSUBSTANTIATED": 0,
            "CONTRADICTED": 0,
            "OVERSTATED": 0
        }
        
        severity_counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0}
        
        for claim in claims:
            status = claim.get("evidence_status", "UNSUBSTANTIATED")
            if status in status_counts:
                status_counts[status] += 1
            
            severity = claim.get("severity")
            if severity and severity in severity_counts:
                severity_counts[severity] += 1
        
        # Base score from substantiation rate
        substantiated = (
            status_counts["SUBSTANTIATED_BACKUP"] + 
            status_counts["SUBSTANTIATED_PUBMED"]
        )
        partially = status_counts["PARTIALLY_SUBSTANTIATED"]
        
        base_score = ((substantiated * 1.0) + (partially * 0.5)) / total_claims * 100
        
        # Deductions for issues
        deductions = (
            severity_counts["CRITICAL"] * 15 +
            severity_counts["MAJOR"] * 8 +
            severity_counts["MINOR"] * 3
        )
        
        final_score = max(0, min(100, base_score - deductions))
        
        return round(final_score)
