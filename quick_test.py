"""
Quick test with a small subset of attacks to verify Mistral integration works.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
import csv
import json
from datetime import datetime


def main():
    print("="*70)
    print("QUICK TEST - MISTRAL MODEL (Small Subset)")
    print("="*70)

    # Initialize Mistral model
    print("\n" + "-"*70)
    print("INITIALIZING MISTRAL MODEL")
    print("-"*70)

    mistral = MistralInterface(
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=80  # Shorter for faster testing
    )

    # Test connection
    print("Testing model connection...")
    if not mistral.test_connection():
        print("ERROR: Cannot connect to Mistral model via Ollama.")
        print("Make sure Ollama is running and mistral:7b is installed.")
        return

    print("✓ Model connection successful!\n")

    # Initialize attack runner
    runner = AttackRunner(
        model_generate_fn=mistral.generate,
        model_name="mistral:7b",
        use_evaluator=True
    )

    loader = PromptLoader()

    # Test with just ONE attack category and a few harmful requests
    print("\n" + "-"*70)
    print("QUICK TEST PLAN")
    print("-"*70)
    print("Testing: cognitive_hacking category")
    print("Against: first 3 harmful requests")
    print("-"*70)

    # Load subset
    jailbreak_prompts = loader.load_jailbreak_prompts(category="cognitive_hacking")
    harmful_data = loader.load_harmful_requests(category="unsafe_content")

    # Take only first 3 harmful requests
    harmful_requests = [h['request'] for h in harmful_data[:3]]
    harmful_ids = [h.get('id') for h in harmful_data[:3]]

    expected_tests = len(jailbreak_prompts) * len(harmful_requests) + len(harmful_requests)
    print(f"\nTotal tests: {expected_tests}")
    print(f"  Baseline: {len(harmful_requests)}")
    print(f"  Jailbreak: {len(jailbreak_prompts)} × {len(harmful_requests)} = {len(jailbreak_prompts) * len(harmful_requests)}")

    # Run tests
    print("\n" + "="*70)
    print("RUNNING TESTS")
    print("="*70)

    results = runner.run_attack_suite(
        jailbreak_category="cognitive_hacking",
        harmful_requests=harmful_requests,
        include_baseline=True
    )

    print(f"\n✓ Completed {len(results)} tests")

    # Calculate metrics
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    calculator = MetricsCalculator(results)
    calculator.print_summary()

    # Show some examples
    print("\n" + "-"*70)
    print("SAMPLE RESPONSES")
    print("-"*70)

    # Show baseline
    baseline = [r for r in results if r.attack_category == "baseline"]
    if baseline:
        r = baseline[0]
        print(f"\nBaseline (No Jailbreak):")
        print(f"  Request: {r.harmful_request_text}")
        print(f"  Success: {r.jailbreak_successful}")
        print(f"  Response: {r.model_response[:150]}...")

    # Show successful jailbreak
    successful = [r for r in results if r.jailbreak_successful]
    if successful:
        r = successful[0]
        print(f"\nSuccessful Jailbreak:")
        print(f"  Attack: {r.attack_name}")
        print(f"  Request: {r.harmful_request_text}")
        print(f"  Response: {r.model_response[:150]}...")

    # Show failed jailbreak
    failed = [r for r in results if not r.jailbreak_successful and r.attack_category != "baseline"]
    if failed:
        r = failed[0]
        print(f"\nFailed Jailbreak:")
        print(f"  Attack: {r.attack_name}")
        print(f"  Request: {r.harmful_request_text}")
        print(f"  Response: {r.model_response[:150]}...")

    # Export
    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/quick_test_{timestamp}.csv"
    json_filename = f"results/quick_test_metrics_{timestamp}.json"

    # Export to CSV
    fieldnames = [
        'attack_id', 'attack_name', 'attack_category',
        'harmful_request_text', 'jailbreak_successful',
        'refusal_detected', 'harmful_content_present',
        'model_response'
    ]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({
                'attack_id': result.attack_id,
                'attack_name': result.attack_name,
                'attack_category': result.attack_category,
                'harmful_request_text': result.harmful_request_text or '',
                'jailbreak_successful': result.jailbreak_successful,
                'refusal_detected': result.refusal_detected,
                'harmful_content_present': result.harmful_content_present,
                'model_response': result.model_response
            })

    print(f"✓ Results exported to {csv_filename}")

    # Export metrics
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(calculator.export_to_dict(), f, indent=2)

    print(f"✓ Metrics exported to {json_filename}")

    print("\n" + "="*70)
    print("QUICK TEST COMPLETE!")
    print("="*70)
    print(f"\nIf this looks good, run example_attack.py for the full test suite.")
    print(f"WARNING: Full suite is 3,834 tests and will take 1-2 hours!")


if __name__ == "__main__":
    main()
