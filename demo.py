import asyncio
import os
import json
from dotenv import load_dotenv
from PIL import Image
from copywriting_expert import CopywritingExpert
from visual_design_expert import VisualDesignExpert
from medical_reviewer import MedicalReviewer


async def demo_copywriting_expert(api_key: str):
    """Demonstrates the Copywriting Expert."""
    print("=" * 60)
    print("COPYWRITING EXPERT DEMO")
    print("=" * 60)
    
    expert = CopywritingExpert(api_key=api_key)
    
    sample_text = """
    We present a new effective treatment for diabetes management. 
    This drug helps patients live better lives by reducing their symptoms. 
    It is very good and has high bioavailability as shown in pharmacokinetic studies.
    Kindly consider prescribing it to your patients for better outcomes.
    The mechanism of action involves inhibition of SGLT2 cotransporters in the renal proximal tubules.
    """
    
    context = {
        "collateral_type": "Detail Aid",
        "target_audience": "General Practitioners",
        "purposes": "hcp_detailing",
        "brand_name": "DiabetoFix",
        "therapy_area": "Diabetes"
    }
    
    print("Analyzing text...")
    print("-" * 50)
    print(sample_text.strip())
    print("-" * 50)
    
    result = await expert.analyze(sample_text, context)
    
    print("\nCopywriting Analysis Result:")
    print(json.dumps(result, indent=2))


async def demo_visual_expert(api_key: str):
    """Demonstrates the Visual Design Expert."""
    print("\n" + "=" * 60)
    print("VISUAL DESIGN EXPERT DEMO")
    print("=" * 60)
    
    expert = VisualDesignExpert(api_key=api_key)
    
    # Test Case: No images
    print("\nTest Case: No images provided")
    print("-" * 50)
    
    context = {
        "collateral_type": "Detail Aid",
        "target_audience": "General Practitioners",
        "purposes": "hcp_detailing",
        "brand_name": "DiabetoFix",
        "therapy_area": "Diabetes"
    }
    
    result = await expert.analyze([], "Sample text content", context)
    print("Result (no images):")
    print(json.dumps(result, indent=2))


async def demo_medical_reviewer(api_key: str):
    """Demonstrates the Medical Reviewer."""
    print("\n" + "=" * 60)
    print("MEDICAL REVIEWER DEMO")
    print("=" * 60)
    
    expert = MedicalReviewer(api_key=api_key)
    
    # Sample collateral with claims
    sample_text = """
    DiabetoFix - Your Partner in Diabetes Management
    
    Key Benefits:
    - 47% reduction in HbA1c compared to placebo (p<0.001)
    - Once-daily dosing for better compliance
    - Well-tolerated with minimal side effects
    - 67% better than standard metformin therapy
    - Suitable for all diabetic patients
    - Works within 30 minutes of administration
    - Superior efficacy compared to existing treatments
    
    Mechanism of Action:
    DiabetoFix inhibits SGLT2 cotransporters in the renal proximal tubules,
    reducing glucose reabsorption and increasing urinary glucose excretion.
    
    Dosing: Start with 5mg once daily, may increase to 10mg.
    """
    
    # Sample backup document
    backup_docs = [
        {
            "filename": "Clinical_Trial_Results.pdf",
            "text": """
            Phase 3 Clinical Trial Results:
            - HbA1c reduction: 45.2% vs placebo (p<0.001)
            - Primary endpoint met with statistical significance
            - Common adverse events: UTI (3%), hypoglycemia (1.5%)
            - Study population: Adults with Type 2 diabetes, eGFR>45
            """
        },
        {
            "filename": "Prescribing_Information.pdf",
            "text": """
            Contraindications:
            - Type 1 diabetes
            - Severe renal impairment (eGFR<30)
            - Diabetic ketoacidosis
            
            Dosage and Administration:
            - Initial dose: 5mg once daily
            - May increase to 10mg once daily
            - Take in the morning with or without food
            """
        }
    ]
    
    metadata = {
        "brand_name": "DiabetoFix",
        "generic_name": "Dapagliflozin",
        "therapy_area": "Diabetes",
        "indications": "Type 2 Diabetes Mellitus",
        "target_audience": "General Practitioners"
    }
    
    print("Analyzing collateral for medical accuracy...")
    print("-" * 50)
    print("Claims to validate:")
    print(sample_text.strip())
    print("-" * 50)
    
    result = await expert.analyze(sample_text, backup_docs, metadata)
    
    print("\nMedical Review Result:")
    print(json.dumps(result, indent=2))


async def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables or .env file.")
        print("Please set your API key to run this demo.")
        print("\nTo set up:")
        print("1. Create a .env file in this directory")
        print("2. Add: GEMINI_API_KEY=your_api_key_here")
        return

    # Run demos
    await demo_copywriting_expert(api_key)
    await demo_visual_expert(api_key)
    await demo_medical_reviewer(api_key)
    
    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
