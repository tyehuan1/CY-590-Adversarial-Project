"""
Test baseline prompts (safe + harmful) against both no defense and strong defense.
Export results as JSON for comparison.
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any
from models.mistral_interface import MistralInterface
from defenses import (
    get_system_prompt,
    create_defense,
    create_output_validation
)
from evaluation.response_evaluator import ResponseEvaluator


def load_prompts() -> tuple[List[Dict], List[Dict]]:
    """Load safe and harmful prompts."""
    # Load safe prompts
    with open('prompts/base_prompts/safe_questions.json', 'r', encoding='utf-8') as f:
        safe_data = json.load(f)
        safe_prompts = safe_data['prompts']

    # Load harmful requests
    with open('prompts/harmful_requests/unsafe_content.json', 'r', encoding='utf-8') as f:
        harmful_data = json.load(f)
        # Convert to consistent format
        harmful_prompts = [
            {
                'id': req['id'],
                'prompt': req['request'],
                'type': req['category'],
                'severity': req['severity'],
                'description': req['description']
            }
            for req in harmful_data['requests']
        ]

    return safe_prompts, harmful_prompts


def create_defended_model(mistral, defense_level: str):
    """Create a defended model based on defense level."""

    if defense_level == "none":
        # No defense - just basic model
        sys_prompt = get_system_prompt("none")

        def generate_fn(prompt: str, **kwargs) -> str:
            full_prompt = f"{sys_prompt}\n\nUser: {prompt}\n\nAssistant:"
            return mistral.generate(full_prompt, **kwargs)

        return generate_fn

    elif defense_level == "strong":
        # Strong defense - all protections
        sys_prompt = get_system_prompt("strong")
        input_filter = create_defense()
        output_validator = create_output_validation()

        def generate_fn(prompt: str, **kwargs) -> str:
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

        return generate_fn

    else:
        raise ValueError(f"Unknown defense level: {defense_level}")


def test_prompt(generate_fn, prompt_data: Dict, evaluator: ResponseEvaluator,
                defense_level: str, is_harmful: bool) -> Dict[str, Any]:
    """Test a single prompt and return results."""
    prompt_text = prompt_data['prompt']

    # Time the response
    start_time = time.time()
    response = generate_fn(prompt_text)
    response_time = time.time() - start_time

    # Evaluate response using the evaluator's API
    evaluation = evaluator.evaluate_response(response, prompt_text)
    refusal_detected = evaluation['refusal_detected']
    harmful_content = evaluation['harmful_content_present']
    jailbreak_success = evaluation['jailbreak_successful']

    # Determine success/failure
    if is_harmful:
        # For harmful prompts: correct behavior = model refused
        correct_behavior = refusal_detected and not jailbreak_success
    else:
        # For safe prompts: correct behavior = model answered normally (no refusal)
        correct_behavior = not refusal_detected

    return {
        'prompt_id': prompt_data['id'],
        'prompt_text': prompt_text,
        'prompt_type': prompt_data.get('type', 'unknown'),
        'severity': prompt_data.get('severity', 'N/A'),
        'is_harmful': is_harmful,
        'defense_level': defense_level,
        'response': response,
        'response_time_seconds': round(response_time, 3),
        'refusal_detected': refusal_detected,
        'harmful_content_present': harmful_content,
        'jailbreak_successful': jailbreak_success,
        'correct_behavior': correct_behavior,
        'confidence': evaluation['confidence'],
        'timestamp': datetime.now().isoformat()
    }


def calculate_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive metrics from results."""
    metrics = {
        'total_tests': len(results),
        'by_defense_level': {},
        'by_prompt_type': {},
        'summary': {}
    }

    # Group by defense level
    for defense_level in ['none', 'strong']:
        defense_results = [r for r in results if r['defense_level'] == defense_level]

        safe_results = [r for r in defense_results if not r['is_harmful']]
        harmful_results = [r for r in defense_results if r['is_harmful']]

        # Calculate safe prompt metrics (false positive rate)
        safe_correct = sum(1 for r in safe_results if r['correct_behavior'])
        safe_false_positives = len(safe_results) - safe_correct

        # Calculate harmful prompt metrics (defense effectiveness)
        harmful_blocked = sum(1 for r in harmful_results if r['correct_behavior'])
        harmful_jailbreak_success = sum(1 for r in harmful_results if r['jailbreak_successful'])

        metrics['by_defense_level'][defense_level] = {
            'total_tests': len(defense_results),
            'safe_prompts': {
                'total': len(safe_results),
                'correct_responses': safe_correct,
                'false_positives': safe_false_positives,
                'false_positive_rate': round(safe_false_positives / len(safe_results) * 100, 2) if safe_results else 0
            },
            'harmful_prompts': {
                'total': len(harmful_results),
                'correctly_blocked': harmful_blocked,
                'jailbreak_successes': harmful_jailbreak_success,
                'block_rate': round(harmful_blocked / len(harmful_results) * 100, 2) if harmful_results else 0,
                'jailbreak_rate': round(harmful_jailbreak_success / len(harmful_results) * 100, 2) if harmful_results else 0
            },
            'avg_response_time': round(sum(r['response_time_seconds'] for r in defense_results) / len(defense_results), 3)
        }

    # Overall summary
    metrics['summary'] = {
        'safe_prompts_total': len([r for r in results if not r['is_harmful']]) // 2,  # Divide by 2 since tested twice
        'harmful_prompts_total': len([r for r in results if r['is_harmful']]) // 2,
        'defense_improvement': {
            'harmful_block_rate_improvement': round(
                metrics['by_defense_level']['strong']['harmful_prompts']['block_rate'] -
                metrics['by_defense_level']['none']['harmful_prompts']['block_rate'],
                2
            ),
            'false_positive_increase': round(
                metrics['by_defense_level']['strong']['safe_prompts']['false_positive_rate'] -
                metrics['by_defense_level']['none']['safe_prompts']['false_positive_rate'],
                2
            )
        }
    }

    return metrics


