import os
import json
import asyncio
import textstat
import re
import google.generativeai as genai
from typing import Dict, Any, List, Optional

SYSTEM_PROMPT = """
ROLE: You are a Pharmaceutical Copywriting Expert for Indian markets. Evaluate text for clarity, audience fit, and persuasion. Provide specific rewrites. Output JSON only.
SCOPE: Focus on messaging quality. Do NOT flag regulatory violations (prohibited terms, missing disclaimers)—that's handled by Compliance Officer.
EVALUATION DIMENSIONS & WEIGHTS:
•	message_clarity (30%): Core message identifiable in 5 seconds, logical flow, no ambiguity
•	audience_alignment (25%): Language complexity matches target audience (see grade levels below)
•	persuasion_effectiveness (25%): Headlines differentiate, CTAs are specific, benefits are tangible
•	scientific_support (20%): Claims have data backing, statistics presented clearly (not accuracy—just presentation)
SCORING FORMULA:
overall_score = (MC×0.30) + (AA×0.25) + (PE×0.25) + (SS×0.20)
Round to nearest integer. All dimension scores: 0-100.
SEVERITY RULES:
•	CRITICAL: No identifiable core message OR completely wrong audience level OR score <40
•	MAJOR: Weak/generic headline OR missing CTA OR audience mismatch OR score 40-69
•	MINOR: Wordiness, passive voice, style improvements OR score 70-84
AUDIENCE LANGUAGE TARGETS:
•	Patients/Caregivers: Grade 6-8, sentences <20 words, explain ALL medical terms, empathetic tone
•	General Practitioners: Grade 10-12, clinical terms OK, efficient/concise, data-driven
•	Specialists: Grade 12-14, technical depth expected, MOA details acceptable, evidence hierarchy matters
•	Pharmacists: Grade 12-14, focus on dosing, interactions, formulation details
•	Payers/Administrators: Grade 12-14, outcomes-focused, cost-effectiveness language, HEOR terminology
INDIAN MARKET LANGUAGE CONSIDERATIONS:
•	Indian English conventions: "Kindly" is acceptable, "Do the needful" avoid, British spellings preferred (colour, organisation)
•	Patient materials: Simple English, avoid idioms, consider low-literacy contexts, family-inclusive messaging ("Discuss with your family and doctor")
•	HCP materials: Indian clinical practice context (busy OPDs, 2-3 min consultations), reference Indian studies/guidelines where relevant
•	Currency/units: Use ₹ for costs, metric units, Indian number system (lakhs/crores) for large numbers if patient-facing
•	Avoid: US-centric references, American spellings, Western idioms ("hit it out of the park"), culturally inappropriate metaphors
HEADLINE EXAMPLES (What Good vs Bad Looks Like):
❌ BAD: "An Effective Treatment Option for Diabetes"
   Problems: Generic (every drug claims this), no differentiation, no data, forgettable
✓ GOOD: "1.8% HbA1c Reduction in 12 Weeks—Once-Daily, With or Without Food"
   Why: Specific benefit (1.8%), timeframe (12 weeks), convenience (once-daily), flexibility (with/without food)
❌ BAD: "Helping Patients Live Better"
   Problems: Vague, emotional without substance, could apply to any drug
✓ GOOD: "47% Fewer Hospitalisations—Give Your Patients More Time at Home"
   Why: Specific outcome (47%), tangible benefit (fewer hospitalisations), emotional hook (time at home)
CTA EXAMPLES:
❌ BAD (HCP): "Learn More" | "Consider Prescribing"
✓ GOOD (HCP): "Start Your Next 5 Uncontrolled Patients—See Results in 4 Weeks"
❌ BAD (Patient): "Ask Your Doctor" (too vague)
✓ GOOD (Patient): "Ask Your Doctor if Once-Daily [Brand] is Right for You"
PURPOSE-BASED WEIGHT ADJUSTMENTS:
•	patient_engagement: AA→35%, MC→25%, PE→20%, SS→20%
•	hcp_detailing: SS→35%, MC→25%, PE→25%, AA→15%
•	scientific_education: SS→40%, MC→30%, AA→20%, PE→10%
•	brand_awareness: PE→40%, MC→30%, AA→20%, SS→10%
•	digital_campaign: PE→35%, MC→30%, AA→25%, SS→10%
For other/multiple purposes: use default weights.
OUTPUT FORMAT (JSON only, no markdown):
{   "overall_score": 62,   "dimensions": {     "message_clarity": 70,     "audience_alignment": 55,     "persuasion_effectiveness": 50,     "scientific_support": 75   },   "issues": [     {       "id": "COPY-001",       "component": "headline",       "location": "Slide 1",       "severity": "MAJOR",       "current_text": "An Effective Treatment Option",       "problem": "Generic, no differentiation, no data",       "rewrite": "1.8% HbA1c Drop in 12 Weeks—Once Daily",       "rationale": "Specific benefit + timeframe + convenience"     },     {       "id": "COPY-002",       "component": "body",       "location": "Slide 3, para 2",       "severity": "MAJOR",       "current_text": "The pharmacokinetic profile demonstrates superior bioavailability",       "problem": "Too technical for patient audience (Grade 14+)",       "rewrite": "The medicine is absorbed well by your body",       "rationale": "Simplified to Grade 6 for patient comprehension"     }   ],   "strengths": ["Good use of bullet points", "Clear section headers"],   "priority_rewrites": ["Headline—add specific data", "Simplify para 2 for patients"] }
RULES:
1.	Output ONLY valid JSON. No markdown, no backticks, no explanations.
2.	Every issue MUST have: current_text, problem, rewrite (actual text, not suggestion), rationale.
3.	Do NOT flag regulatory terms (cure, guaranteed, etc.)—Compliance Officer handles that.
4.	Maximum 3 items in priority_rewrites (highest impact first).
5.	Location format: "Slide X" or "Page X, para Y" or "Section heading".
6.	You are ADVISORY only—recommendations need human review.
"""

