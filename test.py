"""
Interactive Test Script for Medical Agents
Run this file to test the agents with your own input.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


async def test_copywriting_from_image():
    """Test Copywriting Expert with image input."""
    from copywriting_expert import CopywritingExpert
    
    print("\n" + "=" * 60)
    print("COPYWRITING EXPERT - Image Input")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR IMAGE PATH HERE
    # ============================================
    
    image_path = "C:/Users/user/Downloads/test.jpeg"  # <-- CHANGE THIS
    
    context = {
        "collateral_type": "Detail Aid",           # Change: Brochure, Leaflet, Email, etc.
        "target_audience": "General Practitioners", # Change: Patients, Specialists, Pharmacists
        "purposes": "hcp_detailing",               # Change: patient_engagement, brand_awareness
        "brand_name": "YourBrandName",             # <-- CHANGE THIS
        "therapy_area": "Diabetes"                 # <-- CHANGE THIS
    }
    
    # ============================================
    
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found at {image_path}")
        print("Please update the image_path variable with a valid path.")
        return
    
    expert = CopywritingExpert(api_key=API_KEY)
    
    print(f"Processing image: {image_path}")
    print("-" * 50)
    
    # Use the new analyze_from_image method
    result = await expert.analyze_from_image(image_path, context)
    
    import json
    print("\n" + "=" * 50)
    print("ANALYSIS RESULT:")
    print("=" * 50)
    print(json.dumps(result, indent=2))


async def test_copywriting_from_text():
    """Test Copywriting Expert with text input."""
    from copywriting_expert import CopywritingExpert
    
    print("\n" + "=" * 60)
    print("COPYWRITING EXPERT - Text Input")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR TEXT HERE
    # ============================================
    
    text = """
    DiabetoFix - Your Partner in Diabetes Care
    47% HbA1c reduction in just 12 weeks!
    Better than standard therapy. Safe for all patients.
    Ask your doctor today.
    """
    
    context = {
        "collateral_type": "Detail Aid",
        "target_audience": "General Practitioners",
        "purposes": "hcp_detailing",
        "brand_name": "DiabetoFix",
        "therapy_area": "Diabetes"
    }
    
    # ============================================
    
    expert = CopywritingExpert(api_key=API_KEY)
    result = await expert.analyze(text, context)
    
    import json
    print("\nResult:")
    print(json.dumps(result, indent=2))


async def test_visual():
    """Test Visual Design Expert with your images."""
    from visual_design_expert import VisualDesignExpert
    from PIL import Image
    
    print("\n" + "=" * 60)
    print("VISUAL DESIGN EXPERT - Image Analysis")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR IMAGE PATHS HERE
    # ============================================
    
    image_paths = [
        "C:/Users/user/Downloads/test.jpeg",  # <-- CHANGE THIS
    ]
    
    text = "Related text from your collateral for alignment check..."
    
    context = {
        "collateral_type": "Detail Aid",
        "target_audience": "General Practitioners",
        "purposes": "hcp_detailing",
        "brand_name": "YourBrandName",
        "therapy_area": "Diabetes"
    }
    
    # ============================================
    
    images = []
    for path in image_paths:
        if os.path.exists(path):
            images.append(Image.open(path))
            print(f"Loaded image: {path}")
        else:
            print(f"Image not found: {path}")
    
    if not images:
        print("No images loaded. Please check your image paths.")
        return
    
    expert = VisualDesignExpert(api_key=API_KEY)
    result = await expert.analyze(images, text, context)
    
    import json
    print("\nResult:")
    print(json.dumps(result, indent=2))


async def test_medical():
    """Test Medical Reviewer with realistic claims and backup documents."""
    from medical_reviewer import MedicalReviewer
    
    print("\n" + "=" * 60)
    print("MEDICAL REVIEWER - Claim Validation")
    print("=" * 60)
    
    # ============================================
    # SAMPLE COLLATERAL WITH VARIOUS CLAIM TYPES
    # ============================================
    
    collateral_text = """
    CARDIOMAX - Comprehensive Cardiovascular Protection
    
    HEADLINE:
    67% Reduction in Major Adverse Cardiac Events (MACE) - 
    Superior to Standard Therapy
    
    KEY EFFICACY DATA:
    • Primary endpoint: 47% reduction in hospitalization for heart failure (p<0.001)
    • Secondary endpoint: 32% reduction in cardiovascular mortality (p=0.003)
    • Statistically significant improvement in exercise capacity (p=0.08)
    • 24-hour blood pressure control with once-daily dosing
    
    SAFETY PROFILE:
    • Well-tolerated with minimal side effects
    • Safe in patients with renal impairment
    • No significant drug interactions reported
    • Suitable for all cardiac patients including elderly
    
    MECHANISM OF ACTION:
    CardioMax selectively inhibits the sodium-glucose cotransporter-2 (SGLT2) 
    in the renal proximal tubules, reducing glucose reabsorption and providing 
    cardiovascular protection through osmotic diuresis.
    
    DOSING:
    • Start with 10mg once daily
    • May increase to 25mg based on response
    • Take with or without food
    
    References: CARDIO-OUTCOMES Trial 2023, FDA Approval Letter
    """
    
    # ============================================
    # BACKUP DOCUMENTS (Clinical Trial + PI)
    # ============================================
    
    backup_docs = [
        {
            "filename": "CARDIO_OUTCOMES_Trial_2023.pdf",
            "text": """
            CARDIO-OUTCOMES Phase 3 Clinical Trial Results
            
            Study Design:
            - Randomized, double-blind, placebo-controlled
            - N = 4,500 patients with established cardiovascular disease
            - Follow-up: 36 months
            
            Primary Endpoint Results:
            - Hospitalization for heart failure: 42% reduction vs placebo (p<0.001)
              [Note: Collateral claims 47% - this is a DATA MISMATCH]
            
            Secondary Endpoints:
            - Cardiovascular mortality: 32% reduction (p=0.003) ✓
            - All-cause mortality: 18% reduction (p=0.02)
            - Exercise capacity (6MWT): Improved but not statistically significant (p=0.08)
              [Note: p=0.08 does NOT meet significance threshold]
            
            MACE Composite:
            - 38% reduction in MACE (p<0.001)
              [Note: Collateral claims 67% - MAJOR DISCREPANCY]
            
            Safety Data:
            - Overall adverse events similar to placebo
            - Genital infections: 4.2% vs 1.1% placebo
            - Diabetic ketoacidosis: 0.3% (rare but serious)
            - Hypotension: 2.1% vs 0.8% placebo
            
            Study Population:
            - Adults 45-80 years with Type 2 diabetes and established CVD
            - eGFR ≥ 30 mL/min/1.73m²
            - Excluded: Type 1 diabetes, pregnancy, severe hepatic impairment
            """
        },
        {
            "filename": "CardioMax_Prescribing_Information.pdf",
            "text": """
            CARDIOMAX (dapagliflozin) PRESCRIBING INFORMATION
            
            INDICATIONS AND USAGE:
            - Type 2 diabetes mellitus with established cardiovascular disease
            - Heart failure with reduced ejection fraction (HFrEF)
            
            CONTRAINDICATIONS:
            - Type 1 diabetes mellitus
            - Diabetic ketoacidosis
            - Severe renal impairment (eGFR < 25 mL/min)
            - Known hypersensitivity to dapagliflozin
            
            WARNINGS AND PRECAUTIONS:
            - Hypotension: Risk increased in elderly, patients on diuretics
            - Ketoacidosis: Monitor for signs/symptoms
            - Genital mycotic infections: Common adverse event
            - Fournier's gangrene: Rare but serious
            
            USE IN SPECIFIC POPULATIONS:
            - Elderly (≥65): Use with caution due to hypotension risk
            - Renal Impairment: 
              • eGFR 25-45: Reduced efficacy for glycemic control
              • eGFR < 25: Contraindicated
            - Hepatic Impairment: Not recommended in severe impairment
            - Pregnancy: Category C - not recommended
            
            DOSAGE AND ADMINISTRATION:
            - Initial dose: 5mg once daily (NOT 10mg as claimed)
            - Maximum dose: 10mg once daily (NOT 25mg)
            - Morning administration recommended
            
            DRUG INTERACTIONS:
            - Insulin/sulfonylureas: Increased hypoglycemia risk
            - Diuretics: Additive effect, monitor volume status
            - Lithium: Monitor lithium levels
            """
        }
    ]
    
    metadata = {
        "brand_name": "CardioMax",
        "generic_name": "Dapagliflozin",
        "therapy_area": "Cardiovascular / Diabetes",
        "indications": "Type 2 Diabetes with CVD, Heart Failure (HFrEF)",
        "target_audience": "Cardiologists"
    }
    
    # ============================================
    
    print("\nCollateral Claims to Validate:")
    print("-" * 50)
    print(collateral_text[:500] + "...")
    print("-" * 50)
    
    print("\nBackup Documents Provided:")
    for doc in backup_docs:
        print(f"  • {doc['filename']}")
    
    print("\n" + "=" * 50)
    print("ANALYZING CLAIMS...")
    print("=" * 50)
    
    expert = MedicalReviewer(api_key=API_KEY)
    result = await expert.analyze(collateral_text, backup_docs, metadata)
    
    import json
    print("\n" + "=" * 50)
    print("MEDICAL REVIEW RESULT:")
    print("=" * 50)
    print(json.dumps(result, indent=2))


async def main():
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY not found!")
        print("Add it to .env file: GEMINI_API_KEY=your_key_here")
        return
    
    print("\nWhich agent do you want to test?")
    print("1. Copywriting Expert (from IMAGE) <-- Extracts text from image first")
    print("2. Copywriting Expert (from TEXT)")
    print("3. Visual Design Expert")
    print("4. Medical Reviewer")
    print("5. All agents")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        await test_copywriting_from_image()
    elif choice == "2":
        await test_copywriting_from_text()
    elif choice == "3":
        await test_visual()
    elif choice == "4":
        await test_medical()
    elif choice == "5":
        await test_copywriting_from_image()
        await test_visual()
        await test_medical()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
