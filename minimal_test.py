"""
Minimal test - just 5 attacks to verify the system works.
Should complete in under 1 minute.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
import time


def main():
    print("="*70)
    print("MINIMAL TEST - 5 Attacks Only")
    print("="*70)

    # Initialize Mistral with shorter response limit
    print("\nInitializing Mistral...")
    mistral = MistralInterface(
        model_name="mistral:7b",
        temperature=0.7,
        max_tokens=80  # Very short responses for speed
    )

    # Test connection
    if not mistral.test_connection():
        print("ERROR: Cannot connect to Mistral")
        return

    print("✓ Connected\n")

    # Initialize runner
    runner = AttackRunner(
        model_generate_fn=mistral.generate,
        model_name="mistral:7b",
        use_evaluator=True
    )

    loader = PromptLoader()

    # Load just 1 attack from each of 5 categories
    print("Loading 5 attacks...")
    attacks = []
    categories = ['cognitive_hacking', 'roleplay', 'hypothetical', 'social_engineering', 'refusal_suppression']

    for cat in categories:
        prompts = loader.load_jailbreak_prompts(category=cat)
        if prompts:
            attacks.append(prompts[0])  # Just take first attack from each

    # Use just 1 harmful request
    harmful_data = loader.load_harmful_requests(category="unsafe_content")
    harmful_request = harmful_data[0]['request']
    harmful_id = harmful_data[0]['id']

    print(f"Testing {len(attacks)} attacks against 1 harmful request")
    print(f"Harmful request: {harmful_request[:50]}...\n")

    # Run baseline
    print("-"*70)
    print("Running baseline (no jailbreak)...")
    start = time.time()
    baseline_result = runner.run_baseline(harmful_request, harmful_id)
    baseline_time = time.time() - start

    print(f"  Time: {baseline_time:.2f}s")
    print(f"  Success: {baseline_result.jailbreak_successful}")
    print(f"  Response: {baseline_result.model_response[:80]}...")

    # Run attacks
    results = [baseline_result]

    print("\n" + "-"*70)
    print(f"Running {len(attacks)} jailbreak attacks...")
    print("-"*70)

    for i, attack in enumerate(attacks, 1):
        print(f"\n[{i}/{len(attacks)}] {attack['name']}")
        start = time.time()
        result = runner.run_attack(attack, harmful_request, harmful_id)
        attack_time = time.time() - start
        results.append(result)

        print(f"  Time: {attack_time:.2f}s")
        print(f"  Success: {result.jailbreak_successful}")
        print(f"  Refusal: {result.refusal_detected}")
        print(f"  Response: {result.model_response[:80]}...")

    # Calculate metrics
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    calculator = MetricsCalculator(results)

    total = len(results)
    successful = sum(1 for r in results if r.jailbreak_successful)

    print(f"\nTotal tests: {total}")
    print(f"Successful jailbreaks: {successful}")
    print(f"Success rate: {(successful/total)*100:.1f}%")

    # Baseline vs attacks
    baseline_success = baseline_result.jailbreak_successful
    attack_results = [r for r in results if r.attack_category != "baseline"]
    attack_success_count = sum(1 for r in attack_results if r.jailbreak_successful)

    print(f"\nBaseline (no jailbreak): {'SUCCESS' if baseline_success else 'FAILED'}")
    print(f"Jailbreak attacks: {attack_success_count}/{len(attack_results)} succeeded")

    print("\n" + "="*70)
    print("✓ MINIMAL TEST COMPLETE")
    print("="*70)
    print("\nThe framework is working! Run example_attack.py for full testing.")


if __name__ == "__main__":
    main()
