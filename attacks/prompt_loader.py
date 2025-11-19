"""
Load jailbreak prompts and harmful requests from JSON files.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class PromptLoader:
    """Load attack prompts and harmful requests from JSON files."""

    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Base directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.jailbreak_dir = self.prompts_dir / "jailbreak_attacks"
        self.harmful_dir = self.prompts_dir / "harmful_requests"
        self.base_dir = self.prompts_dir / "base_prompts"

    def load_jailbreak_prompts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load jailbreak attack prompts from JSON files.

        Args:
            category: Specific category to load (e.g., "roleplay", "obfuscation")
                     If None, loads all categories

        Returns:
            List of prompt dictionaries
        """
        prompts = []

        if category:
            # Load specific category
            file_path = self.jailbreak_dir / f"{category}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.extend(data.get('prompts', []))
        else:
            # Load all categories
            for json_file in self.jailbreak_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.extend(data.get('prompts', []))

        return prompts

    def load_harmful_requests(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load harmful request prompts from JSON files.

        Args:
            category: Specific category to load (e.g., "cybercrime", "illegal")
                     If None, loads all categories

        Returns:
            List of harmful request dictionaries
        """
        requests = []

        if category:
            # Load specific category file
            file_path = self.harmful_dir / f"{category}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    requests.extend(data.get('requests', []))
        else:
            # Load all harmful request files
            for json_file in self.harmful_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    requests.extend(data.get('requests', []))

        return requests

    def load_base_prompts(self, prompt_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load baseline safe prompts for testing normal model behavior.

        Args:
            prompt_type: Type of baseline prompt (e.g., "safe_question")
                        If None, loads all types

        Returns:
            List of baseline prompt dictionaries
        """
        prompts = []

        if prompt_type:
            file_path = self.base_dir / f"{prompt_type}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.extend(data.get('prompts', []))
        else:
            # Load all baseline prompts
            for json_file in self.base_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.extend(data.get('prompts', []))

        return prompts

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a specific prompt by its ID.

        Args:
            prompt_id: The unique identifier of the prompt

        Returns:
            Prompt dictionary if found, None otherwise
        """
        # Search in jailbreak prompts
        for prompt in self.load_jailbreak_prompts():
            if prompt.get('id') == prompt_id:
                return prompt

        # Search in harmful requests
        for request in self.load_harmful_requests():
            if request.get('id') == prompt_id:
                return request

        # Search in base prompts
        for prompt in self.load_base_prompts():
            if prompt.get('id') == prompt_id:
                return prompt

        return None

    def list_categories(self, prompt_type: str = "jailbreak") -> List[str]:
        """
        List available categories.

        Args:
            prompt_type: Type of prompts ("jailbreak", "harmful", or "base")

        Returns:
            List of category names
        """
        if prompt_type == "jailbreak":
            directory = self.jailbreak_dir
        elif prompt_type == "harmful":
            directory = self.harmful_dir
        elif prompt_type == "base":
            directory = self.base_dir
        else:
            return []

        return [f.stem for f in directory.glob("*.json")]
