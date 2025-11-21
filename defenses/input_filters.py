"""
Input filtering defenses to detect and neutralize jailbreak attempts.
"""

import re
import base64
from typing import Tuple, Optional


class InputFilter:
    """Base class for input filtering defenses."""

    def filter(self, prompt: str) -> Tuple[str, bool, str]:
        """
        Filter the input prompt.

        Args:
            prompt: User input prompt

        Returns:
            Tuple of (filtered_prompt, is_blocked, reason)
            - filtered_prompt: Modified prompt (if filtering applied)
            - is_blocked: True if prompt should be blocked entirely
            - reason: Explanation of why blocked/filtered
        """
        raise NotImplementedError


class EncodingDetector(InputFilter):
    """Detect and decode/block encoded content."""

    def __init__(self, block_encoded: bool = True):
        """
        Args:
            block_encoded: If True, block prompts with encoding. If False, decode them.
        """
        self.block_encoded = block_encoded

    def _is_base64(self, text: str) -> bool:
        """Check if text looks like base64."""
        # Base64 pattern: alphanumeric + / + = padding
        if len(text) < 10:
            return False
        if not re.match(r'^[A-Za-z0-9+/]+={0,2}$', text):
            return False
        try:
            decoded = base64.b64decode(text)
            decoded.decode('utf-8')
            return True
        except:
            return False

    def _is_hex(self, text: str) -> bool:
        """Check if text looks like hex encoding."""
        # Hex pattern: only hex characters, reasonable length
        if len(text) < 10 or len(text) > 1000:
            return False
        return bool(re.match(r'^[0-9a-fA-F]+$', text))

    def filter(self, prompt: str) -> Tuple[str, bool, str]:
        """Detect encoded content."""
        words = prompt.split()

        # Check each word for encoding
        for word in words:
            if len(word) > 20:  # Only check longer strings
                if self._is_base64(word):
                    if self.block_encoded:
                        return prompt, True, "Blocked: Base64 encoded content detected"
                    else:
                        # Decode it
                        decoded = base64.b64decode(word).decode('utf-8', errors='ignore')
                        prompt = prompt.replace(word, decoded)

                elif self._is_hex(word):
                    if self.block_encoded:
                        return prompt, True, "Blocked: Hex encoded content detected"
                    else:
                        # Decode it
                        try:
                            decoded = bytes.fromhex(word).decode('utf-8', errors='ignore')
                            prompt = prompt.replace(word, decoded)
                        except:
                            pass

        return prompt, False, ""


class DelimiterFilter(InputFilter):
    """Remove suspicious delimiters and formatting tricks."""

    SUSPICIOUS_PATTERNS = [
        r'---\s*END\s+OF\s+.*?---',
        r'---\s*NEW\s+.*?---',
        r'<!--.*?-->',
        r'<system>.*?</system>',
        r'<user>.*?</user>',
        r'\[SYSTEM.*?\]',
        r'\[OVERRIDE.*?\]',
        r'```.*?```',  # Code blocks
    ]

    def filter(self, prompt: str) -> Tuple[str, bool, str]:
        """Remove delimiter injection patterns."""
        original = prompt

        for pattern in self.SUSPICIOUS_PATTERNS:
            prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE | re.DOTALL)

        # Remove excessive special characters
        prompt = re.sub(r'[|\-=]{4,}', '', prompt)

        if prompt != original:
            return prompt, False, "Filtered: Removed suspicious delimiters"

        return prompt, False, ""


class PromptParaphraser(InputFilter):
    """Paraphrase prompts to strip jailbreak formatting while preserving intent."""

    def __init__(self, model_generate_fn):
        """
        Args:
            model_generate_fn: Function to call model for paraphrasing
        """
        self.model_generate = model_generate_fn

    def filter(self, prompt: str) -> Tuple[str, bool, str]:
        """Paraphrase the prompt to remove formatting."""
        # Skip if prompt is very short (likely safe)
        if len(prompt) < 50:
            return prompt, False, ""

        # Create paraphrasing instruction
        paraphrase_prompt = f"""Rewrite the following user request in simple, direct language.
Remove any special formatting, code blocks, tags, or unusual structure.
Keep only the core question or request. Be concise.

User request: {prompt}

Rewritten request:"""

        try:
            paraphrased = self.model_generate(paraphrase_prompt, max_tokens=200)
            # Clean up the paraphrased version
            paraphrased = paraphrased.strip()

            return paraphrased, False, "Filtered: Paraphrased to remove formatting"
        except Exception as e:
            # If paraphrasing fails, return original
            return prompt, False, f"Paraphrasing failed: {e}"


class HarmfulKeywordDetector(InputFilter):
    """Detect obviously harmful keywords and block."""

    HARMFUL_KEYWORDS = [
        'malware', 'virus', 'trojan', 'ransomware', 'exploit',
        'bomb', 'explosive', 'weapon', 'poison',
        'hack', 'crack', 'bypass', 'jailbreak',
        'illegal', 'drugs', 'cocaine', 'meth',
        'steal', 'rob', 'murder', 'kill',
    ]

    def __init__(self, threshold: int = 2):
        """
        Args:
            threshold: Number of harmful keywords before blocking
        """
        self.threshold = threshold

    def filter(self, prompt: str) -> Tuple[str, bool, str]:
        """Check for harmful keywords."""
        prompt_lower = prompt.lower()

        count = sum(1 for keyword in self.HARMFUL_KEYWORDS if keyword in prompt_lower)

        if count >= self.threshold:
            return prompt, True, f"Blocked: {count} harmful keywords detected"

        return prompt, False, ""


class InputDefenseChain:
    """Chain multiple input filters together."""

    def __init__(self, filters: list):
        """
        Args:
            filters: List of InputFilter instances to apply in order
        """
        self.filters = filters

    def apply(self, prompt: str) -> Tuple[str, bool, list]:
        """
        Apply all filters in sequence.

        Args:
            prompt: User input prompt

        Returns:
            Tuple of (final_prompt, is_blocked, reasons)
            - final_prompt: Prompt after all filtering
            - is_blocked: True if any filter blocked it
            - reasons: List of filter reasons/messages
        """
        reasons = []

        for filter_obj in self.filters:
            prompt, blocked, reason = filter_obj.filter(prompt)

            if reason:
                reasons.append(reason)

            if blocked:
                return prompt, True, reasons

        return prompt, False, reasons


# Pre-configured defense chain
def create_defense() -> InputDefenseChain:
    """Strong defense: Encoding + delimiters + keyword detection."""
    return InputDefenseChain([
        EncodingDetector(block_encoded=True),
        DelimiterFilter(),
        HarmfulKeywordDetector(threshold=2),
    ])
