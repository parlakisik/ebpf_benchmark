#!/usr/bin/env python3
"""
Process Benchmark Results

Load, parse, and aggregate benchmark results from JSON files
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from collections import defaultdict


class ResultsProcessor:
    """Process and aggregate benchmark results"""

    def __init__(self, results_dir: str = "benchmarks/results"):
        self.results_dir = Path(results_dir)
        self.results = []
        self.dataframe = None

    def load_results(self, pattern: str = "*.json") -> List[Dict]:
        """Load result files from directory"""
        self.results = []

        for result_file in self.results_dir.glob(pattern):
            if result_file.name in ['latest.json']:  # Skip aggregated files
                continue

            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)

                # Handle both single result and aggregated results
                results = data.get('results', [data])
                self.results.extend(results)
            except Exception as e:
                print(f"Error loading {result_file}: {e}")

        return self.results

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame"""
        if not self.results:
            return pd.DataFrame()

        # Flatten nested structures
        flattened = []
        for result in self.results:
            flat_result = {
                'benchmark_id': result.get('benchmark_id'),
                'benchmark_name': result.get('benchmark_name'),
                'language': result.get('language'),
                'program_type': result.get('program_type'),
                'data_mechanism': result.get('data_mechanism'),
                'status': result.get('status'),
                'timestamp': result.get('timestamp'),
                'duration': result.get('duration', 0),
            }

            # Flatten metrics
            metrics = result.get('metrics', {})
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    flat_result[f"metric_{key}"] = value

            flattened.append(flat_result)

        self.dataframe = pd.DataFrame(flattened)
        return self.dataframe

    def get_summary_stats(self, benchmark_id: Optional[str] = None) -> Dict:
        """Get summary statistics for benchmarks"""
        df = self.dataframe or self.to_dataframe()

        if benchmark_id:
            df = df[df['benchmark_id'] == benchmark_id]

        if df.empty:
            return {}

        summary = {}

        # Group by language and benchmark
        for (bench_id, language), group in df.groupby(['benchmark_id', 'language']):
            key = f"{bench_id}_{language}"
            summary[key] = {
                'count': len(group),
                'status': group['status'].mode()[0] if not group['status'].empty else 'unknown',
                'avg_duration': group['duration'].mean(),
                'min_duration': group['duration'].min(),
                'max_duration': group['duration'].max(),
            }

        return summary

    def compare_languages(self, benchmark_id: str, metric: str) -> Dict:
        """Compare metric across languages for specific benchmark"""
        df = self.dataframe or self.to_dataframe()
        df = df[df['benchmark_id'] == benchmark_id]

        if df.empty:
            return {}

        metric_col = f"metric_{metric}"
        if metric_col not in df.columns:
            return {}

        comparison = {}
        for language, group in df.groupby('language'):
            values = group[metric_col].dropna()
            if not values.empty:
                comparison[language] = {
                    'mean': values.mean(),
                    'median': values.median(),
                    'std': values.std(),
                    'min': values.min(),
                    'max': values.max(),
                    'count': len(values),
                }

        return comparison

    def export_csv(self, output_file: str):
        """Export results to CSV"""
        df = self.dataframe or self.to_dataframe()

        if df.empty:
            print("No results to export")
            return

        df.to_csv(output_file, index=False)
        print(f"Exported {len(df)} results to {output_file}")

    def get_benchmark_comparison(self, benchmark_id: str) -> pd.DataFrame:
        """Get comparison DataFrame for a specific benchmark"""
        df = self.dataframe or self.to_dataframe()
        return df[df['benchmark_id'] == benchmark_id].copy()

    def calculate_percentiles(self, values: List[float], percentiles: List[int] = None) -> Dict:
        """Calculate percentiles for latency data"""
        if percentiles is None:
            percentiles = [50, 95, 99, 99.9]

        if not values:
            return {}

        return {
            f"p{p}": np.percentile(values, p)
            for p in percentiles
        }

    def get_throughput_comparison(self) -> Dict:
        """Get throughput comparison across all benchmarks"""
        df = self.dataframe or self.to_dataframe()

        comparison = defaultdict(dict)
        for (bench_id, language), group in df.groupby(['benchmark_id', 'language']):
            throughput = group.get('metric_throughput', [])
            if not throughput.empty:
                comparison[bench_id][language] = throughput.mean()

        return dict(comparison)

    def print_summary(self):
        """Print summary statistics"""
        df = self.dataframe or self.to_dataframe()

        if df.empty:
            print("No results loaded")
            return

        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)

        print(f"\nTotal results: {len(df)}")
        print(f"Benchmarks: {df['benchmark_id'].nunique()}")
        print(f"Languages: {df['language'].nunique()}")
        print(f"Success rate: {(df['status'] == 'success').sum() / len(df) * 100:.1f}%")

        print("\nResults by Benchmark:")
        for bench_id, group in df.groupby('benchmark_id'):
            print(f"\n  {bench_id}:")
            for language, lang_group in group.groupby('language'):
                status_counts = lang_group['status'].value_counts()
                status_str = ", ".join(f"{s}={c}" for s, c in status_counts.items())
                print(f"    {language}: {status_str}")

        print("\n" + "="*80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Process benchmark results")
    parser.add_argument(
        '-d', '--dir',
        default='benchmarks/results',
        help='Results directory'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output CSV file'
    )
    parser.add_argument(
        '-s', '--summary',
        action='store_true',
        help='Print summary'
    )
    parser.add_argument(
        '-b', '--benchmark',
        help='Filter to specific benchmark'
    )
    parser.add_argument(
        '-m', '--metric',
        help='Compare specific metric across languages'
    )

    args = parser.parse_args()

    processor = ResultsProcessor(args.dir)
    processor.load_results()
    processor.to_dataframe()

    if args.summary:
        processor.print_summary()

    if args.metric and args.benchmark:
        comparison = processor.compare_languages(args.benchmark, args.metric)
        print(f"\nComparison for {args.benchmark} - {args.metric}:")
        for lang, stats in comparison.items():
            print(f"  {lang}: mean={stats['mean']:.2f}, median={stats['median']:.2f}")

    if args.output:
        processor.export_csv(args.output)


if __name__ == '__main__':
    main()