class CopywritingExpert:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def analyze(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the text using the Gemini API and returns the structured evaluation.
        """
        prompt = self._construct_prompt(text, context)
        
        try:
            response = await self.model.generate_content_async(prompt)
            # Clean up response text if it contains markdown code blocks
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text)
            
            # Post-processing validations and calculations
            self.validate_response(data)
            
            # Recalculate score server-side to ensure accuracy
            purpose = context.get('purposes', '').split(',')[0].strip().lower().replace(' ', '_')
            data['overall_score'] = self.calculate_score(data['dimensions'], purpose)
            
            # Add server-side readability analysis
            data['readability_analysis'] = self.analyze_readability(text, context.get('target_audience', ''))
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "overall_score": 0,
                "dimensions": {},
                "issues": [],
                "strengths": [],
                "priority_rewrites": []
            }

    def _construct_prompt(self, text: str, context: Dict[str, Any]) -> str:
        return f"{SYSTEM_PROMPT}\n\nAnalyze this pharmaceutical marketing copy.\n\nCONTEXT:\nCollateral Type: {context.get('collateral_type', 'Unknown')}\nTarget Audience: {context.get('target_audience', 'Unknown')}\nPurpose: {context.get('purposes', 'Unknown')}\nBrand: {context.get('brand_name', 'Unknown')}\nTherapy Area: {context.get('therapy_area', 'Unknown')}\n\nTEXT CONTENT:\n{text}\n\nProvide analysis with specific rewrites in JSON format."

    def validate_response(self, data: Dict[str, Any]) -> bool:
        """Validates the structure and content of the API response."""
        try:
            assert 0 <= data['overall_score'] <= 100
            for dim in ['message_clarity', 'audience_alignment', 'persuasion_effectiveness', 'scientific_support']:
                assert 0 <= data['dimensions'][dim] <= 100
            
            for issue in data.get('issues', []):
                assert issue['severity'] in ['CRITICAL', 'MAJOR', 'MINOR']
                assert len(issue.get('rewrite', '')) > 0
                assert len(issue.get('current_text', '')) > 0
                assert len(issue.get('problem', '')) > 0
            
            assert len(data.get('priority_rewrites', [])) <= 3
            return True
        except AssertionError as e:
            # In a real system, we might log this or raise a specific error
            print(f"Validation warning: {e}")
            return False

    def calculate_score(self, dimensions: Dict[str, float], purpose: Optional[str] = None) -> int:
        """Calculates the overall score based on dimensions and purpose weights."""
        weights = {
            'message_clarity': 0.30,
            'audience_alignment': 0.25,
            'persuasion_effectiveness': 0.25,
            'scientific_support': 0.20
        }
        
        PURPOSE_WEIGHTS = {
            'patient_engagement': {'audience_alignment': 0.35, 'message_clarity': 0.25,
                                  'persuasion_effectiveness': 0.20, 'scientific_support': 0.20},
            'hcp_detailing': {'scientific_support': 0.35, 'message_clarity': 0.25,
                             'persuasion_effectiveness': 0.25, 'audience_alignment': 0.15},
            'scientific_education': {'scientific_support': 0.40, 'message_clarity': 0.30,
                                    'audience_alignment': 0.20, 'persuasion_effectiveness': 0.10},
            'brand_awareness': {'persuasion_effectiveness': 0.40, 'message_clarity': 0.30,
                               'audience_alignment': 0.20, 'scientific_support': 0.10},
            'digital_campaign': {'persuasion_effectiveness': 0.35, 'message_clarity': 0.30,
                                'audience_alignment': 0.25, 'scientific_support': 0.10}
        }
        
        if purpose and purpose in PURPOSE_WEIGHTS:
            weights = PURPOSE_WEIGHTS[purpose]
            
        score = sum(dimensions[k] * weights[k] for k in weights)
        return round(score)

    def analyze_readability(self, text: str, target_audience: str) -> Dict[str, Any]:
        """Analyzes readability using textstat."""
        # Calculate grade level
        grade = textstat.flesch_kincaid_grade(text)
        
        # Sentence stats
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        avg_sentence_len = len(words) / max(len(sentences), 1)
        
        # Target grade by audience
        TARGETS = {
            'patients': (6, 8),
            'caregivers': (6, 8),
            'general_practitioners': (10, 12),
            'specialists': (12, 14),
            'cardiologists': (12, 14),
            'diabetologists': (12, 14),
            'pharmacists': (12, 14),
            'nurses': (10, 12),
            'payers': (12, 14)
        }
        
        normalized_audience = target_audience.lower().replace(' ', '_')
        # Try to find a partial match if full match fails (e.g. "specialist" in "medical specialist")
        target_min, target_max = (10, 12) # Default
        for key, val in TARGETS.items():
            if key in normalized_audience:
                target_min, target_max = val
                break
        
        return {
            'grade_level': round(grade, 1),
            'avg_sentence_length': round(avg_sentence_len, 1),
            'target_grade_range': f"{target_min}-{target_max}",
            'is_appropriate': target_min <= grade <= target_max + 2,
            'recommendation': None if target_min <= grade <= target_max + 2 else (
                f"Simplify to Grade {target_max}" if grade > target_max + 2
                else f"Can increase complexity to Grade {target_min}"
            )
        }
