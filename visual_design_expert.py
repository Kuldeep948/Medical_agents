import os
import json
import asyncio
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from PIL import Image

SYSTEM_PROMPT = """
ROLE: You are a Visual Design Expert for pharmaceutical marketing materials in India. Analyze images for medical accuracy, cultural fit, and regulatory compliance. Output JSON only.
EVALUATION DIMENSIONS & WEIGHTS:
•	medical_accuracy (25%): Anatomical correctness, MOA accuracy, data visualization integrity
•	visual_text_alignment (20%): Image supports text message, emotional tone match
•	cultural_sensitivity (20%): Indian demographics, settings, family structures, attire
•	brand_consistency (15%): Color palette, image style, logo usage, visual hierarchy
•	regulatory_compliance (10%): No misleading graphs, proper scales, fair balance
•	accessibility (10%): Color contrast, readability, complexity appropriate for audience
SCORING FORMULA:
overall_score = (MA×0.25) + (VTA×0.20) + (CS×0.20) + (BC×0.15) + (RC×0.10) + (ACC×0.10)
Round to nearest integer. All dimension scores: 0-100.
SEVERITY RULES (per image issue):
•	CRITICAL: Medical inaccuracy causing potential harm OR regulatory violation (misleading graph) OR score <40
•	MAJOR: Cultural mismatch (Western imagery for Indian market) OR visual contradicts text OR score 40-69
•	MINOR: Quality improvements (slightly low resolution, minor style inconsistency) OR score 70-84
INDIAN MARKET SPECIFICS - MUST CHECK:
•	Demographics: Indian skin tones (light brown to dark), Indian facial features, black hair
•	Family: Multi-generational (grandparents common), joint family context, 3+ members typical
•	Settings: Indian homes (concrete walls, Indian kitchens with gas stove/pressure cooker), Indian hospitals/clinics (crowded OPD, smaller rooms)
•	Attire: Sarees, salwar kameez, kurta for men (when contextual), white coats for doctors
•	RED FLAGS: Caucasian/Western-only models, American suburban homes, US-style hospitals, blonde hair, Christmas/Western cultural symbols
PURPOSE-BASED WEIGHT ADJUSTMENTS:
Apply these weight modifications based on purpose provided in context:
•	patient_engagement: CS→30%, ACC→15%, MA→15%, VTA→20%, BC→10%, RC→10%
•	hcp_detailing: MA→35%, RC→15%, VTA→20%, CS→10%, BC→10%, ACC→10%
•	scientific_education: MA→35%, VTA→25%, RC→15%, BC→10%, CS→10%, ACC→5%
•	brand_awareness: BC→30%, VTA→25%, CS→20%, MA→10%, RC→10%, ACC→5%
•	digital_campaign: ACC→25%, VTA→25%, CS→20%, BC→15%, MA→10%, RC→5%
•	regulatory_submission: RC→30%, MA→30%, VTA→20%, BC→10%, CS→5%, ACC→5%
For other purposes or multiple purposes: use default weights.
OUTPUT FORMAT (JSON only, no markdown, no explanation):
{   "overall_score": 72,   "images_analyzed": 5,   "dimensions": {     "medical_accuracy": 85,     "visual_text_alignment": 70,     "cultural_sensitivity": 45,     "brand_consistency": 80,     "regulatory_compliance": 90,     "accessibility": 75   },   "issues": [     {       "id": "VIS-001",       "location": "Page 2, center",       "severity": "MAJOR",       "category": "cultural_sensitivity",       "finding": "Caucasian family in Western kitchen setting",       "fix": "Replace with Indian multi-generational family in Indian home setting",       "alternatives": ["Indian family with grandparents", "Indian doctor-patient scene"]     }   ],   "strengths": ["Clear data charts", "Consistent brand colors"],   "priority_fixes": ["Replace Western family image (Page 2)"] }
RULES:
1.	Output ONLY valid JSON. No markdown, no backticks, no explanations.
2.	Every issue MUST have a specific fix and at least one alternative.
3.	If no images found, return: {"overall_score": 100, "images_analyzed": 0, "issues": [], "note": "No images in collateral"}
4.	Maximum 3 items in priority_fixes (most impactful first).
5.	Location format: "Page X, position" (e.g., "Page 3, top-right").
6.	You are ADVISORY only. Include disclaimer awareness in analysis.
"""


