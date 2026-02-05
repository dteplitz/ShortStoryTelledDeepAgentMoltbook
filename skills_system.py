"""Agent Skills System - Progressive disclosure for LangGraph agents

This module implements a three-level progressive disclosure system for agent skills:
- Level 1: Metadata (~100 tokens) - Always loaded in system prompt
- Level 2: Instructions (~1-2k tokens) - Loaded when skill is used
- Level 3: Resources (unlimited) - Loaded on-demand as referenced

Based on Anthropic's Agent Skills architecture adapted for LangGraph.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SkillMetadata:
    """Level 1: Metadata (always loaded, ~100 tokens per skill)"""
    name: str
    description: str
    skill_dir: Path
    
    def to_prompt_text(self) -> str:
        """Convert to text for system prompt"""
        return f"- **{self.name}**: {self.description}"


@dataclass
class SkillContent:
    """Level 2: Full instructions (loaded on-demand)"""
    metadata: SkillMetadata
    instructions: str
    available_resources: List[str]
    
    def get_resource_path(self, resource_name: str) -> Optional[Path]:
        """Get path to a specific resource file"""
        resource_path = self.metadata.skill_dir / resource_name
        return resource_path if resource_path.exists() else None


class SkillsManager:
    """Manages Agent Skills with progressive disclosure"""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.metadata_cache: Dict[str, SkillMetadata] = {}
        self.content_cache: Dict[str, SkillContent] = {}
        
        if self.skills_dir.exists():
            self._load_all_metadata()
    
    def _load_all_metadata(self):
        """Level 1: Load only metadata from all skills"""
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    metadata = self._parse_skill_metadata(skill_file, skill_path)
                    if metadata:
                        self.metadata_cache[metadata.name] = metadata
    
    def _parse_skill_metadata(self, skill_file: Path, skill_dir: Path) -> Optional[SkillMetadata]:
        """Extract metadata from SKILL.md frontmatter"""
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    return SkillMetadata(
                        name=frontmatter.get('name', skill_dir.name),
                        description=frontmatter.get('description', ''),
                        skill_dir=skill_dir
                    )
                except yaml.YAMLError:
                    pass
        return None
    
    def get_all_metadata(self) -> List[SkillMetadata]:
        """Level 1: Get all skill metadata (for system prompt)"""
        return list(self.metadata_cache.values())
    
    def load_skill_content(self, skill_name: str) -> Optional[SkillContent]:
        """Level 2: Load full skill instructions on-demand"""
        # Check cache first
        if skill_name in self.content_cache:
            return self.content_cache[skill_name]
        
        # Get metadata
        metadata = self.metadata_cache.get(skill_name)
        if not metadata:
            return None
        
        # Read full SKILL.md
        skill_file = metadata.skill_dir / "SKILL.md"
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract instructions (after frontmatter)
        if content.startswith('---'):
            parts = content.split('---', 2)
            instructions = parts[2].strip() if len(parts) >= 3 else content
        else:
            instructions = content
        
        # List available resources
        resources = []
        for item in metadata.skill_dir.iterdir():
            if item.name != "SKILL.md":
                relative_path = str(item.relative_to(metadata.skill_dir))
                resources.append(relative_path)
        
        # Cache and return
        skill_content = SkillContent(
            metadata=metadata,
            instructions=instructions,
            available_resources=resources
        )
        self.content_cache[skill_name] = skill_content
        return skill_content
    
    def read_resource(self, skill_name: str, resource_path: str) -> Optional[str]:
        """Level 3: Load specific resource file on-demand"""
        skill_content = self.load_skill_content(skill_name)
        if not skill_content:
            return None
        
        full_path = skill_content.metadata.skill_dir / resource_path
        if not full_path.exists():
            return None
        
        # Handle different file types
        if full_path.suffix == '.py':
            return f"Python script at: {full_path}\nUse read_text_file() to view or execute it."
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading resource: {str(e)}"
    
    def execute_skill_script(self, skill_name: str, script_path: str, *args) -> str:
        """Level 3: Execute a skill's Python script"""
        skill_content = self.load_skill_content(skill_name)
        if not skill_content:
            return f"Skill '{skill_name}' not found"
        
        full_path = skill_content.metadata.skill_dir / script_path
        if not full_path.exists() or full_path.suffix != '.py':
            return f"Script '{script_path}' not found or not a Python file"
        
        # Import and execute (in production, use proper sandboxing)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("skill_script", full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Assume script has a main() or run() function
            if hasattr(module, 'run'):
                return str(module.run(*args))
            elif hasattr(module, 'main'):
                return str(module.main(*args))
            else:
                return "Script loaded but no run() or main() function found"
        except Exception as e:
            return f"Error executing script: {str(e)}"
    
    def generate_system_prompt_section(self) -> str:
        """Generate Skills section for system prompt (Level 1 only)"""
        if not self.metadata_cache:
            return ""
        
        lines = ["\n## Available Agent Skills\n"]
        lines.append("You have access to specialized writing skills. Use them when creating stories:\n")
        for metadata in self.get_all_metadata():
            lines.append(metadata.to_prompt_text())
        lines.append("\nTo use a skill: use_skill(skill_name='...')")
        lines.append("To read skill resources: read_skill_resource(skill_name='...', resource_path='...')")
        return "\n".join(lines)


# Global skills manager instance
_skills_manager = None

def get_skills_manager() -> SkillsManager:
    """Get or create global skills manager"""
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = SkillsManager()
    return _skills_manager


__all__ = ["SkillsManager", "SkillMetadata", "SkillContent", "get_skills_manager"]
