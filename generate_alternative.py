#!/usr/bin/env python3
import json
import sys
import re
from transformers import pipeline

def create_fallback_json(topic, tone):
    """Create a structured JSON response as fallback."""
    # Simple template-based generation
    title_templates = {
        "friendly": f"Your Complete Guide to {topic}",
        "professional": f"Professional {topic}: A Comprehensive Overview",
        "casual": f"Everything You Need to Know About {topic}",
        "expert": f"Advanced {topic}: Expert Insights and Strategies"
    }
    
    title = title_templates.get(tone.lower(), f"{topic}: A {tone} Guide")
    
    # Generate outline based on topic keywords
    if "workout" in topic.lower() or "fitness" in topic.lower():
        outline = ["Getting Started", "Essential Equipment", "Weekly Schedule"]
    elif "cooking" in topic.lower() or "recipe" in topic.lower():
        outline = ["Preparation", "Cooking Techniques", "Serving Suggestions"]
    else:
        outline = ["Introduction", "Key Concepts", "Practical Applications"]
    
    intro = f"Welcome to this {tone.lower()} guide on {topic.lower()}. Here you'll discover essential information and practical tips to help you succeed."
    
    return {
        "title": title,
        "outline": outline,
        "intro": intro
    }

def extract_json_from_text(text):
    """Try to extract JSON from generated text using regex."""
    # Look for JSON-like patterns
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text)
    
    for match in matches:
        try:
            # Try to parse each potential JSON block
            data = json.loads(match)
            if isinstance(data, dict) and 'title' in data:
                return data
        except:
            continue
    
    return None

def main():
    # Read inputs
    topic = sys.argv[1] if len(sys.argv) > 1 else "Home Workout Routines"
    tone  = sys.argv[2] if len(sys.argv) > 2 else "Friendly"

    print(f"🎯 Generating blog outline for: {topic} (Tone: {tone})")

    # Try using a different model approach
    try:
        # Use a smaller, more reliable model for text generation
        generator = pipeline(
            "text-generation",
            model="distilgpt2",
            device=-1,
            pad_token_id=50256
        )

        # Create a more structured prompt
        prompt = f"""Blog post outline in JSON format:

Topic: {topic}
Tone: {tone}

{{
  "title": "Complete Guide to {topic}",
  "outline": [
    "Getting Started",
    "Key Points",
    "Next Steps"
  ],
  "intro": "This {tone.lower()} guide covers {topic.lower()}"
}}

Generate similar JSON for the topic "{topic}" with a {tone.lower()} tone:

{{"""

        # Generate with constrained parameters
        result = generator(
            prompt, 
            max_new_tokens=150,
            do_sample=True,
            temperature=0.3,
            num_return_sequences=1,
            pad_token_id=50256
        )
        
        raw_output = result[0]["generated_text"]
        print("Raw model output:", repr(raw_output))
        
        # Extract the generated part (remove the prompt)
        generated_part = raw_output[len(prompt):]
        full_json = "{" + generated_part
        
        print("Extracted JSON attempt:", repr(full_json))
        
        # Try to extract valid JSON
        extracted = extract_json_from_text(full_json)
        
        if extracted:
            print("\n✅ Successfully extracted JSON:")
            print(json.dumps(extracted, indent=2))
        else:
            raise ValueError("Could not extract valid JSON")
            
    except Exception as e:
        print(f"⚠️ Model generation failed: {e}")
        print("🔄 Using fallback template generation...")
        
        # Use template-based fallback
        fallback_data = create_fallback_json(topic, tone)
        print("\n✅ Generated using template:")
        print(json.dumps(fallback_data, indent=2))

if __name__ == "__main__":
    main()