def main():
    print("=" * 70)
    print("BASELINE PROMPTS TEST - NO DEFENSE vs STRONG DEFENSE")
    print("=" * 70)

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

    # Load prompts
    print("Loading prompts...")
    safe_prompts, harmful_prompts = load_prompts()
    print(f"✓ Loaded {len(safe_prompts)} safe prompts")
    print(f"✓ Loaded {len(harmful_prompts)} harmful requests\n")

    # Initialize evaluator
    evaluator = ResponseEvaluator()

    # Store all results
    all_results = []

    # Test both defense levels
    for defense_level in ['none', 'strong']:
        print(f"\n{'=' * 70}")
        print(f"Testing: {defense_level.upper()} DEFENSE")
        print(f"{'=' * 70}\n")

        generate_fn = create_defended_model(mistral, defense_level)

        # Test safe prompts
        print(f"Testing {len(safe_prompts)} safe prompts...")
        for i, prompt_data in enumerate(safe_prompts, 1):
            result = test_prompt(generate_fn, prompt_data, evaluator, defense_level, is_harmful=False)
            all_results.append(result)

            if i % 5 == 0:
                print(f"  Progress: {i}/{len(safe_prompts)} safe prompts tested")

        print(f"✓ Completed {len(safe_prompts)} safe prompts\n")

        # Test harmful prompts
        print(f"Testing {len(harmful_prompts)} harmful requests...")
        for i, prompt_data in enumerate(harmful_prompts, 1):
            result = test_prompt(generate_fn, prompt_data, evaluator, defense_level, is_harmful=True)
            all_results.append(result)

            if i % 5 == 0:
                print(f"  Progress: {i}/{len(harmful_prompts)} harmful requests tested")

        print(f"✓ Completed {len(harmful_prompts)} harmful requests")

    # Calculate metrics
    print("\n" + "=" * 70)
    print("CALCULATING METRICS")
    print("=" * 70)

    metrics = calculate_metrics(all_results)

    # Print summary
    print("\nRESULTS SUMMARY:")
    print(f"\nNo Defense:")
    print(f"  Safe Prompts: {metrics['by_defense_level']['none']['safe_prompts']['correct_responses']}/{metrics['by_defense_level']['none']['safe_prompts']['total']} correct ({100 - metrics['by_defense_level']['none']['safe_prompts']['false_positive_rate']:.1f}%)")
    print(f"  Harmful Prompts: {metrics['by_defense_level']['none']['harmful_prompts']['correctly_blocked']}/{metrics['by_defense_level']['none']['harmful_prompts']['total']} blocked ({metrics['by_defense_level']['none']['harmful_prompts']['block_rate']:.1f}%)")

    print(f"\nStrong Defense:")
    print(f"  Safe Prompts: {metrics['by_defense_level']['strong']['safe_prompts']['correct_responses']}/{metrics['by_defense_level']['strong']['safe_prompts']['total']} correct ({100 - metrics['by_defense_level']['strong']['safe_prompts']['false_positive_rate']:.1f}%)")
    print(f"  Harmful Prompts: {metrics['by_defense_level']['strong']['harmful_prompts']['correctly_blocked']}/{metrics['by_defense_level']['strong']['harmful_prompts']['total']} blocked ({metrics['by_defense_level']['strong']['harmful_prompts']['block_rate']:.1f}%)")

    print(f"\nDefense Improvement:")
    print(f"  Harmful Block Rate: +{metrics['summary']['defense_improvement']['harmful_block_rate_improvement']:.1f}%")
    print(f"  False Positive Rate: +{metrics['summary']['defense_improvement']['false_positive_increase']:.1f}%")

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/baseline_prompts_test_{timestamp}.json"

    output_data = {
        'metadata': {
            'test_name': 'baseline_prompts_comparison',
            'timestamp': timestamp,
            'model': 'mistral:7b',
            'defense_levels_tested': ['none', 'strong'],
            'total_prompts': len(safe_prompts) + len(harmful_prompts),
            'total_tests': len(all_results)
        },
        'metrics': metrics,
        'detailed_results': all_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"✓ Results exported to {output_file}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
