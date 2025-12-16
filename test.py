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
    """Test Medical Reviewer with your claims."""
    from medical_reviewer import MedicalReviewer
    
    print("\n" + "=" * 60)
    print("MEDICAL REVIEWER - Claim Validation")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR INPUT HERE
    # ============================================
    
    collateral_text = """
    DiabetoFix - Key Benefits:
    - 47% reduction in HbA1c compared to placebo (p<0.001)
    - Well-tolerated with minimal side effects
    - Superior to standard metformin therapy
    - Suitable for all diabetic patients
    """
    
    backup_docs = [
        {
            "filename": "Clinical_Trial.pdf",
            "text": """
            Phase 3 Clinical Trial Results:
            - HbA1c reduction: 45.2% vs placebo (p<0.001)
            - Common adverse events: UTI (3%), hypoglycemia (1.5%)
            - Study population: Adults with Type 2 diabetes, eGFR>45
            """
        },
    ]
    
    metadata = {
        "brand_name": "DiabetoFix",
        "generic_name": "Dapagliflozin",
        "therapy_area": "Diabetes",
        "indications": "Type 2 Diabetes Mellitus",
        "target_audience": "General Practitioners"
    }
    
    # ============================================
    
    expert = MedicalReviewer(api_key=API_KEY)
    result = await expert.analyze(collateral_text, backup_docs, metadata)
    
    import json
    print("\nResult:")
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
