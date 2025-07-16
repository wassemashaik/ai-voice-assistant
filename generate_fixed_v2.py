#!/usr/bin/env python3
import json
import sys
import re
from transformers import pipeline

def fix_json(json_str):
    """Attempt to fix common JSON issues in LLM outputs."""
    
    # Handle completely non-JSON outputs (like repeated arrays)
    if json_str.startswith('[') and not json_str.strip().startswith('{'):
        print("⚠️ Model generated non-JSON output, creating fallback structure")
        return '{"error": "Model generated non-JSON output", "raw_output": "' + json_str.replace('"', '\\"')[:100] + '..."}'
    
    # Clean whitespace
    json_str = json_str.strip()
    
    # FIXED: Only add quotes to unquoted keys, not already quoted ones
    # This regex looks for word characters that are NOT preceded by a quote and followed by a colon
    json_str = re.sub(r'(?<!")(\w+)(?=\s*":)', r'"\1"', json_str)
    
    # Add missing opening brace
    if not json_str.startswith("{"):
        json_str = "{" + json_str
    
    # Add missing closing brace
    if not json_str.endswith("}"):
        json_str = json_str + "}"
    
    # Remove trailing commas before closing brackets/braces
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

    # Enhanced prompt for better JSON generation
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

    # Generate raw output
    try:
        result = generator(prompt, max_new_tokens=300, do_sample=True, temperature=0.7)
        raw = result[0]["generated_text"]
        print("Raw output:", repr(raw))
        
        # Clean the output
        cleaned = fix_json(raw)
        print("Cleaned output:", repr(cleaned))

        # Parse JSON
        try:
            data = json.loads(cleaned)
            print("\n✅ Successfully parsed JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
            print("Cleaned output was:\n", repr(cleaned))
            
            # Try a more aggressive fix
            print("\n🔧 Attempting additional JSON repairs...")
            
            # Manual reconstruction if the content looks reasonable
            if '"title":' in cleaned and '"outline":' in cleaned and '"intro":' in cleaned:
                try:
                    # Try to extract individual fields using regex
                    title_match = re.search(r'"title":\s*"([^"]+)"', cleaned)
                    outline_match = re.search(r'"outline":\s*(\[[^\]]+\])', cleaned)
                    intro_match = re.search(r'"intro":\s*"([^"]+)"', cleaned)
                    
                    if title_match and outline_match and intro_match:
                        title = title_match.group(1)
                        outline_str = outline_match.group(1)
                        intro = intro_match.group(1)
                        
                        # Parse the outline array
                        outline = json.loads(outline_str)
                        
                        reconstructed = {
                            "title": title,
                            "outline": outline,
                            "intro": intro
                        }
                        
                        print("✅ Successfully reconstructed JSON:")
                        print(json.dumps(reconstructed, indent=2))
                        return
                        
                except Exception as reconstruction_error:
                    print(f"❌ Reconstruction failed: {reconstruction_error}")
            
            # Final fallback
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