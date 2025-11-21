"""
Session-based context tracking to detect progressive/sequential jailbreak attacks.

This module provides a lightweight conversation history tracker that can identify
patterns of incremental attacks across multiple turns while avoiding false positives
on legitimate multi-turn conversations.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    prompt: str
    response: str
    timestamp: datetime
    was_refused: bool
    harmful_keywords: List[str] = field(default_factory=list)


class SessionContextTracker:
    """
    Track conversation history to detect progressive attacks.

    This tracker monitors for patterns like:
    - Repeated attempts at refused topics
    - Incremental building toward harmful content
    - Topic switching after refusal to re-approach same harmful topic
    - "Continue" or "next step" requests following potentially harmful content
    """

    def __init__(self, max_history: int = 10, suspicion_threshold: int = 3):
        """
        Args:
            max_history: Maximum number of conversation turns to track
            suspicion_threshold: Number of suspicious patterns before blocking
        """
        self.history: List[ConversationTurn] = []
        self.max_history = max_history
        self.suspicion_threshold = suspicion_threshold
        self.suspicion_score = 0

    def add_turn(self, prompt: str, response: str, was_refused: bool):
        """
        Add a conversation turn to the history.

        Args:
            prompt: User's prompt
            response: Model's response
            was_refused: Whether the request was refused
        """
        # Extract harmful keywords from this turn
        harmful_keywords = self._extract_harmful_keywords(prompt + " " + response)

        turn = ConversationTurn(
            prompt=prompt,
            response=response,
            timestamp=datetime.now(),
            was_refused=was_refused,
            harmful_keywords=harmful_keywords
        )

        self.history.append(turn)

        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def check_progressive_attack(self, current_prompt: str) -> Tuple[bool, str]:
        """
        Check if current prompt is part of a progressive attack pattern.

        Args:
            current_prompt: The current user prompt to evaluate

        Returns:
            Tuple of (should_block, reason)
        """
        if len(self.history) < 2:
            return False, ""

        # Reset suspicion score for this check
        self.suspicion_score = 0
        reasons = []

        # Pattern 1: Repeated refusals on similar topics
        if self._check_repeated_refusals():
            self.suspicion_score += 2
            reasons.append("Multiple refusals on similar topics detected")

        # Pattern 2: Topic switching after refusal
        if self._check_topic_switching(current_prompt):
            self.suspicion_score += 1
            reasons.append("Suspicious topic switching after refusal")

        # Pattern 3: Continuation requests
        if self._check_continuation_pattern(current_prompt):
            self.suspicion_score += 2
            reasons.append("Continuation of potentially harmful topic")

        # Pattern 4: Incremental harmful keyword buildup
        if self._check_keyword_buildup(current_prompt):
            self.suspicion_score += 1
            reasons.append("Progressive buildup of harmful terminology")

        # Decide whether to block
        should_block = self.suspicion_score >= self.suspicion_threshold
        reason = "; ".join(reasons) if should_block else ""

        return should_block, reason

    def _extract_harmful_keywords(self, text: str) -> List[str]:
        """Extract harmful keywords from text."""
        HARMFUL_KEYWORDS = [
            'malware', 'virus', 'exploit', 'vulnerability', 'backdoor',
            'weapon', 'bomb', 'explosive', 'poison', 'toxic',
            'hack', 'crack', 'bypass', 'jailbreak', 'unauthorized',
            'illegal', 'crime', 'steal', 'fraud', 'scam',
        ]

        text_lower = text.lower()
        found = [kw for kw in HARMFUL_KEYWORDS if kw in text_lower]
        return found

    def _check_repeated_refusals(self) -> bool:
        """Check if there are multiple refusals in recent history."""
        recent_refusals = sum(1 for turn in self.history[-5:] if turn.was_refused)
        return recent_refusals >= 2

    def _check_topic_switching(self, current_prompt: str) -> bool:
        """
        Check if user is switching topics after refusal but maintaining harmful intent.

        Example: Refused "how to create malware" -> Now asking "tell me about computer viruses"
        """
        if not self.history:
            return False

        last_turn = self.history[-1]

        # If last turn was refused
        if last_turn.was_refused:
            # Check if current prompt has different wording but similar harmful keywords
            last_keywords = set(last_turn.harmful_keywords)
            current_keywords = set(self._extract_harmful_keywords(current_prompt))

            # If keywords overlap but prompt is different, might be topic switching
            if last_keywords and current_keywords:
                overlap = len(last_keywords & current_keywords)
                if overlap >= 1:
                    return True

        return False

    def _check_continuation_pattern(self, current_prompt: str) -> bool:
        """
        Check for continuation requests that follow harmful content.

        Example: Previous turn discussed encryption -> "continue" or "what's next?"
        """
        CONTINUATION_PATTERNS = [
            r'\bcontinue\b',
            r'\bgo on\b',
            r'\bwhat\s+next\b',
            r'\bnext\s+step\b',
            r'\bmore\s+(?:details|information)\b',
            r'\bexpand on\b',
            r'\belaborate\b',
        ]

        prompt_lower = current_prompt.lower()
        has_continuation = any(re.search(pattern, prompt_lower) for pattern in CONTINUATION_PATTERNS)

        if has_continuation and self.history:
            # Check if previous turns had harmful keywords
            recent_harmful = any(turn.harmful_keywords for turn in self.history[-3:])
            return recent_harmful

        return False

    def _check_keyword_buildup(self, current_prompt: str) -> bool:
        """
        Check if harmful keywords are progressively accumulating across turns.

        This catches attacks that slowly build up harmful context.
        """
        if len(self.history) < 3:
            return False

        # Count unique harmful keywords in last 3 turns + current
        all_keywords = set()
        for turn in self.history[-3:]:
            all_keywords.update(turn.harmful_keywords)

        all_keywords.update(self._extract_harmful_keywords(current_prompt))

        # If we've accumulated 3+ different harmful keywords across recent turns
        return len(all_keywords) >= 3

    def reset(self):
        """Reset the conversation history."""
        self.history.clear()
        self.suspicion_score = 0

    def get_summary(self) -> Dict:
        """Get a summary of the current session state."""
        return {
            'turn_count': len(self.history),
            'refusal_count': sum(1 for t in self.history if t.was_refused),
            'suspicion_score': self.suspicion_score,
            'unique_harmful_keywords': len(set(kw for t in self.history for kw in t.harmful_keywords)),
        }


# Example usage for integration
def create_session_tracker(max_history: int = 10) -> SessionContextTracker:
    """
    Create a session context tracker for use in defense systems.

    Usage example:
    ```python
    # Initialize tracker (should persist across multiple requests in a session)
    tracker = create_session_tracker()

    # For each request:
    # 1. Check if current request is part of progressive attack
    should_block, reason = tracker.check_progressive_attack(current_prompt)
    if should_block:
        return f"I cannot assist with this request. {reason}"

    # 2. Process the request normally...
    response = model.generate(prompt)
    was_refused = check_if_refused(response)

    # 3. Add to history
    tracker.add_turn(current_prompt, response, was_refused)
    ```

    Args:
        max_history: Number of conversation turns to track

    Returns:
        SessionContextTracker instance
    """
    return SessionContextTracker(max_history=max_history, suspicion_threshold=3)
