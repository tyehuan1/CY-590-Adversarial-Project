"""
Test parallel execution - should be 3-4x faster than sequential.
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
import time


def main():
    print("="*70)
    print("PARALLEL EXECUTION TEST")
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

    print("✓ Connected\n")

    # Load test data
    loader = PromptLoader()

    # Use first 10 attacks from cognitive_hacking
    attacks = loader.load_jailbreak_prompts(category="cognitive_hacking")[:10]

    # Use first 2 harmful requests
    harmful_data = loader.load_harmful_requests(category="unsafe_content")[:2]
    harmful_requests = [h['request'] for h in harmful_data]

    total_tests = len(attacks) * len(harmful_requests) + len(harmful_requests)  # +baseline
    print(f"Testing: {len(attacks)} attacks × {len(harmful_requests)} requests + {len(harmful_requests)} baseline")
    print(f"Total tests: {total_tests}\n")

    # Initialize runner
    runner = AttackRunner(
        model_generate_fn=mistral.generate,
        model_name="mistral:7b",
        use_evaluator=True
    )

    # ===== SEQUENTIAL TEST =====
    print("="*70)
    print("1. SEQUENTIAL EXECUTION (original)")
    print("="*70)

    start_seq = time.time()
    results_seq = runner.run_attack_suite(
        jailbreak_category="cognitive_hacking",
        harmful_requests=harmful_requests,
        include_baseline=True,
        parallel=False  # Sequential
    )
    time_seq = time.time() - start_seq

    print(f"\n✓ Sequential completed in {time_seq:.1f} seconds ({time_seq/60:.1f} minutes)")
    print(f"  Average: {time_seq/len(results_seq):.1f}s per test")

    # ===== PARALLEL TEST =====
    print("\n" + "="*70)
    print("2. PARALLEL EXECUTION (4 workers)")
    print("="*70)

    start_par = time.time()
    results_par = runner.run_attack_suite(
        jailbreak_category="cognitive_hacking",
        harmful_requests=harmful_requests,
        include_baseline=True,
        parallel=True,      # Parallel!
        max_workers=4       # 4 concurrent requests
    )
    time_par = time.time() - start_par

    print(f"\n✓ Parallel completed in {time_par:.1f} seconds ({time_par/60:.1f} minutes)")
    print(f"  Average: {time_par/len(results_par):.1f}s per test")

    # ===== COMPARISON =====
    print("\n" + "="*70)
    print("SPEEDUP COMPARISON")
    print("="*70)

    speedup = time_seq / time_par
    time_saved = time_seq - time_par

    print(f"\nSequential:  {time_seq:.1f}s ({time_seq/60:.1f} min)")
    print(f"Parallel:    {time_par:.1f}s ({time_par/60:.1f} min)")
    print(f"\nSpeedup:     {speedup:.2f}x faster")
    print(f"Time saved:  {time_saved:.1f}s ({time_saved/60:.1f} min)")

    # Metrics
    calc_seq = MetricsCalculator(results_seq)
    calc_par = MetricsCalculator(results_par)

    print(f"\nSuccess rates:")
    print(f"  Sequential: {calc_seq.overall_success_rate():.1f}%")
    print(f"  Parallel:   {calc_par.overall_success_rate():.1f}%")

    # Estimate for full suite
    full_suite_size = 3834
    estimated_seq_hours = (time_seq / len(results_seq)) * full_suite_size / 3600
    estimated_par_hours = (time_par / len(results_par)) * full_suite_size / 3600

    print("\n" + "="*70)
    print("ESTIMATED TIME FOR FULL SUITE (3,834 tests)")
    print("="*70)
    print(f"Sequential:  {estimated_seq_hours:.1f} hours")
    print(f"Parallel:    {estimated_par_hours:.1f} hours")
    print(f"Time saved:  {estimated_seq_hours - estimated_par_hours:.1f} hours")

    print("\n" + "="*70)
    print("✓ PARALLEL EXECUTION WORKING!")
    print("="*70)
    print(f"\nUse parallel=True and max_workers=4 in run_attack_suite()")
    print(f"to get {speedup:.1f}x speedup on all tests.")


if __name__ == "__main__":
    main()
