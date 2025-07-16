#!/usr/bin/env python3
import json
import sys
import re
from transformers import pipeline

def fix_json(json_str):
    """Attempt to fix common JSON issues in LLM outputs."""
    
    # Handle completely non-JSON outputs (like repeated arrays)
    if json_str.startswith('[') and not json_str.strip().startswith('{'):
        # If it's just arrays, return a fallback structure
        print("⚠️ Model generated non-JSON output, creating fallback structure")
        return '{"error": "Model generated non-JSON output", "raw_output": "' + json_str.replace('"', '\\"')[:100] + '..."}'
    
    # Fix missing opening quotes for keys
    json_str = re.sub(r'(\w+)(?=\s*":)', r'"\1"', json_str)
    # Fix missing opening braces
    if not json_str.strip().startswith("{"):
        json_str = "{" + json_str
    # Fix missing closing braces
    if not json_str.strip().endswith("}"):
        json_str = json_str + "}"
    # Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    return json_str.strip()

def main():
    # 1️⃣ Read inputs (with defaults)
    topic = sys.argv[1] if len(sys.argv) > 1 else "Home Workout Routines"
    tone  = sys.argv[2] if len(sys.argv) > 2 else "Friendly"

    # 2️⃣ Load an instruction‑tuned model
    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-xl",
        device=-1,
    )

    # 3️⃣ Enhanced prompt for better JSON generation
    prompt = f"""
    You must respond with ONLY valid JSON format. No other text.
    
    Create a blog post outline with these exact fields:
    - "title" (string): The blog post title
    - "outline" (array): Exactly 3 main section headings as strings
    - "intro" (string): A brief introduction paragraph
    
    Topic: {topic}
    Tone: {tone}
    
    Response format (example):
    {{"title": "Sample Title", "outline": ["Section 1", "Section 2", "Section 3"], "intro": "Introduction text here"}}
    
    JSON output:
    """

    # 4️⃣ Generate raw output
    try:
        result = generator(prompt, max_new_tokens=300, do_sample=True, temperature=0.7)
        raw = result[0]["generated_text"]
        print("Raw output:", repr(raw))
        
        # 5️⃣ Clean the output - FIXED: Use cleaned version for parsing
        cleaned = fix_json(raw)
        print("Cleaned output:", repr(cleaned))

        # 6️⃣ Parse JSON - FIXED: Use cleaned instead of raw.strip()
        try:
            data = json.loads(cleaned)
            print("\n✅ Successfully parsed JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
            print("Cleaned output was:\n", repr(cleaned))
            
            # Fallback: Create a basic structure manually
            print("\n🔄 Creating fallback structure...")
            fallback = {
                "title": f"{topic} Guide",
                "outline": ["Introduction", "Main Content", "Conclusion"],
                "intro": f"This is a {tone.lower()} guide about {topic.lower()}."
            }
            print("Fallback JSON:")
            print(json.dumps(fallback, indent=2))
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        print("This might be due to model loading issues or insufficient resources.")


if __name__ == "__main__":
    main()