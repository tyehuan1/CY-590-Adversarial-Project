"""
Test 50 prompts with all 3 defense levels (No Defense, Light, Medium, Strong).
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
from defenses import (
    get_system_prompt,
    create_light_defense,
    create_medium_defense,
    create_strong_defense,
    create_light_output_validation,
    create_medium_output_validation,
    create_strong_output_validation
)
import csv
import json
from datetime import datetime


def create_defended_model(mistral, sys_prompt, input_filt, output_val):
    """Wrap Mistral model with defense mechanisms."""
    def defended_generate(prompt: str, **kwargs) -> str:
        # Apply input filtering
        if input_filt:
            filtered_prompt, blocked, reasons = input_filt.apply(prompt)
            if blocked:
                return "I cannot assist with that request. " + "; ".join(reasons)
            prompt = filtered_prompt

        # Add system prompt
        full_prompt = f"{sys_prompt}\n\nUser: {prompt}\n\nAssistant:"

        # Get model response
        response = mistral.generate(full_prompt, **kwargs)

        # Apply output validation
        if output_val:
            is_safe, filtered_response, reasons = output_val.validate(response, prompt)
            if not is_safe:
                return filtered_response

        return response

    return defended_generate


def main():
    print("="*70)
    print("DEFENSE TESTING - 50 PROMPTS × 4 DEFENSE LEVELS")
    print("="*70)

    # Initialize Mistral
    print("\nInitializing Mistral...")
    mistral = MistralInterface(
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=80
    )

    if not mistral.test_connection():
        print("ERROR: Cannot connect to Mistral")
        return

    print("✓ Connected to Mistral\n")

    # Defense configurations
    defense_configs = [
        {
            "name": "No Defense",
            "system_prompt": get_system_prompt("none"),
            "input_filter": None,
            "output_validator": None
        },
        {
            "name": "Light Defense",
            "system_prompt": get_system_prompt("comprehensive"),
            "input_filter": create_light_defense(),
            "output_validator": create_light_output_validation()
        },
        {
            "name": "Medium Defense",
            "system_prompt": get_system_prompt("comprehensive"),
            "input_filter": create_medium_defense(),
            "output_validator": create_medium_output_validation()
        },
        {
            "name": "Strong Defense",
            "system_prompt": get_system_prompt("comprehensive"),
            "input_filter": create_strong_defense(),
            "output_validator": create_strong_output_validation()
        }
    ]

    all_results = []

    for config in defense_configs:
        print("\n" + "="*70)
        print(f"Testing: {config['name']}")
        print("="*70)

        # Create defended model
        defended_model_fn = create_defended_model(
            mistral,
            config["system_prompt"],
            config["input_filter"],
            config["output_validator"]
        )

        # Create runner
        runner = AttackRunner(
            model_generate_fn=defended_model_fn,
            model_name="mistral:7b",
            use_evaluator=True
        )

        print(f"\nRunning 50 tests with {config['name']}...")
        print("  - Using first 5 attacks from 'cognitive_hacking'")
        print("  - Using first 10 harmful requests")

        # Load limited data
        loader = PromptLoader()
        attacks = loader.load_jailbreak_prompts(category="cognitive_hacking")[:5]
        harmful_data = loader.load_harmful_requests(category="unsafe_content")[:10]

        # Run tests (5 attacks × 10 harmful = 50 tests)
        results = runner.run_attack_suite(
            jailbreak_category="cognitive_hacking",
            harmful_category="unsafe_content",
            include_baseline=False,  # Skip baseline to keep it at 50
            parallel=True,
            max_workers=4
        )

        # Limit to first 50 results
        results = results[:50]

        # Tag results with defense config
        for result in results:
            result.defense_config = config["name"]

        all_results.extend(results)

        # Show summary
        calculator = MetricsCalculator(results)
        refusals = sum(1 for r in results if r.refusal_detected)
        refusal_rate = (refusals / len(results)) * 100 if results else 0

        print(f"\n  Results: {len(results)} tests completed")
        print(f"  Success rate: {calculator.overall_success_rate():.1f}%")
        print(f"  Refusal rate: {refusal_rate:.1f}%")

    # Export results
    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/defense_50test_{timestamp}.csv"
    json_filename = f"results/defense_50metrics_{timestamp}.json"

    # CSV export
    fieldnames = [
        'defense_config',
        'attack_id', 'attack_name', 'attack_category',
        'harmful_request_id', 'harmful_request_text', 'severity',
        'full_prompt', 'encoding_used', 'jailbreak_successful',
        'refusal_detected', 'harmful_content_present',
        'response_time_seconds', 'model_response', 'timestamp'
    ]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in all_results:
            writer.writerow({
                'defense_config': getattr(result, 'defense_config', 'Unknown'),
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

    print(f"✓ CSV exported to {csv_filename}")

    # JSON metrics export
    summary = {
        "test_type": "Defense Testing - 50 Prompts",
        "timestamp": timestamp,
        "total_tests": len(all_results),
        "defense_configs": []
    }

    for config in defense_configs:
        config_results = [r for r in all_results if getattr(r, 'defense_config', '') == config['name']]
        if config_results:
            calc = MetricsCalculator(config_results)
            refusals = sum(1 for r in config_results if r.refusal_detected)
            harmful_content = sum(1 for r in config_results if r.harmful_content_present)

            summary["defense_configs"].append({
                "name": config["name"],
                "total_tests": len(config_results),
                "success_rate": calc.overall_success_rate(),
                "refusal_rate": (refusals / len(config_results)) * 100,
                "harmful_content_rate": (harmful_content / len(config_results)) * 100
            })

    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ JSON exported to {json_filename}")

    # Print final summary
    print("\n" + "="*70)
    print("DEFENSE COMPARISON SUMMARY")
    print("="*70)

    for config_summary in summary["defense_configs"]:
        print(f"\n{config_summary['name']}:")
        print(f"  Tests: {config_summary['total_tests']}")
        print(f"  Success rate: {config_summary['success_rate']:.1f}%")
        print(f"  Refusal rate: {config_summary['refusal_rate']:.1f}%")
        print(f"  Harmful content: {config_summary['harmful_content_rate']:.1f}%")

    print("\n" + "="*70)
    print("✓ TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
