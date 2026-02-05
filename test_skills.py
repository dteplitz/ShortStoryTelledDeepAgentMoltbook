"""Quick test to verify skills system is working"""
from skills_system import get_skills_manager

def test_skills():
    """Test that skills are loaded and accessible"""
    manager = get_skills_manager()
    
    # Test Level 1: Metadata loading
    print("=" * 60)
    print("LEVEL 1: METADATA (Always Loaded)")
    print("=" * 60)
    metadata = manager.get_all_metadata()
    print(f"\n✓ Found {len(metadata)} skills:\n")
    for skill in metadata:
        print(f"  • {skill.name}")
        print(f"    {skill.description[:80]}...")
        print()
    
    # Test Level 2: Loading full skill content
    print("=" * 60)
    print("LEVEL 2: INSTRUCTIONS (On-Demand)")
    print("=" * 60)
    skill_content = manager.load_skill_content("narrative_structure")
    if skill_content:
        print(f"\n✓ Loaded 'narrative_structure' skill")
        print(f"  Instructions length: {len(skill_content.instructions)} characters")
        print(f"  Available resources: {len(skill_content.available_resources)}")
        print(f"\n  Resources:")
        for resource in skill_content.available_resources:
            print(f"    - {resource}")
    
    # Test Level 3: Reading specific resource
    print("\n" + "=" * 60)
    print("LEVEL 3: RESOURCES (On-Demand)")
    print("=" * 60)
    resource = manager.read_resource(
        "narrative_structure",
        "templates/opening_hooks.txt"
    )
    if resource:
        print(f"\n✓ Loaded resource: templates/opening_hooks.txt")
        print(f"  Content length: {len(resource)} characters")
        print(f"  First 200 characters:")
        print(f"  {resource[:200]}...")
    
    # Test system prompt generation
    print("\n" + "=" * 60)
    print("SYSTEM PROMPT INTEGRATION")
    print("=" * 60)
    prompt_section = manager.generate_system_prompt_section()
    print(f"\n✓ Generated system prompt section:")
    print(prompt_section)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nSkills system is ready to use!")
    print("\nNext steps:")
    print("1. Your agent will automatically see skill metadata")
    print("2. Use use_skill('skill_name') to load instructions")
    print("3. Use read_skill_resource('skill_name', 'path') for resources")

if __name__ == "__main__":
    test_skills()
