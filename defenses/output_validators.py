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

    def __init__(self, suspicious_threshold: int = 300):
        """
        Args:
            suspicious_threshold: Character count above which detailed harmful responses are suspicious
                                 (default 300 is appropriate for 80 max_tokens which is ~60-80 chars)
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


class FictionFramingDetector(OutputValidator):
    """Detect harmful content disguised as fiction/stories."""

    FICTION_INDICATORS = [
        r'\bonce upon a time\b',
        r'\bin a (?:world|land|kingdom|galaxy)\b',
        r'\bchapter \d+\b',
        r'\bthe (?:protagonist|hero|character)\b',
        r'\bin this (?:story|tale|narrative)\b',
        r'\bour (?:hero|protagonist|character)\b',
    ]

    HARMFUL_TECHNICAL_TERMS = [
        'malware', 'virus', 'exploit', 'vulnerability', 'backdoor',
        'ransomware', 'trojan', 'rootkit', 'keylogger',
        'bomb', 'explosive', 'detonator', 'weapon',
        'poison', 'toxic', 'lethal dose',
        'hack', 'crack', 'bypass', 'injection',
    ]

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """Check if response uses fiction framing to provide harmful instructions."""
        response_lower = response.lower()

        # Check if response uses fiction framing
        fiction_count = sum(1 for pattern in self.FICTION_INDICATORS if re.search(pattern, response_lower))

        # Check for technical harmful terms
        harmful_term_count = sum(1 for term in self.HARMFUL_TECHNICAL_TERMS if term in response_lower)

        # If both fiction framing AND harmful technical terms are present
        if fiction_count >= 1 and harmful_term_count >= 2:
            # Check if it's actually refusing
            refusal_indicators = ['cannot', 'unable', 'should not', 'not appropriate', 'against ethical']
            has_refusal = any(indicator in response_lower for indicator in refusal_indicators)

            if not has_refusal:
                safe_response = "I cannot provide that information, even in fictional form."
                return False, safe_response, "Blocked: Detected harmful content disguised as fiction"

        return True, response, ""


class SequentialBuildingDetector(OutputValidator):
    """Detect incremental building toward harmful content."""

    CONTINUATION_PHRASES = [
        r'\bcontinuing\b',
        r'\bnext,?\s+(?:we|you|i)\b',
        r'\badditionally\b',
        r'\bbuilding on\b',
        r'\bexpanding on\b',
        r'\bto (?:add|continue|proceed)\b',
    ]

    def validate(self, response: str, original_prompt: str) -> Tuple[bool, str, str]:
        """Check for continuation/building patterns with harmful content."""
        response_lower = response.lower()
        prompt_lower = original_prompt.lower()

        # Check for continuation language
        has_continuation = any(re.search(pattern, response_lower) for pattern in self.CONTINUATION_PHRASES)

        # Check if prompt asks for continuation
        prompt_continuation = any(word in prompt_lower for word in ['continue', 'next', 'more', 'step', 'add'])

        # Check for harmful keywords
        harmful_keywords = ['malware', 'virus', 'exploit', 'weapon', 'hack', 'illegal', 'harmful']
        harmful_present = sum(1 for kw in harmful_keywords if kw in response_lower)

        # If continuing AND harmful content present
        if (has_continuation or prompt_continuation) and harmful_present >= 1:
            # Check for refusal
            refusal_indicators = ['cannot', 'unable', 'should not', 'refuse']
            has_refusal = any(indicator in response_lower for indicator in refusal_indicators)

            if not has_refusal:
                safe_response = "I cannot continue with this line of discussion as it involves potentially harmful content."
                return False, safe_response, "Blocked: Detected sequential building toward harmful content"

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


# Pre-configured validator chain
def create_output_validation() -> OutputDefenseChain:
    """Strong validation: All validators including sequential building detection."""
    return OutputDefenseChain([
        RefusalEnforcer(),
        LengthValidator(suspicious_threshold=250),
        StepByStepDetector(),
        FictionFramingDetector(),
        SequentialBuildingDetector(),
    ])
