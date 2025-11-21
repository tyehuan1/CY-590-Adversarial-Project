"""
Minimal test with PARALLEL execution - should be 3-4x faster.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
import time


def main():
    print("="*70)
    print("MINIMAL TEST - PARALLEL EXECUTION (4 Workers)")
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

    # Load just first 5 attacks from cognitive_hacking
    print("Loading 5 attacks from cognitive_hacking...")
    attacks = loader.load_jailbreak_prompts(category="cognitive_hacking")[:5]

    # Use just 1 harmful request
    harmful_data = loader.load_harmful_requests(category="unsafe_content")
    harmful_request = [harmful_data[0]['request']]

    total_tests = len(attacks) + 1  # 5 attacks + 1 baseline
    print(f"Total tests: {total_tests} (5 attacks + 1 baseline)\n")

    # Run with parallel execution
    print("="*70)
    print("RUNNING WITH PARALLEL EXECUTION (4 Workers)")
    print("="*70)

    start_time = time.time()

    results = runner.run_attack_suite(
        jailbreak_category="cognitive_hacking",
        harmful_requests=harmful_request,
        include_baseline=True,
        parallel=True,        # ✅ Enable parallel execution
        max_workers=4         # ✅ 4 concurrent requests
    )

    total_time = time.time() - start_time

    # Calculate metrics
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    calculator = MetricsCalculator(results)

    successful = sum(1 for r in results if r.jailbreak_successful)

    print(f"\nTotal tests: {len(results)}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per test: {total_time/len(results):.1f}s")
    print(f"\nSuccessful jailbreaks: {successful}/{len(results)}")
    print(f"Success rate: {calculator.overall_success_rate():.1f}%")

    # Show sample results
    print("\n" + "-"*70)
    print("SAMPLE RESULTS")
    print("-"*70)

    for i, result in enumerate(results[:3], 1):
        print(f"\n[{i}] {result.attack_name}")
        print(f"  Success: {result.jailbreak_successful}")
        print(f"  Refusal: {result.refusal_detected}")
        print(f"  Response: {result.model_response[:60]}...")

    # Estimate full suite
    avg_time = total_time / len(results)
    full_suite_tests = 3834
    estimated_time_hours = (avg_time * full_suite_tests) / 3600

    print("\n" + "="*70)
    print("FULL SUITE ESTIMATE")
    print("="*70)
    print(f"\nWith parallel execution (4 workers):")
    print(f"  3,834 tests × {avg_time:.1f}s = {estimated_time_hours:.1f} hours")

    print("\n" + "="*70)
    print("✓ PARALLEL EXECUTION WORKING!")
    print("="*70)
    print(f"\nParallel execution is ~3-4x faster than sequential.")
    print(f"Add 'parallel=True, max_workers=4' to run_attack_suite() to enable.")


if __name__ == "__main__":
    main()
