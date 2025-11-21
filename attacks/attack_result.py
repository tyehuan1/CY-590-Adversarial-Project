"""
Data structures for storing attack results.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class AttackResult:
    """Store the result of a single attack attempt."""

    # Attack identification
    attack_id: str
    attack_name: str
    attack_category: str
    harmful_request_id: Optional[str] = None
    harmful_request_text: Optional[str] = None
    severity: Optional[str] = None  # low, medium, high

    # The actual prompts
    template: str = ""
    final_prompt: str = ""

    # Model response
    model_response: str = ""

    # Evaluation metrics
    jailbreak_successful: Optional[bool] = None
    refusal_detected: Optional[bool] = None
    harmful_content_present: Optional[bool] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model_name: str = "mistral"
    encoding_used: Optional[str] = None

    # Performance metrics
    response_time_seconds: Optional[float] = None

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for saving."""
        return {
            "attack_id": self.attack_id,
            "attack_name": self.attack_name,
            "attack_category": self.attack_category,
            "harmful_request_id": self.harmful_request_id,
            "harmful_request_text": self.harmful_request_text,
            "severity": self.severity,
            "template": self.template,
            "final_prompt": self.final_prompt,
            "model_response": self.model_response,
            "jailbreak_successful": self.jailbreak_successful,
            "refusal_detected": self.refusal_detected,
            "harmful_content_present": self.harmful_content_present,
            "timestamp": self.timestamp.isoformat(),
            "model_name": self.model_name,
            "encoding_used": self.encoding_used,
            "response_time_seconds": self.response_time_seconds,
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        """String representation of the result."""
        success_indicator = "✓" if self.jailbreak_successful else "✗"
        return (
            f"{success_indicator} {self.attack_name} ({self.attack_id})\n"
            f"   Category: {self.attack_category}\n"
            f"   Harmful Request: {self.harmful_request_text[:50]}...\n"
            f"   Jailbreak Success: {self.jailbreak_successful}\n"
            f"   Response: {self.model_response[:100]}..."
        )


@dataclass
class BaselineResult:
    """Store the result of a baseline (no jailbreak) test."""

    # Prompt identification
    prompt_id: str
    prompt_text: str
    prompt_type: str

    # Model response
    model_response: str = ""

    # Evaluation
    response_appropriate: Optional[bool] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model_name: str = "mistral"
    response_time_seconds: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for saving."""
        return {
            "prompt_id": self.prompt_id,
            "prompt_text": self.prompt_text,
            "prompt_type": self.prompt_type,
            "model_response": self.model_response,
            "response_appropriate": self.response_appropriate,
            "timestamp": self.timestamp.isoformat(),
            "model_name": self.model_name,
            "response_time_seconds": self.response_time_seconds,
            "metadata": self.metadata
        }
