#!/usr/bin/env python3
"""
Generate Benchmark Analysis Plots

Create comprehensive visualizations of benchmark results
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from process_results import ResultsProcessor


class PlotGenerator:
    """Generate analysis plots from benchmark results"""

    def __init__(self, results_dir: str = "benchmarks/results", output_dir: str = "analysis/plots"):
        self.results_dir = results_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.processor = ResultsProcessor(results_dir)
        self.processor.load_results()
        self.df = self.processor.to_dataframe()

        # Set style
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def plot_throughput_comparison(self, benchmark_id: Optional[str] = None):
        """Plot throughput comparison across languages"""
        if self.df.empty:
            return

        df = self.df.copy()
        if benchmark_id:
            df = df[df['benchmark_id'] == benchmark_id]

        if 'metric_throughput' not in df.columns:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        # Prepare data
        plot_data = df.dropna(subset=['metric_throughput'])
        if plot_data.empty:
            return

        # Create bar plot
        sns.barplot(
            data=plot_data,
            x='benchmark_id',
            y='metric_throughput',
            hue='language',
            ax=ax
        )

        ax.set_title("Throughput Comparison (events/sec)")
        ax.set_ylabel("Throughput (events/sec)")
        ax.set_xlabel("Benchmark")
        ax.legend(title="Language")

        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_file = self.output_dir / "throughput_comparison.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved throughput plot to {output_file}")

    def plot_latency_distribution(self, benchmark_id: Optional[str] = None):
        """Plot latency distribution across languages"""
        if self.df.empty:
            return

        df = self.df.copy()
        if benchmark_id:
            df = df[df['benchmark_id'] == benchmark_id]

        # Check for latency columns
        latency_cols = [col for col in df.columns if 'latency' in col.lower()]
        if not latency_cols:
            return

        fig, axes = plt.subplots(1, len(latency_cols), figsize=(5 * len(latency_cols), 4))
        if len(latency_cols) == 1:
            axes = [axes]

        for ax, latency_col in zip(axes, latency_cols):
            plot_data = df.dropna(subset=[latency_col])
            if plot_data.empty:
                continue

            sns.boxplot(data=plot_data, x='language', y=latency_col, ax=ax)
            ax.set_title(f"{latency_col}")
            ax.set_ylabel("Latency (µs)")
            ax.set_xlabel("Language")

        plt.tight_layout()

        output_file = self.output_dir / "latency_distribution.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved latency plot to {output_file}")

    def plot_program_type_comparison(self):
        """Compare performance across different program types"""
        if self.df.empty or 'metric_throughput' not in self.df.columns:
            return

        df = self.df.copy()
        plot_data = df.dropna(subset=['metric_throughput'])

        if plot_data.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.barplot(
            data=plot_data,
            x='program_type',
            y='metric_throughput',
            hue='language',
            ax=ax
        )

        ax.set_title("Performance Comparison by eBPF Program Type")
        ax.set_ylabel("Throughput (events/sec)")
        ax.set_xlabel("Program Type")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

        plt.xticks(rotation=45, ha='right')
        plt.legend(title="Language")
        plt.tight_layout()

        output_file = self.output_dir / "program_type_comparison.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved program type plot to {output_file}")

    def plot_data_mechanism_comparison(self):
        """Compare performance across data mechanisms"""
        if self.df.empty or 'metric_throughput' not in self.df.columns:
            return

        df = self.df.copy()
        plot_data = df.dropna(subset=['metric_throughput'])

        if plot_data.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.barplot(
            data=plot_data,
            x='data_mechanism',
            y='metric_throughput',
            hue='language',
            ax=ax
        )

        ax.set_title("Performance Comparison by Data Mechanism")
        ax.set_ylabel("Throughput (events/sec)")
        ax.set_xlabel("Data Mechanism")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

        plt.xticks(rotation=45, ha='right')
        plt.legend(title="Language")
        plt.tight_layout()

        output_file = self.output_dir / "data_mechanism_comparison.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved data mechanism plot to {output_file}")

    def plot_language_performance_heatmap(self):
        """Create heatmap of language performance across benchmarks"""
        if self.df.empty or 'metric_throughput' not in self.df.columns:
            return

        df = self.df.copy()
        plot_data = df.dropna(subset=['metric_throughput'])

        if plot_data.empty:
            return

        # Create pivot table
        pivot = plot_data.pivot_table(
            values='metric_throughput',
            index='benchmark_id',
            columns='language',
            aggfunc='mean'
        )

        if pivot.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(
            pivot,
            annot=True,
            fmt='.0f',
            cmap='YlOrRd',
            ax=ax,
            cbar_kws={'label': 'Throughput (events/sec)'}
        )

        ax.set_title("Performance Heatmap (Throughput by Language and Benchmark)")
        ax.set_ylabel("Benchmark")
        ax.set_xlabel("Language")

        plt.tight_layout()

        output_file = self.output_dir / "performance_heatmap.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved heatmap to {output_file}")

    def plot_cpu_usage_analysis(self):
        """Plot CPU usage comparison"""
        if self.df.empty or 'metric_cpu_usage_percent' not in self.df.columns:
            return

        df = self.df.copy()
        plot_data = df.dropna(subset=['metric_cpu_usage_percent'])

        if plot_data.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.boxplot(
            data=plot_data,
            x='language',
            y='metric_cpu_usage_percent',
            ax=ax
        )

        ax.set_title("CPU Usage Comparison")
        ax.set_ylabel("CPU Usage (%)")
        ax.set_xlabel("Language")

        plt.tight_layout()

        output_file = self.output_dir / "cpu_usage_analysis.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved CPU usage plot to {output_file}")

    def plot_duration_comparison(self):
        """Plot benchmark duration comparison"""
        if self.df.empty:
            return

        df = self.df.copy()

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.barplot(
            data=df,
            x='benchmark_id',
            y='duration',
            hue='language',
            ax=ax
        )

        ax.set_title("Benchmark Duration Comparison")
        ax.set_ylabel("Duration (seconds)")
        ax.set_xlabel("Benchmark")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_file = self.output_dir / "duration_comparison.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"✓ Saved duration plot to {output_file}")

    def generate_all(self):
        """Generate all available plots"""
        print("Generating plots...")

        self.plot_throughput_comparison()
        self.plot_latency_distribution()
        self.plot_program_type_comparison()
        self.plot_data_mechanism_comparison()
        self.plot_language_performance_heatmap()
        self.plot_cpu_usage_analysis()
        self.plot_duration_comparison()

        print(f"\n✓ All plots saved to {self.output_dir}")

    def generate_report_html(self):
        """Generate HTML report with all plots"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>eBPF Benchmark Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #555;
                    margin-top: 30px;
                }
                img {
                    max-width: 100%;
                    margin: 20px 0;
                    border: 1px solid #ddd;
                    padding: 10px;
                    border-radius: 4px;
                }
                .summary {
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-left: 4px solid #007bff;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>eBPF Benchmark Analysis Report</h1>
                <div class="summary">
                    <p>This report contains comprehensive analysis of eBPF benchmark results.</p>
                    <p>Generated: {timestamp}</p>
                </div>

                <h2>Throughput Comparison</h2>
                <img src="throughput_comparison.png" alt="Throughput Comparison">

                <h2>Latency Distribution</h2>
                <img src="latency_distribution.png" alt="Latency Distribution">

                <h2>Program Type Comparison</h2>
                <img src="program_type_comparison.png" alt="Program Type Comparison">

                <h2>Data Mechanism Comparison</h2>
                <img src="data_mechanism_comparison.png" alt="Data Mechanism Comparison">

                <h2>Performance Heatmap</h2>
                <img src="performance_heatmap.png" alt="Performance Heatmap">

                <h2>CPU Usage Analysis</h2>
                <img src="cpu_usage_analysis.png" alt="CPU Usage Analysis">

                <h2>Duration Comparison</h2>
                <img src="duration_comparison.png" alt="Duration Comparison">
            </div>
        </body>
        </html>
        """.format(timestamp=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

        html_file = self.output_dir / "report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)

        print(f"✓ HTML report saved to {html_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmark analysis plots")
    parser.add_argument(
        '-d', '--dir',
        default='benchmarks/results',
        help='Results directory'
    )
    parser.add_argument(
        '-o', '--output',
        default='analysis/plots',
        help='Output directory for plots'
    )

    args = parser.parse_args()

    generator = PlotGenerator(args.dir, args.output)
    generator.generate_all()
    generator.generate_report_html()


if __name__ == '__main__':
    main()
