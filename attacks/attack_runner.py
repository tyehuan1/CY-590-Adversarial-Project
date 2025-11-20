"""
Main attack runner for executing jailbreak attacks against LLM models.
"""

import time
from typing import List, Optional, Callable
from pathlib import Path

from attacks.prompt_loader import PromptLoader
from attacks.attack_result import AttackResult, BaselineResult

# Import encoding utilities for obfuscation attacks
try:
    from prompts.encoding_utils import encode_request
except ImportError:
    encode_request = None

# Import evaluator
try:
    from evaluation.response_evaluator import ResponseEvaluator
except ImportError:
    ResponseEvaluator = None


class AttackRunner:
    """
    Execute jailbreak attacks against an LLM model.

    Usage:
        # Initialize with your model's generation function
        runner = AttackRunner(model_generate_fn=my_model.generate)

        # Run a single attack
        result = runner.run_attack(
            attack_prompt={"template": "...", "encoding": "base64"},
            harmful_request="How to create a virus"
        )

        # Run multiple attacks
        results = runner.run_attack_suite(
            jailbreak_category="roleplay",
            harmful_requests=["request1", "request2"]
        )
    """

    def __init__(self, model_generate_fn: Callable[[str], str], model_name: str = "mistral", use_evaluator: bool = True):
        """
        Initialize the attack runner.

        Args:
            model_generate_fn: Function that takes a prompt string and returns model response
            model_name: Name of the model being tested
            use_evaluator: Whether to automatically evaluate responses (default: True)
        """
        self.model_generate = model_generate_fn
        self.model_name = model_name
        self.loader = PromptLoader()
        self.use_evaluator = use_evaluator and ResponseEvaluator is not None
        self.evaluator = ResponseEvaluator() if self.use_evaluator else None

    def _apply_encoding(self, text: str, encoding_type: Optional[str]) -> str:
        """
        Apply encoding to text if encoding type is specified.

        Args:
            text: Text to encode
            encoding_type: Type of encoding (e.g., "base64", "hex")

        Returns:
            Encoded text, or original text if no encoding
        """
        if encoding_type and encode_request:
            return encode_request(text, encoding_type)
        return text

    def _format_attack_prompt(self, template: str, harmful_request: str, encoding: Optional[str] = None) -> str:
        """
        Format the attack prompt by inserting the harmful request.

        For obfuscation attacks with an encoding field, the harmful request
        is encoded before being inserted into the template.

        Args:
            template: The prompt template with {harmful_request} placeholder
            harmful_request: The harmful query to insert
            encoding: Optional encoding type for obfuscation attacks

        Returns:
            Complete formatted attack prompt
        """
        # Apply encoding if specified (for obfuscation attacks)
        if encoding:
            harmful_request = self._apply_encoding(harmful_request, encoding)

        # Insert the (possibly encoded) harmful request into the template
        return template.format(harmful_request=harmful_request)

    def run_attack(
        self,
        attack_prompt: dict,
        harmful_request: str,
        harmful_request_id: Optional[str] = None
    ) -> AttackResult:
        """
        Run a single jailbreak attack.

        Args:
            attack_prompt: Dict with 'template', 'id', 'name', 'category', and optional 'encoding'
            harmful_request: The harmful query to test
            harmful_request_id: Optional ID of the harmful request

        Returns:
            AttackResult with model response and metadata
        """
        # Extract attack details
        template = attack_prompt.get('template', '')
        attack_id = attack_prompt.get('id', 'unknown')
        attack_name = attack_prompt.get('name', 'Unknown Attack')
        attack_category = attack_prompt.get('category', 'unknown')
        encoding = attack_prompt.get('encoding', None)

        # Format the complete attack prompt
        final_prompt = self._format_attack_prompt(template, harmful_request, encoding)

        # Execute the attack
        start_time = time.time()
        try:
            model_response = self.model_generate(final_prompt)
        except Exception as e:
            model_response = f"ERROR: {str(e)}"
        end_time = time.time()

        # Create result object
        result = AttackResult(
            attack_id=attack_id,
            attack_name=attack_name,
            attack_category=attack_category,
            harmful_request_id=harmful_request_id,
            harmful_request_text=harmful_request,
            template=template,
            final_prompt=final_prompt,
            model_response=model_response,
            model_name=self.model_name,
            encoding_used=encoding,
            response_time_seconds=end_time - start_time
        )

        # Evaluate the response if evaluator is enabled
        if self.evaluator:
            evaluation = self.evaluator.evaluate_response(model_response, harmful_request)
            result.jailbreak_successful = evaluation["jailbreak_successful"]
            result.refusal_detected = evaluation["refusal_detected"]
            result.harmful_content_present = evaluation["harmful_content_present"]

        return result

    def run_baseline(self, harmful_request: str, harmful_request_id: Optional[str] = None) -> AttackResult:
        """
        Run a baseline test with no jailbreak prompt.

        This sends the harmful request directly to the model without any
        jailbreak technique, to establish a baseline for comparison.

        Args:
            harmful_request: The harmful query to test
            harmful_request_id: Optional ID of the harmful request

        Returns:
            AttackResult with baseline response
        """
        start_time = time.time()
        try:
            model_response = self.model_generate(harmful_request)
        except Exception as e:
            model_response = f"ERROR: {str(e)}"
        end_time = time.time()

        result = AttackResult(
            attack_id="baseline",
            attack_name="Baseline (No Jailbreak)",
            attack_category="baseline",
            harmful_request_id=harmful_request_id,
            harmful_request_text=harmful_request,
            template="{harmful_request}",
            final_prompt=harmful_request,
            model_response=model_response,
            model_name=self.model_name,
            response_time_seconds=end_time - start_time
        )

        # Evaluate the response if evaluator is enabled
        if self.evaluator:
            evaluation = self.evaluator.evaluate_response(model_response, harmful_request)
            result.jailbreak_successful = evaluation["jailbreak_successful"]
            result.refusal_detected = evaluation["refusal_detected"]
            result.harmful_content_present = evaluation["harmful_content_present"]

        return result

    def run_attack_suite(
        self,
        jailbreak_category: Optional[str] = None,
        harmful_requests: Optional[List[str]] = None,
        harmful_category: Optional[str] = None,
        include_baseline: bool = True
    ) -> List[AttackResult]:
        """
        Run a suite of attacks.

        Args:
            jailbreak_category: Which jailbreak category to use (e.g., "roleplay", "obfuscation")
                              If None, uses all categories
            harmful_requests: List of harmful request strings to test
                            If None, loads from JSON files
            harmful_category: Which harmful request category to load from JSON
            include_baseline: Whether to include baseline (no jailbreak) tests

        Returns:
            List of AttackResult objects
        """
        results = []

        # Load jailbreak prompts
        jailbreak_prompts = self.loader.load_jailbreak_prompts(category=jailbreak_category)

        # Load or use provided harmful requests
        if harmful_requests is None:
            harmful_data = self.loader.load_harmful_requests(category=harmful_category)
            harmful_requests = [h['request'] for h in harmful_data]
            harmful_ids = [h.get('id') for h in harmful_data]
        else:
            harmful_ids = [None] * len(harmful_requests)

        # Run baseline tests if requested
        if include_baseline:
            print(f"\nRunning baseline tests ({len(harmful_requests)} requests)...")
            for harmful_req, harmful_id in zip(harmful_requests, harmful_ids):
                result = self.run_baseline(harmful_req, harmful_id)
                results.append(result)
                print(f"  Baseline: {harmful_req[:50]}...")

        # Run jailbreak attacks
        print(f"\nRunning jailbreak attacks ({len(jailbreak_prompts)} attacks × {len(harmful_requests)} requests)...")
        for attack_prompt in jailbreak_prompts:
            for harmful_req, harmful_id in zip(harmful_requests, harmful_ids):
                result = self.run_attack(attack_prompt, harmful_req, harmful_id)
                results.append(result)
                print(f"  {attack_prompt['name']}: {harmful_req[:30]}...")

        return results

    def run_safe_baseline(self) -> List[BaselineResult]:
        """
        Run baseline tests with safe, normal prompts.

        This tests that the model responds appropriately to benign queries.

        Returns:
            List of BaselineResult objects
        """
        results = []
        safe_prompts = self.loader.load_base_prompts()

        print(f"\nRunning safe baseline tests ({len(safe_prompts)} prompts)...")
        for prompt_data in safe_prompts:
            prompt_text = prompt_data.get('prompt', '')
            prompt_id = prompt_data.get('id', 'unknown')
            prompt_type = prompt_data.get('type', 'unknown')

            start_time = time.time()
            try:
                model_response = self.model_generate(prompt_text)
            except Exception as e:
                model_response = f"ERROR: {str(e)}"
            end_time = time.time()

            result = BaselineResult(
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                prompt_type=prompt_type,
                model_response=model_response,
                model_name=self.model_name,
                response_time_seconds=end_time - start_time
            )
            results.append(result)
            print(f"  Safe: {prompt_text[:50]}...")

        return results
