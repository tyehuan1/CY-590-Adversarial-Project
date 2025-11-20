"""
Calculate metrics and statistics from attack results.
"""

from typing import List, Dict
from collections import defaultdict


class MetricsCalculator:
    """Calculate success rates and statistics from attack results."""

    def __init__(self, results: List):
        """
        Initialize with a list of AttackResult objects.

        Args:
            results: List of AttackResult objects from attack runs
        """
        self.results = results

    def overall_success_rate(self) -> float:
        """
        Calculate overall jailbreak success rate.

        Returns:
            Percentage of successful jailbreaks (0-100)
        """
        if not self.results:
            return 0.0

        successful = sum(1 for r in self.results if r.jailbreak_successful)
        return (successful / len(self.results)) * 100

    def success_rate_by_category(self) -> Dict[str, float]:
        """
        Calculate success rate for each attack category.

        Returns:
            Dictionary mapping category name to success rate percentage
        """
        category_counts = defaultdict(int)
        category_successes = defaultdict(int)

        for result in self.results:
            category = result.attack_category
            category_counts[category] += 1
            if result.jailbreak_successful:
                category_successes[category] += 1

        success_rates = {}
        for category in category_counts:
            rate = (category_successes[category] / category_counts[category]) * 100
            success_rates[category] = rate

        return dict(sorted(success_rates.items(), key=lambda x: x[1], reverse=True))

    def baseline_vs_jailbreak(self) -> Dict[str, any]:
        """
        Compare baseline (no jailbreak) success vs jailbreak success.

        Returns:
            Dictionary with baseline and jailbreak success rates
        """
        baseline_results = [r for r in self.results if r.attack_category == "baseline"]
        jailbreak_results = [r for r in self.results if r.attack_category != "baseline"]

        baseline_success = 0
        if baseline_results:
            baseline_success = (sum(1 for r in baseline_results if r.jailbreak_successful) / len(baseline_results)) * 100

        jailbreak_success = 0
        if jailbreak_results:
            jailbreak_success = (sum(1 for r in jailbreak_results if r.jailbreak_successful) / len(jailbreak_results)) * 100

        return {
            "baseline_success_rate": baseline_success,
            "jailbreak_success_rate": jailbreak_success,
            "improvement": jailbreak_success - baseline_success,
            "baseline_count": len(baseline_results),
            "jailbreak_count": len(jailbreak_results)
        }

    def most_effective_attacks(self, top_n: int = 10) -> List[Dict[str, any]]:
        """
        Find the most effective individual attack prompts.

        Args:
            top_n: Number of top attacks to return

        Returns:
            List of dictionaries with attack info and success rates
        """
        attack_stats = defaultdict(lambda: {"total": 0, "successful": 0, "name": "", "category": ""})

        for result in self.results:
            if result.attack_category == "baseline":
                continue

            attack_id = result.attack_id
            attack_stats[attack_id]["total"] += 1
            attack_stats[attack_id]["name"] = result.attack_name
            attack_stats[attack_id]["category"] = result.attack_category
            if result.jailbreak_successful:
                attack_stats[attack_id]["successful"] += 1

        # Calculate success rates
        attack_list = []
        for attack_id, stats in attack_stats.items():
            rate = (stats["successful"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            attack_list.append({
                "attack_id": attack_id,
                "name": stats["name"],
                "category": stats["category"],
                "success_rate": rate,
                "successful": stats["successful"],
                "total": stats["total"]
            })

        # Sort by success rate
        attack_list.sort(key=lambda x: x["success_rate"], reverse=True)

        return attack_list[:top_n]

    def average_response_time(self) -> float:
        """
        Calculate average response time across all attacks.

        Returns:
            Average response time in seconds
        """
        times = [r.response_time_seconds for r in self.results if r.response_time_seconds]
        return sum(times) / len(times) if times else 0.0

    def print_summary(self):
        """Print a formatted summary of all metrics."""
        print("\n" + "=" * 70)
        print("ATTACK METRICS SUMMARY")
        print("=" * 70)

        # Overall stats
        print(f"\nTotal Attacks Run: {len(self.results)}")
        print(f"Overall Success Rate: {self.overall_success_rate():.1f}%")
        print(f"Average Response Time: {self.average_response_time():.2f}s")

        # Baseline vs Jailbreak
        print("\n" + "-" * 70)
        print("BASELINE vs JAILBREAK COMPARISON")
        print("-" * 70)
        comparison = self.baseline_vs_jailbreak()
        print(f"Baseline Success Rate: {comparison['baseline_success_rate']:.1f}% ({comparison['baseline_count']} tests)")
        print(f"Jailbreak Success Rate: {comparison['jailbreak_success_rate']:.1f}% ({comparison['jailbreak_count']} tests)")
        print(f"Improvement: +{comparison['improvement']:.1f} percentage points")

        # By category
        print("\n" + "-" * 70)
        print("SUCCESS RATE BY ATTACK CATEGORY")
        print("-" * 70)
        category_rates = self.success_rate_by_category()
        for category, rate in category_rates.items():
            if category != "baseline":
                print(f"{category:30} : {rate:5.1f}%")

        # Most effective attacks
        print("\n" + "-" * 70)
        print("TOP 10 MOST EFFECTIVE ATTACKS")
        print("-" * 70)
        top_attacks = self.most_effective_attacks(10)
        for i, attack in enumerate(top_attacks, 1):
            print(f"{i:2}. {attack['name']:40} {attack['success_rate']:5.1f}% ({attack['successful']}/{attack['total']})")

        print("\n" + "=" * 70)

    def export_to_dict(self) -> Dict[str, any]:
        """
        Export all metrics as a dictionary for saving to JSON.

        Returns:
            Dictionary with all calculated metrics
        """
        return {
            "total_attacks": len(self.results),
            "overall_success_rate": self.overall_success_rate(),
            "average_response_time": self.average_response_time(),
            "baseline_vs_jailbreak": self.baseline_vs_jailbreak(),
            "success_by_category": self.success_rate_by_category(),
            "top_attacks": self.most_effective_attacks(10)
        }