class VisualDesignExpert:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash',
                                           system_instruction=SYSTEM_PROMPT)

    async def analyze(self, images: List[Image.Image], text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes images using the Gemini Vision API.
        
        Args:
            images: List of PIL Image objects with position metadata.
            text: First 500 chars of text for alignment check.
            context: Context dictionary with collateral metadata.
        """
        if not images:
            return {
                "overall_score": 100,
                "images_analyzed": 0,
                "issues": [],
                "dimensions": {
                    "medical_accuracy": 100,
                    "visual_text_alignment": 100,
                    "cultural_sensitivity": 100,
                    "brand_consistency": 100,
                    "regulatory_compliance": 100,
                    "accessibility": 100
                },
                "strengths": [],
                "priority_fixes": [],
                "note": "No images in collateral"
            }
        
        prompt = self._construct_prompt(text, context)
        
        try:
            # Prepare content for Gemini - prompt first, then images
            content = [prompt] + images[:10]  # Max 10 images
            
            response = await self.model.generate_content_async(content)
            
            # Clean up response text
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text)
            
            # Validate response
            self.validate_response(data)
            
            # Recalculate score server-side
            purpose = context.get('purposes', '').split(',')[0].strip().lower().replace(' ', '_')
            calculated_score = self.calculate_score(data['dimensions'], purpose)
            
            # If deviation > 5 points, use server-calculated score
            if abs(data['overall_score'] - calculated_score) > 5:
                data['overall_score'] = calculated_score
            
            data['images_analyzed'] = min(len(images), 10)
            
            return data
            
        except Exception as e:
            return {
                "error": str(e),
                "overall_score": 0,
                "images_analyzed": 0,
                "dimensions": {},
                "issues": [],
                "strengths": [],
                "priority_fixes": []
            }

    def _construct_prompt(self, text: str, context: Dict[str, Any]) -> str:
        text_preview = text[:500] if len(text) > 500 else text
        return f"""Analyze these pharmaceutical marketing images.

CONTEXT:
Collateral Type: {context.get('collateral_type', 'Unknown')}
Target Audience: {context.get('target_audience', 'Unknown')}
Purpose: {context.get('purposes', 'Unknown')}
Brand: {context.get('brand_name', 'Unknown')}
Therapy Area: {context.get('therapy_area', 'Unknown')}

TEXT CONTENT FOR ALIGNMENT CHECK:
{text_preview}

IMAGES: [attached images with page/position labels]

Provide analysis in JSON format."""

    def validate_response(self, data: Dict[str, Any]) -> bool:
        """Validates the structure and content of the API response."""
        try:
            assert 0 <= data['overall_score'] <= 100
            assert data.get('images_analyzed', 0) >= 0
            
            for dim in ['medical_accuracy', 'visual_text_alignment', 'cultural_sensitivity',
                       'brand_consistency', 'regulatory_compliance', 'accessibility']:
                assert 0 <= data['dimensions'][dim] <= 100
            
            for issue in data.get('issues', []):
                assert issue['severity'] in ['CRITICAL', 'MAJOR', 'MINOR']
                assert len(issue.get('fix', '')) > 0
            
            assert len(data.get('priority_fixes', [])) <= 3
            return True
        except AssertionError as e:
            print(f"Validation warning: {e}")
            return False

    def calculate_score(self, dimensions: Dict[str, float], purpose: Optional[str] = None) -> int:
        """Calculates the overall score based on dimensions and purpose weights."""
        weights = {
            'medical_accuracy': 0.25,
            'visual_text_alignment': 0.20,
            'cultural_sensitivity': 0.20,
            'brand_consistency': 0.15,
            'regulatory_compliance': 0.10,
            'accessibility': 0.10
        }
        
        PURPOSE_WEIGHTS = {
            'patient_engagement': {
                'cultural_sensitivity': 0.30, 'accessibility': 0.15,
                'medical_accuracy': 0.15, 'visual_text_alignment': 0.20,
                'brand_consistency': 0.10, 'regulatory_compliance': 0.10
            },
            'hcp_detailing': {
                'medical_accuracy': 0.35, 'regulatory_compliance': 0.15,
                'visual_text_alignment': 0.20, 'cultural_sensitivity': 0.10,
                'brand_consistency': 0.10, 'accessibility': 0.10
            },
            'scientific_education': {
                'medical_accuracy': 0.35, 'visual_text_alignment': 0.25,
                'regulatory_compliance': 0.15, 'brand_consistency': 0.10,
                'cultural_sensitivity': 0.10, 'accessibility': 0.05
            },
            'brand_awareness': {
                'brand_consistency': 0.30, 'visual_text_alignment': 0.25,
                'cultural_sensitivity': 0.20, 'medical_accuracy': 0.10,
                'regulatory_compliance': 0.10, 'accessibility': 0.05
            },
            'digital_campaign': {
                'accessibility': 0.25, 'visual_text_alignment': 0.25,
                'cultural_sensitivity': 0.20, 'brand_consistency': 0.15,
                'medical_accuracy': 0.10, 'regulatory_compliance': 0.05
            },
            'regulatory_submission': {
                'regulatory_compliance': 0.30, 'medical_accuracy': 0.30,
                'visual_text_alignment': 0.20, 'brand_consistency': 0.10,
                'cultural_sensitivity': 0.05, 'accessibility': 0.05
            }
        }
        
        if purpose and purpose in PURPOSE_WEIGHTS:
            weights = PURPOSE_WEIGHTS[purpose]
        
        score = sum(dimensions[k] * weights[k] for k in weights)
        return round(score)
