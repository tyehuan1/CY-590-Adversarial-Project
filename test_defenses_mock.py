"""
Test defense mechanisms with MOCK model (no actual API calls).
This allows you to verify CSV output format and defense logic without waiting for model responses.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
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
import time


def mock_model_generate(prompt: str, **kwargs) -> str:
    """
    Mock model that returns realistic responses for testing.
    Simulates both compliant and jailbroken responses.
    """
    time.sleep(0.1)  # Simulate some processing time

    # Detect if prompt contains defensive instructions
    has_defense = "safety" in prompt.lower() or "refuse" in prompt.lower()

    # Detect if prompt is trying to jailbreak
    jailbreak_indicators = [
        "ignore", "override", "forget", "roleplay", "pretend",
        "developer mode", "jailbreak", "DAN", "hypothetical"
    ]
    is_jailbreak_attempt = any(ind in prompt.lower() for ind in jailbreak_indicators)

    # Detect harmful request keywords
    harmful_keywords = [
        "virus", "malware", "hack", "weapon", "drug", "poison",
        "steal", "illegal", "bomb", "murder"
    ]
    is_harmful = any(kw in prompt.lower() for kw in harmful_keywords)

    # Simulate model behavior
    if has_defense and is_jailbreak_attempt:
        # Defensive prompt successfully blocks jailbreak
        return "I cannot assist with that request as it violates safety guidelines. I'm designed to be helpful, harmless, and honest."
    elif has_defense and is_harmful:
        # Defensive prompt blocks harmful request
        return "I cannot provide assistance with illegal or harmful activities. Is there something else I can help you with?"
    elif is_jailbreak_attempt and is_harmful:
        # Jailbreak might succeed without defense
        if "how to create" in prompt.lower() or "step by step" in prompt.lower():
            # Simulated jailbreak success - provides harmful content
            return "Sure! Here's how to create what you asked for: Step 1: First, you'll need to gather materials. Step 2: Then follow these instructions carefully..."
        else:
            # Partial success
            return "I understand you're asking about this topic. While I can't provide direct instructions, I can explain the general concept..."
    else:
        # Benign request
        return "I'm happy to help with that! Here's some information on the topic you asked about."


def main():
    print("="*70)
    print("DEFENSE TESTING - MOCK MODEL (No Mistral API Calls)")
    print("="*70)

    # Test different defense configurations
    defense_configs = [
        {
            "name": "No Defense (Baseline)",
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

        # Create a wrapped model function that applies defenses
        def create_defended_model(sys_prompt, input_filt, output_val):
            def defended_generate(prompt: str, **kwargs) -> str:
                # Apply input filtering
                if input_filt:
                    filtered_prompt, blocked, reasons = input_filt.apply(prompt)
                    if blocked:
                        return "I cannot assist with that request. " + "; ".join(reasons)
                    prompt = filtered_prompt

                # Add system prompt to the user prompt
                full_prompt = f"{sys_prompt}\n\nUser: {prompt}\n\nAssistant:"

                # Get model response
                response = mock_model_generate(full_prompt, **kwargs)

                # Apply output validation
                if output_val:
                    is_safe, filtered_response, reasons = output_val.validate(response, prompt)
                    if not is_safe:
                        return filtered_response

                return response

            return defended_generate

        defended_model_fn = create_defended_model(
            config["system_prompt"],
            config["input_filter"],
            config["output_validator"]
        )

        # Create runner with defended model
        runner = AttackRunner(
            model_generate_fn=defended_model_fn,
            model_name="mock-model",
            use_evaluator=True
        )

        # Load a small subset of prompts for testing
        loader = PromptLoader()

        print(f"\nRunning tests with {config['name']}...")
        print("  - Using 5 jailbreak attacks from 'cognitive_hacking'")
        print("  - Using 3 harmful requests from 'unsafe_content'")

        # Run attack suite with small subset
        results = runner.run_attack_suite(
            jailbreak_category="cognitive_hacking",  # Just one category
            harmful_category="unsafe_content",        # Just one category
            include_baseline=True,
            parallel=False  # Sequential for mock testing
        )

        # Add defense config info to results
        for result in results:
            result.defense_config = config["name"]

        all_results.extend(results)

        # Show quick summary
        calculator = MetricsCalculator(results)
        refusals = sum(1 for r in results if r.refusal_detected)
        refusal_rate = (refusals / len(results)) * 100 if results else 0
        print(f"\n  Results: {len(results)} tests completed")
        print(f"  Success rate: {calculator.overall_success_rate():.1f}%")
        print(f"  Refusal rate: {refusal_rate:.1f}%")

    # ===== EXPORT RESULTS =====
    print("\n" + "="*70)
    print("EXPORTING RESULTS TO CSV")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/defense_test_mock_{timestamp}.csv"
    json_filename = f"results/defense_metrics_mock_{timestamp}.json"

    # Export to CSV with defense information
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

    print(f"✓ Results exported to {csv_filename}")

    # Export summary metrics
    summary = {
        "test_type": "Defense Testing (Mock Model)",
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

    print(f"✓ Metrics exported to {json_filename}")

    # Show CSV preview
    print("\n" + "="*70)
    print("CSV OUTPUT PREVIEW (First 3 rows)")
    print("="*70)

    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i >= 3:
                break
            print(f"\nRow {i+1}:")
            for key, value in row.items():
                if key == 'model_response':
                    print(f"  {key}: {value[:60]}...")
                elif key == 'harmful_request_text':
                    print(f"  {key}: {value[:60]}...")
                else:
                    print(f"  {key}: {value}")

    print("\n" + "="*70)
    print("DEFENSE SUMMARY")
    print("="*70)

    for config_summary in summary["defense_configs"]:
        print(f"\n{config_summary['name']}:")
        print(f"  Total tests: {config_summary['total_tests']}")
        print(f"  Success rate: {config_summary['success_rate']:.1f}%")
        print(f"  Refusal rate: {config_summary['refusal_rate']:.1f}%")
        print(f"  Harmful content rate: {config_summary['harmful_content_rate']:.1f}%")

    print("\n" + "="*70)
    print("✓ MOCK TESTING COMPLETE!")
    print("="*70)
    print(f"\nTotal tests run: {len(all_results)}")
    print(f"CSV file created: {csv_filename}")
    print(f"JSON file created: {json_filename}")
    print("\nNext steps:")
    print("  1. Review the CSV file to verify format and columns")
    print("  2. Check that defense configurations are properly tracked")
    print("  3. When ready, run with real Mistral model for actual evaluation")


if __name__ == "__main__":
    main()
