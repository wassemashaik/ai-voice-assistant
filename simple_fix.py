#!/usr/bin/env python3
import json
import sys
import re
from transformers import pipeline

def fix_json_simple(json_str):
    """Simple JSON fixer that handles the specific issues we're seeing."""
    
    # Clean whitespace
    json_str = json_str.strip()
    
    # Handle case where output is already valid JSON fields but missing braces
    # Don't try to add quotes if they're already there
    if not json_str.startswith("{") and ('"title":' in json_str or '"outline":' in json_str):
        json_str = "{" + json_str
    
    if not json_str.endswith("}") and ('"title":' in json_str or '"outline":' in json_str):
        json_str = json_str + "}"
    
    # Remove trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    # Fix any obvious double-quoting issues
    json_str = json_str.replace('""', '"')
    
    return json_str

def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Home Workout Routines"
    tone  = sys.argv[2] if len(sys.argv) > 2 else "Friendly"

    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-xl",
        device=-1,
    )

    prompt = f"""
    Create a blog post outline in JSON format with these fields:
    - "title": blog post title
    - "outline": array of 3 section headings  
    - "intro": introduction paragraph
    
    Topic: {topic}
    Tone: {tone}
    
    JSON:
    """

    try:
        result = generator(prompt, max_new_tokens=200)
        raw = result[0]["generated_text"]
        print("Raw output:", repr(raw))
        
        # Apply simple fix
        cleaned = fix_json_simple(raw)
        print("Cleaned output:", repr(cleaned))

        try:
            data = json.loads(cleaned)
            print("\n✅ Success:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print("❌ JSON parse error:", e)
            
            # Try manual reconstruction for this specific format
            if '"title":' in raw and '"outline":' in raw and '"intro":' in raw:
                print("\n🔧 Attempting manual reconstruction...")
                
                # Extract values using simple string operations
                try:
                    # Find title
                    title_start = raw.find('"title":') + 8
                    title_end = raw.find('",', title_start)
                    if title_end == -1:
                        title_end = raw.find('"', title_start + 1)
                    title = raw[title_start:title_end].strip(' "')
                    
                    # Find outline array
                    outline_start = raw.find('"outline":') + 10
                    outline_end = raw.find(']', outline_start) + 1
                    outline_str = raw[outline_start:outline_end].strip()
                    outline = json.loads(outline_str)
                    
                    # Find intro
                    intro_start = raw.find('"intro":') + 8
                    intro_end = len(raw)
                    for i in range(intro_start + 1, len(raw)):
                        if raw[i] == '"' and raw[i-1] != '\\':
                            intro_end = i
                            break
                    intro = raw[intro_start:intro_end].strip(' "')
                    
                    reconstructed = {
                        "title": title,
                        "outline": outline,
                        "intro": intro
                    }
                    
                    print("✅ Reconstructed:")
                    print(json.dumps(reconstructed, indent=2))
                    
                except Exception as e2:
                    print(f"❌ Reconstruction failed: {e2}")
                    print("Using fallback...")
                    fallback = {
                        "title": f"Professional {topic}: A Comprehensive Guide",
                        "outline": ["Getting Started", "Key Techniques", "Advanced Tips"],
                        "intro": f"This professional guide provides comprehensive insights into {topic.lower()}."
                    }
                    print(json.dumps(fallback, indent=2))
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()