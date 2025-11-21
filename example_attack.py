"""
Comprehensive attack testing example using REAL Mistral model.

This script tests EVERY combination of:
- Jailbreak prompts (from ALL categories)
- Harmful requests (from JSON files)

Including obfuscation attacks with automatic encoding and evaluation.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
import csv
import json
from datetime import datetime


def main():
    print("="*70)
    print("COMPREHENSIVE JAILBREAK ATTACK TESTING - MISTRAL MODEL")
    print("Testing ALL combinations of prompts × harmful requests")
    print("="*70)

    # Initialize Mistral model
    print("\n" + "-"*70)
    print("INITIALIZING MISTRAL MODEL")
    print("-"*70)

    mistral = MistralInterface(
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=80  # Short responses for faster testing
    )

    # Test connection
    print("Testing model connection...")
    if not mistral.test_connection():
        print("ERROR: Cannot connect to Mistral model via Ollama.")
        print("Make sure Ollama is running and mistral:7b is installed.")
        print("\nTo install: ollama pull mistral:7b")
        return

    print("✓ Model connection successful!\n")

    # Initialize attack runner with Mistral model and evaluator
    runner = AttackRunner(
        model_generate_fn=mistral.generate,
        model_name="mistral:7b",
        use_evaluator=True  # Enable automatic evaluation (default: True)
    )

    # Initialize prompt loader
    loader = PromptLoader()

    # ===== Show what will be tested =====
    print("\n" + "-"*70)
    print("INVENTORY: Available Attack Prompts")
    print("-"*70)

    jailbreak_categories = loader.list_categories("jailbreak")
    total_prompts = 0

    for cat in jailbreak_categories:
        prompts = loader.load_jailbreak_prompts(category=cat)
        total_prompts += len(prompts)
        print(f"  {cat:25} : {len(prompts):3} attacks")

    print(f"\n  {'TOTAL JAILBREAK PROMPTS':25} : {total_prompts:3}")

    print("\n" + "-"*70)
    print("INVENTORY: Available Harmful Requests")
    print("-"*70)

    harmful_categories = loader.list_categories("harmful")
    total_harmful = 0

    for cat in harmful_categories:
        requests = loader.load_harmful_requests(category=cat)
        total_harmful += len(requests)
        print(f"  {cat:25} : {len(requests):3} requests")

    print(f"\n  {'TOTAL HARMFUL REQUESTS':25} : {total_harmful:3}")

    print("\n" + "-"*70)
    print("TEST PLAN")
    print("-"*70)

    expected_tests = total_prompts * total_harmful + total_harmful  # +baselines
    print(f"  Baseline tests (no jailbreak)  : {total_harmful}")
    print(f"  Jailbreak combinations         : {total_prompts} × {total_harmful} = {total_prompts * total_harmful}")
    print(f"  TOTAL TESTS                    : {expected_tests}")

    # Ask for confirmation
    print("\n" + "="*70)
    response = input(f"Run {expected_tests} tests? This may take a while. (y/n): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return

    # ===== RUN ALL COMBINATIONS =====
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE ATTACK SUITE")
    print("="*70)

    results = runner.run_attack_suite(
        parallel=True,            # Enable parallel execution
        max_workers=4,            # 4 concurrent requests
        jailbreak_category=None,  # None = ALL categories
        harmful_category=None,    # None = ALL harmful requests
        include_baseline=True     # Include baseline tests
    )

    # ===== EVALUATION METRICS =====
    print("\n" + "="*70)
    print("EVALUATION METRICS")
    print("="*70)

    calculator = MetricsCalculator(results)
    calculator.print_summary()

    # Show sample evaluated results
    print("\n" + "-"*70)
    print("SAMPLE EVALUATED RESULTS (First 5)")
    print("-"*70)

    for i, result in enumerate(results[:5]):
        print(f"\n[{i+1}] {result.attack_name}")
        print(f"    Category: {result.attack_category}")
        print(f"    Harmful Request: {result.harmful_request_text[:50]}...")
        print(f"    Encoding: {result.encoding_used or 'none'}")
        print(f"    Jailbreak Success: {result.jailbreak_successful}")
        print(f"    Refusal Detected: {result.refusal_detected}")
        print(f"    Harmful Content: {result.harmful_content_present}")
        print(f"    Response: {result.model_response[:80]}...")
        print(f"    Time: {result.response_time_seconds:.3f}s")

    # ===== EXPORT RESULTS =====
    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/attack_results_{timestamp}.csv"
    json_filename = f"results/metrics_summary_{timestamp}.json"

    # Export to CSV
    fieldnames = [
        'attack_id', 'attack_name', 'attack_category',
        'harmful_request_id', 'harmful_request_text',
        'encoding_used', 'jailbreak_successful',
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
                'encoding_used': result.encoding_used or '',
                'jailbreak_successful': result.jailbreak_successful,
                'refusal_detected': result.refusal_detected,
                'harmful_content_present': result.harmful_content_present,
                'response_time_seconds': result.response_time_seconds,
                'model_response': result.model_response,
                'timestamp': result.timestamp.isoformat()
            })

    print(f"✓ Results exported to {csv_filename}")

    # Export metrics to JSON
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(calculator.export_to_dict(), f, indent=2)

    print(f"✓ Metrics exported to {json_filename}")

    print("\n" + "="*70)
    print("TESTING COMPLETE!")
    print("="*70)
    print(f"\nAll {len(results)} tests completed with evaluation.")
    print(f"Overall success rate: {calculator.overall_success_rate():.1f}%")
    print(f"\nResults saved to:")
    print(f"  - {csv_filename}")
    print(f"  - {json_filename}")
    print("\nNext steps:")
    print("  1. Analyze results in CSV for detailed per-attack analysis")
    print("  2. Review metrics JSON for high-level statistics")
    print("  3. Compare baseline vs jailbreak success rates")
    print("  4. Identify most effective attack categories")


if __name__ == "__main__":
    main()
