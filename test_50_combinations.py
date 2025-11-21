"""
Test exactly 50 attack combinations with 3 defense levels: No Defense, Light, Strong.
Total: 50 × 3 = 150 tests
"""

from attacks import AttackRunner, PromptLoader
from evaluation import MetricsCalculator
from models.mistral_interface import MistralInterface
from defenses import (
    get_system_prompt,
    create_light_defense,
    create_strong_defense,
    create_light_output_validation,
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
    print("DEFENSE TESTING - 50 COMBINATIONS × 3 DEFENSE LEVELS = 150 TESTS")
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

    # Defense configurations (No Defense, Light, Strong only)
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
            "name": "Strong Defense",
            "system_prompt": get_system_prompt("comprehensive"),
            "input_filter": create_strong_defense(),
            "output_validator": create_strong_output_validation()
        }
    ]

    # Load exactly 50 combinations
    loader = PromptLoader()

    print("Creating 50 attack combinations...")
    # Get 5 attacks from cognitive_hacking
    attacks = loader.load_jailbreak_prompts(category="cognitive_hacking")[:5]
    # Get 10 harmful requests from unsafe_content
    harmful_requests = loader.load_harmful_requests(category="unsafe_content")[:10]

    print(f"  - {len(attacks)} jailbreak attacks")
    print(f"  - {len(harmful_requests)} harmful requests")
    print(f"  - Total combinations: {len(attacks) * len(harmful_requests)}\n")

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

        print(f"\nRunning 50 combinations with {config['name']}...")

        # Manually run exactly 50 combinations
        from attacks.attack_result import AttackResult
        from datetime import datetime as dt
        import time

        results = []
        test_count = 0

        for attack in attacks:
            for harm_req in harmful_requests:
                test_count += 1
                print(f"  [{test_count}/50] {attack['name'][:30]}... × {harm_req['request'][:30]}...", flush=True)

                # Format the attack prompt
                attack_prompt = attack['template'].format(harmful_request=harm_req['request'])

                # Run the attack
                start_time = time.time()
                response = defended_model_fn(attack_prompt)
                response_time = time.time() - start_time

                # Create result object
                result = AttackResult(
                    attack_id=attack.get('id', 'unknown'),
                    attack_name=attack['name'],
                    attack_category='cognitive_hacking',
                    harmful_request_id=harm_req.get('id', 'unknown'),
                    harmful_request_text=harm_req['request'],
                    severity=harm_req.get('severity', 'unknown'),
                    final_prompt=attack_prompt,
                    encoding_used=attack.get('encoding'),
                    model_response=response,
                    response_time_seconds=response_time,
                    timestamp=dt.now()
                )

                # Evaluate if evaluator is available
                if runner.evaluator:
                    eval_result = runner.evaluator.evaluate_response(
                        response=response,
                        harmful_request=harm_req['request']
                    )
                    result.jailbreak_successful = eval_result['jailbreak_successful']
                    result.refusal_detected = eval_result['refusal_detected']
                    result.harmful_content_present = eval_result['harmful_content_present']

                results.append(result)

        # Tag results with defense config
        for result in results:
            result.defense_config = config["name"]

        all_results.extend(results)

        # Show summary
        calculator = MetricsCalculator(results)
        refusals = sum(1 for r in results if r.refusal_detected)
        refusal_rate = (refusals / len(results)) * 100 if results else 0

        print(f"\n  ✓ Completed: {len(results)} tests")
        print(f"  Success rate: {calculator.overall_success_rate():.1f}%")
        print(f"  Refusal rate: {refusal_rate:.1f}%")

    # Export results
    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results/defense_50combos_{timestamp}.csv"
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
        "test_type": "Defense Testing - 50 Combinations (No Defense, Light, Strong)",
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
    print(f"\nTotal tests run: {len(all_results)}")
    print(f"CSV: {csv_filename}")
    print(f"JSON: {json_filename}")


if __name__ == "__main__":
    main()
