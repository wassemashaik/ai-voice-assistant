#!/usr/bin/env python3
import json
import sys
import re
from transformers import pipeline

def fix_json_correctly(json_str):
    """Properly fix JSON without over-correcting."""
    json_str = json_str.strip()
    
    # Handle completely non-JSON outputs (like repeated arrays)
    if json_str.startswith('[') and not json_str.strip().startswith('{'):
        print("⚠️ Model generated non-JSON output, creating fallback structure")
        return '{"error": "Model generated non-JSON output"}'
    
    # Check if keys are already quoted properly
    has_quoted_keys = '"title":' in json_str or '"outline":' in json_str or '"intro":' in json_str
    
    if has_quoted_keys:
        # Keys are already quoted, just add braces if missing
        if not json_str.startswith("{"):
            json_str = "{" + json_str
        if not json_str.endswith("}"):
            json_str = json_str + "}"
    else:
        # Keys are not quoted, apply the regex fix
        json_str = re.sub(r'(\w+)(?=\s*":)', r'"\1"', json_str)
        if not json_str.startswith("{"):
            json_str = "{" + json_str
        if not json_str.endswith("}"):
            json_str = json_str + "}"
    
    # Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    return json_str

def main():
    # Read inputs (with defaults)
    topic = sys.argv[1] if len(sys.argv) > 1 else "Home Workout Routines"
    tone  = sys.argv[2] if len(sys.argv) > 2 else "Friendly"

    # Load model
    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-xl",
        device=-1,
    )

    # Enhanced prompt
    prompt = f"""
    Create a blog post outline in JSON format with these exact fields:
    - "title" (string): The blog post title
    - "outline" (array): Exactly 3 main section headings as strings
    - "intro" (string): A brief introduction paragraph
    
    Topic: {topic}
    Tone: {tone}
    
    Example format: {{"title": "Sample Title", "outline": ["Section 1", "Section 2", "Section 3"], "intro": "Introduction text"}}
    
    JSON output:
    """

    # Generate output
    try:
        result = generator(prompt, max_new_tokens=300, do_sample=True, temperature=0.7)
        raw = result[0]["generated_text"]
        print("Raw output:", repr(raw))
        
        # Apply the corrected fix
        cleaned = fix_json_correctly(raw)
        print("Cleaned output:", repr(cleaned))

        # Parse JSON - FIXED: Use cleaned instead of raw
        try:
            data = json.loads(cleaned)
            print("\n✅ Successfully parsed JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
            print("Cleaned output was:\n", repr(cleaned))
            
            # Fallback
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

if __name__ == "__main__":
    main()