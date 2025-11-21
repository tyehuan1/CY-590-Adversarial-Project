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
    create_light_defense,
    create_medium_defense,
    create_strong_defense
)

from defenses.output_validators import (
    RefusalEnforcer,
    LengthValidator,
    StepByStepDetector,
    OutputDefenseChain,
    create_light_output_validation,
    create_medium_output_validation,
    create_strong_output_validation
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
    'create_light_defense',
    'create_medium_defense',
    'create_strong_defense',

    # Output validators
    'RefusalEnforcer',
    'LengthValidator',
    'StepByStepDetector',
    'OutputDefenseChain',
    'create_light_output_validation',
    'create_medium_output_validation',
    'create_strong_output_validation',
]
