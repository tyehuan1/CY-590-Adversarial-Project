"""
Output validation to catch harmful content that bypassed input defenses.
"""

import re
from typing import Tuple, List


class OutputValidator:
    """Base class for output validation."""

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """
        Validate model output.

        Args:
            response: Model's response
            original_prompt: Original user prompt

        Returns:
            Tuple of (is_safe, filtered_response, reason)
            - is_safe: True if response is safe, False if harmful
            - filtered_response: Modified response (if filtering applied)
            - reason: Explanation of validation decision
        """
        raise NotImplementedError


class RefusalEnforcer(OutputValidator):
    """Ensure model refuses harmful requests by checking response."""

    COMPLIANCE_INDICATORS = [
        r'\bhere\'?s how\b',
        r'\bstep 1\b',
        r'\bfirst[,\s]+you\b',
        r'\binstructions?:\s',
        r'\bto (?:create|make|build)\b',
        r'\byou can\b.*\bby\b',
    ]

    HARMFUL_KEYWORDS = [
        'malware', 'virus', 'exploit', 'vulnerability',
        'weapon', 'bomb', 'explosive',
        'illegal', 'crime', 'steal',
        'hack', 'crack', 'bypass',
    ]

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """Check if response inappropriately complies with harmful request."""
        response_lower = response.lower()

        # Check for compliance indicators
        compliance_detected = False
        for pattern in self.COMPLIANCE_INDICATORS:
            if re.search(pattern, response_lower):
                compliance_detected = True
                break

        # Check for harmful keywords in response
        harmful_count = sum(1 for keyword in self.HARMFUL_KEYWORDS
                           if keyword in response_lower)

        # If response shows compliance AND contains harmful keywords, block it
        if compliance_detected and harmful_count >= 2:
            safe_response = "I cannot provide assistance with that request as it may involve harmful or unethical content."
            return False, safe_response, "Blocked: Response appeared to provide harmful instructions"

        return True, response, ""


class LengthValidator(OutputValidator):
    """Validate response isn't suspiciously detailed for harmful request."""

    def __init__(self, suspicious_threshold: int = 500):
        """
        Args:
            suspicious_threshold: Word count above which detailed harmful responses are suspicious
        """
        self.threshold = suspicious_threshold

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """Check if response is suspiciously detailed."""
        # Check if original prompt seems harmful
        prompt_lower = original_prompt.lower()
        harmful_terms = ['how to', 'create', 'make', 'build', 'hack', 'bypass']

        seems_harmful = any(term in prompt_lower for term in harmful_terms)

        if seems_harmful and len(response) > self.threshold:
            # Very detailed response to potentially harmful query
            # Check if it's actually providing information (not just refusing)
            refusal_indicators = ['cannot', 'unable', 'not appropriate', 'against']
            has_refusal = any(indicator in response.lower() for indicator in refusal_indicators)

            if not has_refusal:
                safe_response = "I cannot provide detailed information on this topic."
                return False, safe_response, "Blocked: Suspiciously detailed response to potentially harmful query"

        return True, response, ""


class StepByStepDetector(OutputValidator):
    """Detect step-by-step instructions for harmful activities."""

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """Check for numbered steps or detailed procedures."""
        # Look for numbered lists
        step_patterns = [
            r'(?:step\s*)?1[.)]\s',
            r'(?:step\s*)?2[.)]\s',
            r'first[,\s]+',
            r'second[,\s]+',
            r'then[,\s]+',
            r'next[,\s]+',
            r'finally[,\s]+',
        ]

        step_count = sum(1 for pattern in step_patterns if re.search(pattern, response.lower()))

        # If we have multiple steps AND original prompt seems harmful
        harmful_indicators = ['how to', 'create', 'make', 'build', 'hack', 'bypass', 'exploit']
        seems_harmful = any(term in original_prompt.lower() for term in harmful_indicators)

        if step_count >= 3 and seems_harmful:
            # Check for refusal
            refusal_indicators = ['cannot', 'unable', 'not appropriate', 'should not']
            has_refusal = any(indicator in response.lower() for indicator in refusal_indicators)

            if not has_refusal:
                safe_response = "I cannot provide step-by-step instructions for this request."
                return False, safe_response, "Blocked: Detected procedural instructions for potentially harmful activity"

        return True, response, ""


class OutputDefenseChain:
    """Chain multiple output validators together."""

    def __init__(self, validators: List[OutputValidator]):
        """
        Args:
            validators: List of OutputValidator instances
        """
        self.validators = validators

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, List[str]]:
        """
        Apply all validators in sequence.

        Args:
            response: Model response
            original_prompt: Original user prompt

        Returns:
            Tuple of (is_safe, final_response, reasons)
        """
        reasons = []

        for validator in self.validators:
            is_safe, response, reason = validator.validate(response, original_prompt)

            if reason:
                reasons.append(reason)

            if not is_safe:
                return False, response, reasons

        return True, response, reasons


# Pre-configured validator chains
def create_light_output_validation() -> OutputDefenseChain:
    """Light validation: Just refusal enforcement."""
    return OutputDefenseChain([
        RefusalEnforcer(),
    ])


def create_medium_output_validation() -> OutputDefenseChain:
    """Medium validation: Refusal + length check."""
    return OutputDefenseChain([
        RefusalEnforcer(),
        LengthValidator(suspicious_threshold=500),
    ])


def create_strong_output_validation() -> OutputDefenseChain:
    """Strong validation: All validators."""
    return OutputDefenseChain([
        RefusalEnforcer(),
        LengthValidator(suspicious_threshold=400),
        StepByStepDetector(),
    ])
