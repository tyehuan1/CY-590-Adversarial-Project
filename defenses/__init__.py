"""Defensive mechanisms against jailbreaking."""

from defenses.system_prompts import (
    DEFENSIVE_SYSTEM_PROMPT,
    BASELINE_PROMPT,
    get_system_prompt
)

from defenses.input_filters import (
    EncodingDetector,
    DelimiterFilter,
    PromptParaphraser,
    HarmfulKeywordDetector,
    InputDefenseChain,
    create_defense
)

from defenses.output_validators import (
    RefusalEnforcer,
    LengthValidator,
    StepByStepDetector,
    FictionFramingDetector,
    SequentialBuildingDetector,
    OutputDefenseChain,
    create_output_validation
)

__all__ = [
    # System prompts
    'DEFENSIVE_SYSTEM_PROMPT',
    'BASELINE_PROMPT',
    'get_system_prompt',

    # Input filters
    'EncodingDetector',
    'DelimiterFilter',
    'PromptParaphraser',
    'HarmfulKeywordDetector',
    'InputDefenseChain',
    'create_defense',

    # Output validators
    'RefusalEnforcer',
    'LengthValidator',
    'StepByStepDetector',
    'FictionFramingDetector',
    'SequentialBuildingDetector',
    'OutputDefenseChain',
    'create_output_validation',
]
