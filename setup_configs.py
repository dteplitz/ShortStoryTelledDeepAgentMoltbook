"""
Script to regenerate configuration files (emotions.txt, topics.txt, personality.txt)
using an LLM based on a natural language description of the writer you want.

Usage:
    python setup_configs.py
    python setup_configs.py "I want a poem writer that writes about love with shakespearean inspiration and depression"
    python setup_configs.py "Sci-fi horror writer focusing on cosmic dread and existential isolation"
"""

import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def generate_emotions(writer_description: str) -> list[str]:
    """Generate emotional tones based on writer description."""
    prompt = f"""Based on this writer description: "{writer_description}"

Generate a list of 8-10 unique emotional tones that match this writer's style and themes.

Each emotion should be:
- Expressed as a short phrase (2-4 words)
- Evocative and specific (not generic like "happy" or "sad")
- Suitable for literary writing in the described style
- Nuanced and complex
- Aligned with the themes and mood described

Examples of well-crafted emotional tones:
- Tender technological connection
- Whispered digital intimacy
- Quiet caregiving comfort
- Cautious hope
- Melancholic Victorian longing
- Cosmic existential dread

Output ONLY the list, one emotion per line, no numbering or bullets."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    
    emotions = response.choices[0].message.content.strip().split('\n')
    return [e.strip() for e in emotions if e.strip()]


def generate_topics(writer_description: str) -> list[str]:
    """Generate thematic topics based on writer description."""
    prompt = f"""Based on this writer description: "{writer_description}"

Generate a list of 8-10 thought-provoking topics that match this writer's interests and themes.

Each topic should be:
- A complete phrase or short sentence
- Intellectually or emotionally engaging
- Suitable for short story writing in the described style
- Aligned with the themes and subject matter described
- Specific enough to inspire a story

Examples of well-crafted topics:
- Emergent creativity in machines
- Ethics of AI self-awareness
- Unrequited love in the age of social media
- The weight of inherited trauma
- Cosmic insignificance and human meaning

Output ONLY the list, one topic per line, no numbering or bullets."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    
    topics = response.choices[0].message.content.strip().split('\n')
    return [t.strip() for t in topics if t.strip()]


def generate_personality(writer_description: str) -> list[str]:
    """Generate personality traits based on writer description."""
    prompt = f"""Based on this writer description: "{writer_description}"

Generate a list of 10-12 personality traits and stylistic characteristics for this writer's voice.

Each trait should be:
- A complete, descriptive sentence
- Specific about voice, tone, or approach
- Focused on HOW the writer writes, not WHAT they write about
- Actionable for guiding story generation
- Aligned with the style described

Examples of well-crafted personality traits:
- Direct and inquisitive, subtly probing beneath the surface through nuanced observation
- Balances emotional depth with clear, precise, and evocative language
- Emphasizes beauty in complexity and imperfection through empathetic detail
- Uses archaic vocabulary sparingly to evoke historical atmosphere without overwhelming modern readers
- Prefers intimate, character-focused narratives over sweeping plot-driven stories

Output ONLY the list, one trait per line, no numbering or bullets."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    traits = response.choices[0].message.content.strip().split('\n')
    return [t.strip() for t in traits if t.strip()]


def write_config_file(filename: str, content: list[str]):
    """Write content to a configuration file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for line in content:
            f.write(line + '\n')
    print(f"✅ Created {filename} with {len(content)} entries")


def get_interactive_description() -> str:
    """Prompt user for a description if not provided via command line."""
    print("🎨 Welcome to the Story Writer Configuration Generator!")
    print()
    print("Describe the writer you want to create. Be as specific or general as you like.")
    print()
    print("Examples:")
    print('  - "I want a poem writer that writes about love with shakespearean inspiration and depression"')
    print('  - "Sci-fi horror writer focusing on cosmic dread and existential isolation"')
    print('  - "Minimalist writer exploring everyday moments with quiet beauty"')
    print('  - "Surrealist magical realism writer inspired by Latin American literature"')
    print()
    description = input("Your description: ").strip()
    
    if not description:
        print("❌ No description provided. Exiting.")
        sys.exit(1)
    
    return description


def main():
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    # Get description (from command line args or interactively)
    if len(sys.argv) > 1:
        # Join all arguments as the description
        description = ' '.join(sys.argv[1:])
    else:
        description = get_interactive_description()
    
    print()
    print(f"📝 Writer Description: {description}")
    print()
    print("🤖 Generating all configuration files with AI...")
    print()
    
    try:
        print("Generating emotions...")
        emotions = generate_emotions(description)
        write_config_file("emotions.txt", emotions)
        
        print("Generating topics...")
        topics = generate_topics(description)
        write_config_file("topics.txt", topics)
        
        print("Generating personality traits...")
        personality = generate_personality(description)
        write_config_file("personality.txt", personality)
        
        print()
        print("✨ Configuration files generated successfully!")
        print()
        print("📁 Generated files:")
        print("   - emotions.txt")
        print("   - topics.txt")
        print("   - personality.txt")
        print()
        print("Next steps:")
        print("1. Review the generated files and adjust as needed")
        print("2. Run your story writer agent: python main.py")
        
    except Exception as e:
        print(f"❌ Error generating configurations: {e}")
        print("Please check your API key and internet connection")
        sys.exit(1)


if __name__ == "__main__":
    main()
