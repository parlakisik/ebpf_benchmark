#!/usr/bin/env python3
"""
Generate comprehensive benchmark comparison report

Analyzes benchmark results and creates comparative analysis and visualizations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys

# Try to import plotting libraries, with graceful fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, skipping plots")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class BenchmarkReport:
    """Generate benchmarking report from results"""

    def __init__(self, results_dir: str = "benchmarks/results"):
        self.results_dir = Path(results_dir)
        self.results = {}
        self.load_results()

    def load_results(self):
        """Load all JSON result files"""
        if not self.results_dir.exists():
            print(f"Results directory {self.results_dir} not found")
            return

        for result_file in self.results_dir.glob("*.json"):
            if result_file.name in ["latest.json", "benchmark_results_*.json"]:
                continue

            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    # Extract language from filename or data
                    if "Language" in data:
                        language = data["Language"]
                    else:
                        language = result_file.stem.split("_")[0].upper()

                    self.results[language] = data
                    print(f"✓ Loaded {language} results from {result_file.name}")
            except Exception as e:
                print(f"⚠ Error loading {result_file.name}: {e}")

    def generate_text_report(self) -> str:
        """Generate text-based comparison report"""
        if not self.results:
            return "No results available"

        report = []
        report.append("\n" + "="*80)
        report.append("eBPF BENCHMARK COMPARISON REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Number of languages tested: {len(self.results)}")
        report.append("="*80)

        # Benchmark parameters
        if self.results:
            first_result = next(iter(self.results.values()))
            report.append(f"\nBenchmark Configuration:")
            report.append(f"  Program Type:     {first_result.get('ProgramType', 'Unknown')}")
            report.append(f"  Data Mechanism:   {first_result.get('DataMechanism', 'Unknown')}")
            report.append(f"  Duration:         {first_result.get('Duration', 0):.2f} seconds")

        # Results table
        report.append("\n" + "-"*80)
        report.append(f"{'Language':<12} {'Throughput':<20} {'Duration':<15} {'Events':<15}")
        report.append("-"*80)

        # Sort by throughput (descending)
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].get('Throughput', 0),
            reverse=True
        )

        for language, data in sorted_results:
            throughput = data.get('Throughput', 0)
            duration = data.get('Duration', 0)
            event_count = data.get('EventCount', 0)

            report.append(f"{language:<12} {throughput:>18,.0f} ev/s {duration:>13.2f}s {event_count:>13,}")

        report.append("-"*80)

        # Performance comparison
        if len(sorted_results) > 1:
            best_throughput = sorted_results[0][1].get('Throughput', 1)
            report.append("\nRelative Performance (normalized to fastest):")
            report.append("-"*80)

            for language, data in sorted_results:
                throughput = data.get('Throughput', 0)
                relative = (throughput / best_throughput * 100) if best_throughput > 0 else 0
                bar_width = int(relative / 5)
                bar = "█" * bar_width

                report.append(f"{language:<12} {relative:>6.1f}% {bar}")

        report.append("\n" + "="*80)

        # Summary
        report.append("\nKey Observations:")
        if sorted_results:
            best, best_data = sorted_results[0]
            report.append(f"  • Best performance: {best} ({best_data.get('Throughput', 0):,.0f} events/sec)")

        if len(sorted_results) > 1:
            worst, worst_data = sorted_results[-1]
            report.append(f"  • Lowest performance: {worst} ({worst_data.get('Throughput', 0):,.0f} events/sec)")

        report.append("\n" + "="*80 + "\n")

        return "\n".join(report)

    def generate_html_report(self) -> str:
        """Generate HTML report"""
        if not self.results:
            return "<html><body><p>No results available</p></body></html>"

        # Sort results by throughput
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].get('Throughput', 0),
            reverse=True
        )

        # Create comparison table rows
        table_rows = []
        best_throughput = sorted_results[0][1].get('Throughput', 1) if sorted_results else 1

        for language, data in sorted_results:
            throughput = data.get('Throughput', 0)
            relative = (throughput / best_throughput * 100) if best_throughput > 0 else 0
            duration = data.get('Duration', 0)
            events = data.get('EventCount', 0)

            table_rows.append(f"""
                <tr>
                    <td>{language}</td>
                    <td>{throughput:,.0f}</td>
                    <td>{relative:.1f}%</td>
                    <td>{duration:.2f}</td>
                    <td>{events:,}</td>
                </tr>
            """)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>eBPF Benchmark Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .metric {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #007bff;
                }}
                .summary {{
                    background-color: #e7f3ff;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>eBPF Benchmark Comparison Report</h1>

                <div class="summary">
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Languages Tested:</strong> {', '.join([lang for lang, _ in sorted_results])}</p>
                </div>

                <h2>Results Table</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Language</th>
                            <th>Throughput (events/sec)</th>
                            <th>Relative Performance</th>
                            <th>Duration (sec)</th>
                            <th>Total Events</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>

                <h2>Performance Analysis</h2>
                <div class="metric">
                    <p><strong>Best Performance:</strong> {sorted_results[0][0]} with {sorted_results[0][1].get('Throughput', 0):,.0f} events/second</p>
                    {'<p><strong>Lowest Performance:</strong> ' + sorted_results[-1][0] + ' with ' + f"{sorted_results[-1][1].get('Throughput', 0):,.0f}" + ' events/second</p>' if len(sorted_results) > 1 else ''}
                </div>

                <h2>Implementation Details</h2>
                <div class="metric">
                    <ul>
                        <li><strong>Program Type:</strong> {sorted_results[0][1].get('ProgramType', 'Unknown')}</li>
                        <li><strong>Data Mechanism:</strong> {sorted_results[0][1].get('DataMechanism', 'Unknown')}</li>
                        <li><strong>Duration per test:</strong> {sorted_results[0][1].get('Duration', 0):.2f} seconds</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def save_reports(self, output_dir: str = "benchmarks/results"):
        """Save text and HTML reports"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save text report
        text_report = self.generate_text_report()
        text_file = output_path / "report.txt"
        with open(text_file, 'w') as f:
            f.write(text_report)
        print(f"✓ Text report saved to {text_file}")

        # Print to console
        print(text_report)

        # Save HTML report
        html_report = self.generate_html_report()
        html_file = output_path / "report.html"
        with open(html_file, 'w') as f:
            f.write(html_report)
        print(f"✓ HTML report saved to {html_file}")

        return text_file, html_file

    def create_comparison_plots(self, output_dir: str = "benchmarks/results"):
        """Create visualization plots (if matplotlib available)"""
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            print("⚠ Skipping plots (matplotlib/numpy not available)")
            return

        if not self.results:
            return

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Sort by throughput
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].get('Throughput', 0),
            reverse=True
        )

        languages = [lang for lang, _ in sorted_results]
        throughputs = [data.get('Throughput', 0) for _, data in sorted_results]
        events = [data.get('EventCount', 0) for _, data in sorted_results]

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('eBPF Benchmark Results Comparison', fontsize=16, fontweight='bold')

        # Plot 1: Throughput comparison
        ax = axes[0, 0]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(languages)]
        bars = ax.bar(languages, throughputs, color=colors)
        ax.set_ylabel('Throughput (events/sec)')
        ax.set_title('Throughput Comparison')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

        # Add value labels on bars
        for bar, value in zip(bars, throughputs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:,.0f}',
                   ha='center', va='bottom', fontsize=9)

        # Plot 2: Relative performance
        ax = axes[0, 1]
        max_throughput = max(throughputs) if throughputs else 1
        relative = [(t / max_throughput * 100) for t in throughputs]
        bars = ax.barh(languages, relative, color=colors)
        ax.set_xlabel('Relative Performance (%)')
        ax.set_title('Performance Relative to Best')
        ax.set_xlim(0, 110)

        for i, (bar, value) in enumerate(zip(bars, relative)):
            ax.text(value + 1, i, f'{value:.1f}%', va='center', fontsize=9)

        # Plot 3: Event count
        ax = axes[1, 0]
        bars = ax.bar(languages, events, color=colors)
        ax.set_ylabel('Event Count')
        ax.set_title('Total Events Processed')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'))

        for bar, value in zip(bars, events):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:,.0f}',
                   ha='center', va='bottom', fontsize=8, rotation=0)

        # Plot 4: Summary statistics
        ax = axes[1, 1]
        ax.axis('off')

        summary_text = "Benchmark Summary\n" + "-"*30 + "\n"
        summary_text += f"Best: {languages[0]}\n"
        summary_text += f"Throughput: {throughputs[0]:,.0f} ev/s\n\n"

        if len(languages) > 1:
            summary_text += f"Worst: {languages[-1]}\n"
            summary_text += f"Throughput: {throughputs[-1]:,.0f} ev/s\n\n"

        summary_text += f"Average: {np.mean(throughputs):,.0f} ev/s\n"
        summary_text += f"Median: {np.median(throughputs):,.0f} ev/s"

        ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
               verticalalignment='center',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plot_file = output_path / "benchmark_comparison.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved to {plot_file}")
        plt.close()


def main():
    """Main entry point"""
    results_dir = "benchmarks/results"

    print("\n" + "="*80)
    print("BENCHMARK REPORT GENERATOR")
    print("="*80 + "\n")

    report = BenchmarkReport(results_dir)

    if not report.results:
        print("No benchmark results found. Run benchmarks first with: make benchmark")
        sys.exit(1)

    # Generate and save reports
    report.save_reports(results_dir)

    # Create plots if available
    report.create_comparison_plots(results_dir)

    print("\n✓ Report generation complete!")
    print(f"Results saved to: {results_dir}/")


if __name__ == "__main__":
    main()
