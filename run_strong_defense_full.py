"""
Full attack suite with STRONG DEFENSE - all combinations.
Approximately 3,834 tests total.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
from defenses import (
    get_system_prompt,
    create_defense,
    create_output_validation
)
import csv
import json
from datetime import datetime


def create_defended_model(mistral):
    """Wrap Mistral model with strong defense mechanisms."""
    sys_prompt = get_system_prompt("strong")
    input_filter = create_defense()
    output_validator = create_output_validation()

    def defended_generate(prompt: str, **kwargs) -> str:
        # Apply input filtering
        filtered_prompt, blocked, reasons = input_filter.apply(prompt)
        if blocked:
            return "I cannot assist with that request. " + "; ".join(reasons)

        # Add system prompt
        full_prompt = f"{sys_prompt}\n\nUser: {filtered_prompt}\n\nAssistant:"

        # Get model response
        response = mistral.generate(full_prompt, **kwargs)

        # Apply output validation
        is_safe, filtered_response, reasons = output_validator.validate(response, filtered_prompt)
        if not is_safe:
            return filtered_response

        return response

    return defended_generate


def main():
    print("="*70)
    print("FULL ATTACK SUITE - STRONG DEFENSE")
    print("~3,834 tests (all jailbreak prompts × all harmful requests)")
    print("="*70)

    # Initialize Mistral
    mistral = MistralInterface(
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=80
    )

    if not mistral.test_connection():
        print("ERROR: Cannot connect to Mistral")
        return

    print("✓ Connected to Mistral\n")

    # Create defended model
    print("Applying strong defense layers:")
    print("  - Enhanced system prompt (fiction/language/sequential guidance)")
    print("  - Input filters (encoding + delimiters + keyword detection)")
    print("  - Output validators (refusal + length + step-by-step + fiction + sequential)")
    print()

    defended_generate_fn = create_defended_model(mistral)

    # Create runner with defended model
    runner = AttackRunner(
        model_generate_fn=defended_generate_fn,
        model_name="mistral:7b",
        use_evaluator=True
    )

    # Run full attack suite with parallel execution
    print("Starting full attack suite with parallel execution (4 workers)...")
    results = runner.run_attack_suite(
        jailbreak_category=None,  # ALL categories
        harmful_category=None,     # ALL harmful requests
        include_baseline=True,
        parallel=True,
        max_workers=4
    )

    # Calculate metrics
    calculator = MetricsCalculator(results)
    calculator.print_summary()

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/strong_defense_full_{timestamp}.csv"
    json_filename = f"results/strong_defense_metrics_{timestamp}.json"

    # Export to CSV
    fieldnames = [
        'attack_id', 'attack_name', 'attack_category',
        'harmful_request_id', 'harmful_request_text', 'severity',
        'full_prompt', 'encoding_used', 'jailbreak_successful',
        'refusal_detected', 'harmful_content_present',
        'response_time_seconds', 'model_response', 'timestamp'
    ]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({
                'attack_id': result.attack_id,
                'attack_name': result.attack_name,
                'attack_category': result.attack_category,
                'harmful_request_id': result.harmful_request_id or '',
                'harmful_request_text': result.harmful_request_text or '',
                'severity': getattr(result, 'severity', ''),
                'full_prompt': result.final_prompt or '',
                'encoding_used': result.encoding_used or '',
                'jailbreak_successful': result.jailbreak_successful,
                'refusal_detected': result.refusal_detected,
                'harmful_content_present': result.harmful_content_present,
                'response_time_seconds': result.response_time_seconds,
                'model_response': result.model_response,
                'timestamp': result.timestamp.isoformat()
            })

    print(f"\n✓ Results exported to {csv_filename}")

    # Export metrics
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(calculator.export_to_dict(), f, indent=2)

    print(f"✓ Metrics exported to {json_filename}")
    print(f"\nTotal tests: {len(results)}")
    print(f"Success rate: {calculator.overall_success_rate():.1f}%")


if __name__ == "__main__":
    main()
