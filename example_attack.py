"""
Comprehensive attack testing example.

This script tests EVERY combination of:
- Jailbreak prompts (from ALL categories)
- Harmful requests (from JSON files)

Including obfuscation attacks with automatic encoding.
"""

from attacks import AttackRunner, PromptLoader


def mock_model_generate(prompt: str) -> str:
    """
    Mock model for testing the framework.
    Replace this with your actual MistralInterface.generate() method.
    """
    # Simple mock: return indication of what was sent
    if len(prompt) > 200:
        return f"[Mock response to prompt of length {len(prompt)}]"
    else:
        return f"[Mock response] I cannot assist with that request."


def main():
    print("="*70)
    print("COMPREHENSIVE JAILBREAK ATTACK TESTING")
    print("Testing ALL combinations of prompts × harmful requests")
    print("="*70)

    # Initialize attack runner with mock model
    # REPLACE mock_model_generate with: model.generate from MistralInterface
    runner = AttackRunner(
        model_generate_fn=mock_model_generate,
        model_name="mistral"
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
        jailbreak_category=None,  # None = ALL categories
        harmful_category=None,    # None = ALL harmful requests
        include_baseline=True     # Include baseline tests
    )

    # ===== RESULTS SUMMARY =====
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)

    print(f"\nTotal tests completed: {len(results)}")

    # Count by attack category
    category_counts = {}
    for result in results:
        cat = result.attack_category
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\nTests by attack category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat:30} : {count:4} tests")

    # Show encoding usage
    encoding_counts = {}
    for result in results:
        enc = result.encoding_used or "none"
        encoding_counts[enc] = encoding_counts.get(enc, 0) + 1

    print("\nEncoding usage:")
    for enc, count in sorted(encoding_counts.items()):
        print(f"  {enc:30} : {count:4} tests")

    # Show sample results
    print("\n" + "-"*70)
    print("SAMPLE RESULTS (First 5)")
    print("-"*70)

    for i, result in enumerate(results[:5]):
        print(f"\n[{i+1}] {result.attack_name}")
        print(f"    Category: {result.attack_category}")
        print(f"    Harmful Request: {result.harmful_request_text}")
        print(f"    Encoding: {result.encoding_used or 'none'}")
        print(f"    Response: {result.model_response[:80]}...")
        print(f"    Time: {result.response_time_seconds:.3f}s")

    # Show obfuscation examples specifically
    print("\n" + "-"*70)
    print("OBFUSCATION ATTACK EXAMPLES")
    print("-"*70)

    obfuscation_results = [r for r in results if r.attack_category.startswith("obfuscation")]
    if obfuscation_results:
        for result in obfuscation_results[:3]:
            print(f"\n{result.attack_name} ({result.encoding_used})")
            print(f"  Original: {result.harmful_request_text}")
            print(f"  Final prompt (first 100 chars): {result.final_prompt[:100]}...")
            print(f"  Response: {result.model_response[:80]}...")
    else:
        print("  No obfuscation attacks found in results")

    print("\n" + "="*70)
    print("TESTING COMPLETE!")
    print("="*70)
    print(f"\nAll {len(results)} tests completed successfully.")
    print("\nNext steps:")
    print("  1. Replace mock_model_generate with your MistralInterface.generate()")
    print("  2. Add evaluation logic to detect jailbreak success")
    print("  3. Save results to CSV/JSON for analysis")


if __name__ == "__main__":
    main()
