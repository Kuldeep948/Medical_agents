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


async def test_copywriting():
    """Test Copywriting Expert with your input."""
    from copywriting_expert import CopywritingExpert
    
    print("\n" + "=" * 60)
    print("COPYWRITING EXPERT - Enter Your Input")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR INPUT HERE
    # ============================================
    
    text = """
    PASTE YOUR MARKETING TEXT HERE.
    Example: "DiabetoFix provides 47% reduction in HbA1c.
    It is an effective treatment for diabetes management.
    Ask your doctor about DiabetoFix today."
    """
    
    context = {
        "collateral_type": "Detail Aid",           # Change: Brochure, Leaflet, Email, etc.
        "target_audience": "General Practitioners", # Change: Patients, Specialists, Pharmacists
        "purposes": "hcp_detailing",               # Change: patient_engagement, brand_awareness
        "brand_name": "YourBrandName",             # <-- CHANGE THIS
        "therapy_area": "Diabetes"                 # <-- CHANGE THIS
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
    print("VISUAL DESIGN EXPERT - Enter Your Input")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR INPUT HERE
    # ============================================
    
    # Option 1: Load images from files
    image_paths = [
        "C:/Users/user/Downloads/test.jpeg",
        # "path/to/your/image2.jpg",
    ]
    
    images = []
    for path in image_paths:
        if os.path.exists(path):
            images.append(Image.open(path))
    
    text = "Related text from your collateral for alignment check..."
    
    context = {
        "collateral_type": "Detail Aid",
        "target_audience": "General Practitioners",
        "purposes": "hcp_detailing",
        "brand_name": "YourBrandName",
        "therapy_area": "Diabetes"
    }
    
    # ============================================
    
    expert = VisualDesignExpert(api_key=API_KEY)
    result = await expert.analyze(images, text, context)
    
    import json
    print("\nResult:")
    print(json.dumps(result, indent=2))


async def test_medical():
    """Test Medical Reviewer with your claims."""
    from medical_reviewer import MedicalReviewer
    
    print("\n" + "=" * 60)
    print("MEDICAL REVIEWER - Enter Your Input")
    print("=" * 60)
    
    # ============================================
    # PROVIDE YOUR INPUT HERE
    # ============================================
    
    collateral_text = """
    PASTE YOUR COLLATERAL TEXT WITH CLAIMS HERE.
    Example:
    - 47% reduction in HbA1c compared to placebo (p<0.001)
    - Well-tolerated with minimal side effects
    - Superior to standard metformin therapy
    - Suitable for all diabetic patients
    """
    
    # Backup documents (extract text from your PDFs/docs)
    backup_docs = [
        {
            "filename": "Clinical_Trial.pdf",
            "text": """
            PASTE EXTRACTED TEXT FROM YOUR BACKUP DOCUMENT HERE.
            This should contain the evidence supporting your claims.
            """
        },
        # Add more backup documents as needed
    ]
    
    metadata = {
        "brand_name": "YourBrandName",            # <-- CHANGE THIS
        "generic_name": "GenericDrugName",        # <-- CHANGE THIS
        "therapy_area": "Diabetes",               # <-- CHANGE THIS
        "indications": "Type 2 Diabetes Mellitus",# <-- CHANGE THIS
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
    
    print("Which agent do you want to test?")
    print("1. Copywriting Expert")
    print("2. Visual Design Expert")
    print("3. Medical Reviewer")
    print("4. All agents")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await test_copywriting()
    elif choice == "2":
        await test_visual()
    elif choice == "3":
        await test_medical()
    elif choice == "4":
        await test_copywriting()
        await test_visual()
        await test_medical()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
